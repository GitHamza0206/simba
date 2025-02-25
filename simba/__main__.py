def create_app():
    """Create and configure the FastAPI application."""
    import logging
    import multiprocessing
    import os

    from dotenv import load_dotenv
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Set environment variables early
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

    # Set multiprocessing start method if not Windows
    if os.name != "nt" and multiprocessing.get_start_method(allow_none=True) != "spawn":
        multiprocessing.set_start_method("spawn")

    # Load environment variables
    load_dotenv()

    # Import application components
    from simba.api.chat_routes import chat
    from simba.api.database_routes import database_route
    from simba.api.embedding_routes import embedding_route
    from simba.api.ingestion_routes import ingestion
    from simba.api.parsing_routes import parsing
    from simba.api.retriever_routes import retriever_route
    from simba.core.config import settings
    from simba.core.utils.logger import setup_logging

    # Try to import celery app
    try:
        from simba.core.celery_config import celery_app
    except ImportError:
        celery_app = None

    # Setup logging
    setup_logging(level=logging.DEBUG)

    # Initialize FastAPI app
    app = FastAPI(title=settings.project.name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("Starting SIMBA Application")
        logger.info("=" * 50)
        logger.info(f"Project Name: {settings.project.name}")
        logger.info(f"Version: {settings.project.version}")
        logger.info(f"LLM Provider: {settings.llm.provider}")
        logger.info(f"LLM Model: {settings.llm.model_name}")
        logger.info(f"Embedding Provider: {settings.embedding.provider}")
        logger.info(f"Embedding Model: {settings.embedding.model_name}")
        logger.info(f"Embedding Device: {settings.embedding.device}")
        logger.info(f"Vector Store Provider: {settings.vector_store.provider}")
        logger.info(f"Database Provider: {settings.database.provider}")
        logger.info(f"Base Directory: {settings.paths.base_dir}")
        logger.info(f"Upload Directory: {settings.paths.upload_dir}")
        logger.info(f"Vector Store Directory: {settings.paths.vector_store_dir}")
        logger.info("=" * 50)

    @app.on_event("shutdown")
    async def shutdown_event():
        logger = logging.getLogger(__name__)
        logger.info("Shutting down SIMBA Application...")
        if celery_app:
            logger.info("Sending shutdown signal to Celery workers...")
            try:
                celery_app.control.broadcast("shutdown")
                logger.info("Celery workers have been signaled to shut down.")
            except Exception as e:
                logger.error(f"Error while shutting down Celery: {e}")
        logger.info("SIMBA Application shutdown complete.")

    # Include API routers
    app.include_router(chat)
    app.include_router(ingestion)
    app.include_router(parsing)
    app.include_router(database_route)
    app.include_router(embedding_route)
    app.include_router(retriever_route)

    return app
