"""
MongoDB client and connection handling
"""

from pymongo import MongoClient
import os

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if MONGODB_URI is None:
    raise Exception("❌ MONGODB_URI not set in secrets. Please configure it.")
    
if MONGO_DB_NAME is None:
    raise Exception("❌ MONGO_DB_NAME not set in secrets. Please configure it.")
    

def get_mongo_client():
    """
    Get MongoDB database connection
    
    Returns:
        MongoDB database instance
        
    Raises:
        Exception: If connection fails
    """
    try:
        client = MongoClient(MONGODB_URI)
        return client[MONGO_DB_NAME]
    except Exception as e:
        raise Exception(f"❌ Failed to connect to MongoDB: {e}")
