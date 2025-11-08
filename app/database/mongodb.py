"""
MongoDB connection and client
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config import settings
from app.utils.logger import logger


class MongoDB:
    """MongoDB client wrapper"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Set database
            self.db = self.client[settings.MONGODB_DATABASE]
            
            logger.info(f"✅ Connected to MongoDB database: {settings.MONGODB_DATABASE}")
            
            # Create indexes
            await self.create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def create_indexes(self):
        """Create database indexes"""
        try:
            # Images collection indexes
            await self.db.images.create_index("product_id", unique=True)
            await self.db.images.create_index("image_hash")
            await self.db.images.create_index("status")
            
            # Classifications collection indexes
            await self.db.classifications.create_index("product_id")
            await self.db.classifications.create_index("approved")
            await self.db.classifications.create_index([("classified_at", -1)])
            
            # Embeddings collection indexes
            await self.db.embeddings.create_index("product_id", unique=True)
            await self.db.embeddings.create_index("faiss_index_position")
            
            # Training jobs collection indexes
            await self.db.training_jobs.create_index("job_id", unique=True)
            await self.db.training_jobs.create_index("status")
            
            logger.info("✅ MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")


# Create MongoDB instance
mongodb = MongoDB()


async def connect_to_mongo():
    """Connect to MongoDB on startup"""
    await mongodb.connect()


async def close_mongo_connection():
    """Close MongoDB connection on shutdown"""
    await mongodb.close()


def get_database():
    """Get MongoDB database instance"""
    return mongodb.db
