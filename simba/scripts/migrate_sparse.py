"""Migration script to add sparse vectors to existing collections.

Qdrant doesn't support adding sparse vectors to existing collections,
so this script recreates the collection with sparse vector support.

Usage:
    uv run python -m simba.scripts.migrate_sparse --collection <name>
    uv run python -m simba.scripts.migrate_sparse --all
"""

import argparse
import logging
import sys

from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from simba.core.config import settings
from simba.services import embedding_service
from simba.services.qdrant_service import (
    collection_exists,
    collection_has_sparse_vectors,
    get_qdrant_client,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def migrate_collection(collection_name: str, batch_size: int = 100) -> bool:
    """Migrate a collection to support sparse vectors.

    Since Qdrant doesn't support adding sparse vectors to existing collections,
    this function:
    1. Creates a temporary collection with sparse vector support
    2. Copies all points with newly generated sparse embeddings
    3. Deletes the original collection
    4. Renames the temporary collection

    Args:
        collection_name: Name of the collection to migrate.
        batch_size: Number of points to process at a time.

    Returns:
        True if migration was successful, False otherwise.
    """
    client = get_qdrant_client()

    if not collection_exists(collection_name):
        logger.error(f"Collection '{collection_name}' does not exist")
        return False

    # Check if collection already has sparse vectors
    if collection_has_sparse_vectors(collection_name):
        logger.info(
            f"Collection '{collection_name}' already has sparse vectors. "
            "Skipping migration."
        )
        return True

    temp_collection = f"{collection_name}_migration_temp"

    # Check if temp collection exists (from failed previous migration)
    if collection_exists(temp_collection):
        logger.warning(f"Temporary collection '{temp_collection}' exists. Deleting it.")
        client.delete_collection(temp_collection)

    try:
        # Step 1: Create temporary collection with sparse vector support
        logger.info(f"Creating temporary collection '{temp_collection}' with sparse vectors")
        client.create_collection(
            collection_name=temp_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
            sparse_vectors_config={
                "text-sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
        )

        # Step 2: Get total point count
        info = client.get_collection(collection_name=collection_name)
        total_points = info.points_count
        logger.info(f"Migrating {total_points} points from '{collection_name}'")

        # Step 3: Copy all points with sparse vectors
        offset = None
        processed = 0

        while True:
            # Get batch of points with vectors
            results, offset = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )

            if not results:
                break

            # Prepare points with sparse embeddings
            points_to_insert = []
            texts_to_embed = []
            points_data = []

            for point in results:
                chunk_text = point.payload.get("chunk_text", "")
                if chunk_text:
                    texts_to_embed.append(chunk_text)
                    points_data.append(point)
                else:
                    # No text to embed, copy without sparse vector
                    logger.warning(f"Point {point.id} has no chunk_text, copying without sparse")
                    points_to_insert.append(
                        PointStruct(
                            id=point.id,
                            vector=point.vector,
                            payload=point.payload,
                        )
                    )

            # Generate sparse embeddings in batch
            if texts_to_embed:
                sparse_embeddings = embedding_service.get_sparse_embeddings(texts_to_embed)

                for point, sparse in zip(points_data, sparse_embeddings):
                    # Handle both dict and direct vector formats
                    dense_vector = point.vector
                    if isinstance(dense_vector, dict):
                        # Named vectors - get the default one
                        dense_vector = dense_vector.get("") or list(dense_vector.values())[0]

                    points_to_insert.append(
                        PointStruct(
                            id=point.id,
                            vector={
                                "": dense_vector,
                                "text-sparse": SparseVector(
                                    indices=sparse[0],
                                    values=sparse[1],
                                ),
                            },
                            payload=point.payload,
                        )
                    )

            # Insert batch into temp collection
            if points_to_insert:
                client.upsert(
                    collection_name=temp_collection,
                    points=points_to_insert,
                )

            processed += len(results)
            logger.info(f"Processed {processed}/{total_points} points")

            if offset is None:
                break

        # Step 4: Delete original and rename temp
        logger.info(f"Deleting original collection '{collection_name}'")
        client.delete_collection(collection_name)

        logger.info(f"Renaming '{temp_collection}' to '{collection_name}'")
        # Qdrant doesn't have rename, so we need to create new and copy again
        # Actually, let's just use aliases or recreate
        # For simplicity, we'll create the final collection and copy from temp

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
            sparse_vectors_config={
                "text-sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
        )

        # Copy from temp to final
        offset = None
        while True:
            results, offset = client.scroll(
                collection_name=temp_collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )

            if not results:
                break

            points = []
            for point in results:
                points.append(
                    PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=point.payload,
                    )
                )

            if points:
                client.upsert(collection_name=collection_name, points=points)

            if offset is None:
                break

        # Delete temp collection
        client.delete_collection(temp_collection)

        logger.info(f"Migration complete: '{collection_name}' now has sparse vectors")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Cleanup temp collection if it exists
        if collection_exists(temp_collection):
            logger.info(f"Cleaning up temporary collection '{temp_collection}'")
            client.delete_collection(temp_collection)
        return False


def list_collections() -> list[str]:
    """List all collections in Qdrant."""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    return [c.name for c in collections]


def main():
    parser = argparse.ArgumentParser(
        description="Add sparse vectors to existing Qdrant collections for hybrid search."
    )
    parser.add_argument(
        "--collection",
        "-c",
        type=str,
        help="Name of the collection to migrate",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Migrate all collections",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all collections and their sparse vector status",
    )
    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=100,
        help="Number of points to process at a time (default: 100)",
    )

    args = parser.parse_args()

    if args.list:
        collections = list_collections()
        if not collections:
            print("No collections found")
            return

        print("\nCollections:")
        print("-" * 50)
        for name in collections:
            has_sparse = collection_has_sparse_vectors(name)
            status = "sparse vectors" if has_sparse else "dense only"
            print(f"  {name}: {status}")
        print()
        return

    if args.all:
        collections = list_collections()
        if not collections:
            logger.error("No collections found")
            sys.exit(1)

        logger.info(f"Migrating {len(collections)} collections")
        failed = []
        for name in collections:
            if not migrate_collection(name, args.batch_size):
                failed.append(name)

        if failed:
            logger.error(f"Migration failed for collections: {failed}")
            sys.exit(1)

        logger.info("All collections migrated successfully")
        return

    if args.collection:
        if not migrate_collection(args.collection, args.batch_size):
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
