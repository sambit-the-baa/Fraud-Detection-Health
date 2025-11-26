from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB connection string from environment variable
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://frauddetection:FraudDetect2025!@1.mwnrysb.mongodb.net/?retryWrites=true&w=majority&appName=1"
)
DATABASE_NAME = os.getenv("DATABASE_NAME", "fraud_detection_health")

# Async client for FastAPI
async_client = None
async_db = None

# Sync client for startup operations
sync_client = None
sync_db = None


def get_sync_db():
    """Get synchronous MongoDB database connection"""
    global sync_client, sync_db
    if sync_client is None:
        sync_client = MongoClient(MONGODB_URI)
        sync_db = sync_client[DATABASE_NAME]
        logger.info(f"Connected to MongoDB database: {DATABASE_NAME}")
    return sync_db


async def get_async_db():
    """Get async MongoDB database connection for FastAPI"""
    global async_client, async_db
    if async_client is None:
        async_client = AsyncIOMotorClient(MONGODB_URI)
        async_db = async_client[DATABASE_NAME]
        logger.info(f"Connected to async MongoDB database: {DATABASE_NAME}")
    return async_db


async def close_db_connection():
    """Close database connections"""
    global async_client, sync_client
    if async_client:
        async_client.close()
    if sync_client:
        sync_client.close()
    logger.info("Database connections closed")


# Collection names
COLLECTIONS = {
    "policies": "policies",
    "claims": "claims",
    "documents": "documents",
    "questions": "questions"
}


# Legacy compatibility - keep Base for any remaining SQLAlchemy code
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
