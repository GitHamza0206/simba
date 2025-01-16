from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.chat_routes import chat
from core.utils.logger import setup_logging
import logging
from api.ingestion_routes import ingestion
from api.parsing_routes import parsing
# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat)
app.include_router(ingestion)
app.include_router(parsing)
# Setup logging at application start
setup_logging(level=logging.INFO)  # or logging.INFO for less verbose output

# Get logger for this file
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Application starting...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
