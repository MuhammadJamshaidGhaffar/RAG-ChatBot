"""
Authentication service layer
"""

from passlib.hash import bcrypt
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from database.mongo_client import get_mongo_client

ADMIN_USERS_COLLECTION_NAME = os.getenv("ADMIN_USERS_COLLECTION", "admin_users")

db = get_mongo_client()
users_col = db[ADMIN_USERS_COLLECTION_NAME]


def verify_user(username: str, password: str) -> bool:
    """
    Verify user credentials
    
    Args:
        username: Username to verify
        password: Password to verify
        
    Returns:
        True if credentials are valid, False otherwise
    """
    user = users_col.find_one({"username": username})
    if user and bcrypt.verify(password, user["password"]):
        return True
    return False


def update_password(username: str, new_password: str) -> bool:
    """
    Update user password
    
    Args:
        username: Username to update password for
        new_password: New password to set
        
    Returns:
        True if password was updated successfully, False otherwise
    """
    hashed = bcrypt.hash(new_password)
    result = users_col.update_one({"username": username}, {"$set": {"password": hashed}})
    return result.modified_count == 1
