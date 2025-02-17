import os
# Must be set BEFORE any other imports that might use HuggingFace
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

import multiprocessing

# Set multiprocessing start method before any other imports
if os.name != 'nt' and multiprocessing.get_start_method(allow_none=True) != 'spawn':
    multiprocessing.set_start_method('spawn')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.chat_routes import chat
from core.utils.logger import setup_logging
import logging
from api.ingestion_routes import ingestion
from api.parsing_routes import parsing
from api.database_routes import database_route
from api.embedding_routes import embedding_route
from core.config import settings
import uvicorn

# If your Celery app and Redis are both accessible:
# (Replace "celery_app" and "redis_conn" with your actual instances)
try:
    from core.celery_config import celery_app
except ImportError:
    celery_app = None

# If you maintain a Redis client connection:
# import redis
# redis_conn = redis.Redis(host='localhost', port=6379)

# Load environment variables from .env file
load_dotenv()

# Setup logging at application start
setup_logging(level=logging.DEBUG)

# Get logger for this file
logger = logging.getLogger(__name__)

# Log tokenizer settings
logger.info("=" * 50)
logger.info("Initializing Application Settings")
logger.info(f"TOKENIZERS_PARALLELISM set to: {os.environ['TOKENIZERS_PARALLELISM']}")
logger.info("=" * 50)

app = FastAPI(title=settings.project.name)

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Log configuration details on startup"""
    logger.info("=" * 50)
    logger.info("Starting SIMBA Application")
    logger.info("=" * 50)
    
    # Project Info
    logger.info(f"Project Name: {settings.project.name}")
    logger.info(f"Version: {settings.project.version}")
    
    # Model Configurations
    logger.info("\nModel Configurations:")
    logger.info(f"LLM Provider: {settings.llm.provider}")
    logger.info(f"LLM Model: {settings.llm.model_name}")
    logger.info(f"Embedding Provider: {settings.embedding.provider}")
    logger.info(f"Embedding Model: {settings.embedding.model_name}")
    logger.info(f"Embedding Device: {settings.embedding.device}")
    
    # Vector Store & Database
    logger.info("\nStorage Configurations:")
    logger.info(f"Vector Store Provider: {settings.vector_store.provider}")
    logger.info(f"Database Provider: {settings.database.provider}")
    
    # Paths
    logger.info("\nPaths:")
    logger.info(f"Base Directory: {settings.paths.base_dir}")
    logger.info(f"Upload Directory: {settings.paths.upload_dir}")
    logger.info(f"Vector Store Directory: {settings.paths.vector_store_dir}")
    
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Perform any necessary cleanup here: 
    - gracefully end Celery workers 
    - close Redis if directly connected
    """
    logger.info("Shutting down SIMBA Application...")

    # If you have a Celery app running in the same process (uncommon):
    if celery_app:
        logger.info("Sending shutdown signal to Celery workers...")
        try:
            celery_app.control.broadcast("shutdown")
            logger.info("Celery workers have been signaled to shut down.")
        except Exception as e:
            logger.error(f"Error while shutting down Celery: {e}")

    # If you have a direct Redis connection in this process:
    # try:
    #     logger.info("Shutting down Redis server...")
    #     # This gracefully stops Redis without saving. 
    #     # Using it in production is often discouraged unless Redis runs in the same process.
    #     redis_conn.shutdown(nosave=True)
    #     logger.info("Redis server shutdown complete.")
    # except Exception as e:
    #     logger.error(f"Error while shutting down Redis: {e}")

    logger.info("SIMBA Application shutdown complete.")

# Include routers
app.include_router(chat)
app.include_router(ingestion)
app.include_router(parsing)
app.include_router(database_route)
app.include_router(embedding_route)

if __name__ == "__main__":
    # NOTE:
    # Typically, Celery and Redis each run as separate processes/containers.
    # This script only handles FastAPI shutdown. 
    # Celery and Redis will still shut down when their processes/containers stop.
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=1
    )
