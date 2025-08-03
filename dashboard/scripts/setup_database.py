"""
Database setup and initialization scripts
"""

from pymongo import MongoClient
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from passlib.hash import bcrypt

# loading dot env
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# custom imports
from database.mongo_client import get_mongo_client
from utils.constants import (
    ADMIN_USERS_COLLECTION_NAME, 
    IMAGES_COLLECTION, 
    VIDEOS_COLLECTION, 
    CONFIG_COLLECTION,
    CHAT_HISTORY_COLLECTION,
    QUESTIONS_COLLECTION
)


def setup_admin_user():
    """
    Set up initial admin user in the database
    """
    # Get environment variables
    ADMIN_USER = os.getenv("ADMIN_USER")
    if not ADMIN_USER:
        print("❌ ADMIN_USER not set in environment variables. Please configure it.")
        exit(1)

    ADMIN_PWD = os.getenv("ADMIN_PWD")
    if not ADMIN_PWD:
        print("❌ ADMIN_PWD not set in environment variables. Please configure it.")
        exit(1)
        
    ADMIN_USERS_COLLECTION_NAME = os.getenv("ADMIN_USERS_COLLECTION", "admin_users")

    # Connect to MongoDB
    db = get_mongo_client()
    users_collection = db[ADMIN_USERS_COLLECTION_NAME]

    # Define initial user (admin)
    admin_user = {
        "username": ADMIN_USER,
        "password": bcrypt.hash(ADMIN_PWD),
        "created_at": datetime.now(timezone.utc)
    }

    # Insert only if user with same username doesn't exist
    if not users_collection.find_one({"username": admin_user["username"]}):
        users_collection.insert_one(admin_user)
        print(f"✅ Admin user added: {admin_user['username']}")
    else:
        print(f"ℹ️ Admin user already exists: {admin_user['username']}")

    collection_names = [ADMIN_USERS_COLLECTION_NAME, "config", IMAGES_COLLECTION, VIDEOS_COLLECTION]
    for name in collection_names:
        if name not in db.list_collection_names():
            db.create_collection(name)
            print(f"Created collection: {name}")
        else:
            print(f"Collection already exists: {name}")

    print("MongoDB initialization complete.")


def create_collections():
    """Create chat_history and questions collections with proper indexes."""
    
    # Connect to MongoDB
    db = get_mongo_client()
    
    # Create config collection with app_settings document structure
    config_collection = db[CONFIG_COLLECTION]
    try:
        # Check if app_settings config exists, if not create default
        existing_config = config_collection.find_one({"_id": "app_settings"})
        if not existing_config:
            # Get Gemini API key from environment
            gemini_api_key = os.getenv("GEMINI_API_KEY", "")
            
            app_settings_config = {
                "_id": "app_settings",
                "chat_storage": {
                    "save_full_chat": True,
                    "save_questions_only": False,
                    "enabled": True
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            config_collection.insert_one(app_settings_config)
            print(f"✅ Created {CONFIG_COLLECTION} collection with app_settings config")
            if gemini_api_key:
                print(f"✅ Gemini API key configured from environment")
            else:
                print(f"⚠️  Gemini API key placeholder created - configure via dashboard")
        else:
            print(f"ℹ️  app_settings config already exists in {CONFIG_COLLECTION} collection")
            # Check if chat_storage exists in existing config
            if "chat_storage" not in existing_config:
                # Add chat_storage to existing config
                config_collection.update_one(
                    {"_id": "app_settings"},
                    {
                        "$set": {
                            "chat_storage": {
                                "save_full_chat": True,
                                "save_questions_only": False,
                                "enabled": True
                            },
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                print(f"✅ Added chat_storage config to existing app_settings")
            
            # Check if gemini_api_key exists in existing config
            if "gemini_api_key" not in existing_config:
                gemini_api_key = os.getenv("GEMINI_API_KEY", "")
                config_collection.update_one(
                    {"_id": "app_settings"},
                    {
                        "$set": {
                            "gemini_api_key": gemini_api_key,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                print(f"✅ Added Gemini API key to existing app_settings")
            
    except Exception as e:
        print(f"❌ Config collection setup error: {e}")
    
    # Create chat_history collection
    chat_collection = db[CHAT_HISTORY_COLLECTION]
    
    # Create indexes for chat_history collection
    try:
        # Index on session_id for fast chat retrieval
        chat_collection.create_index("session_id")
        # Index on timestamp for chronological ordering
        chat_collection.create_index("timestamp")
        # Compound index for session queries with time ordering
        chat_collection.create_index([("session_id", 1), ("timestamp", 1)])
        print(f"Created {CHAT_HISTORY_COLLECTION} collection with indexes.")
    except Exception as e:
        print(f"Chat history collection already exists or error: {e}")
    
    # Create questions collection
    questions_collection = db[QUESTIONS_COLLECTION]
    
    # Create indexes for questions collection
    try:
        # Index on user_id for user-specific queries
        questions_collection.create_index("user_id")
        # Index on timestamp for chronological ordering
        questions_collection.create_index("timestamp")
        # Index on faculty for faculty-specific analytics
        questions_collection.create_index("faculty")
        # Text index for question content search
        questions_collection.create_index([("question", "text")])
        print(f"Created {QUESTIONS_COLLECTION} collection with indexes.")
    except Exception as e:
        print(f"Questions collection already exists or error: {e}")

if __name__ == "__main__":
    setup_admin_user()
    create_collections()
