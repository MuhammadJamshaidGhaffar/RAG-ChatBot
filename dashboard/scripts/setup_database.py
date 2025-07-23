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
from constants import ADMIN_USERS_COLLECTION_NAME, IMAGES_COLLECTION, VIDEOS_COLLECTION


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

if __name__ == "__main__":
    setup_admin_user()
