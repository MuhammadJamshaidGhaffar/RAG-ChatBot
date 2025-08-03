import datetime
import chainlit as cl
from mongo_util import get_mongo_client
from constants import CHAT_HISTORY_COLLECTION, QUESTIONS_COLLECTION, CONFIG_COLLECTION, USERS_COLLECTION

"""
Storage Strategy:
1. User data (name, email, mobile, faculty) is stored once in USERS_COLLECTION when KYC is completed
2. Chat history and questions only store session_id to link back to user data
3. Use get_chat_history_with_user_data() or get_questions_with_user_data() to retrieve enriched data
4. This approach reduces storage redundancy and ensures data consistency
"""

def get_storage_config():
    """Get storage configuration from MongoDB config collection based on your existing structure."""
    try:
        mongo_db = get_mongo_client()
        config_collection = mongo_db[CONFIG_COLLECTION]
        
        # Look for document with _id "app_settings"
        config = config_collection.find_one({"_id": "app_settings"})
        
        if config and "chat_storage" in config:
            chat_storage = config["chat_storage"]
            
            # Check if chat storage is enabled
            if not chat_storage.get("enabled", False):
                print("DEBUG: Chat storage is disabled")
                return None
                
            # Determine storage mode based on your flags
            if chat_storage.get("save_full_chat", False):
                storage_mode = "chat_history"
                print("DEBUG: Storage mode from config: chat_history")
                return storage_mode
            elif chat_storage.get("save_questions_only", False):
                storage_mode = "questions"
                print("DEBUG: Storage mode from config: questions")
                return storage_mode
            else:
                print("DEBUG: No storage mode enabled in config")
                return None
        else:
            print("DEBUG: No app_settings config found, storage disabled")
            return None
            
    except Exception as e:
        print(f"DEBUG: Error getting storage config: {e}, storage disabled")
        return None

def save_interaction_data(user_input, ai_response, storage_mode):
    """Save interaction data based on storage mode configuration."""
    print(f"DEBUG: Saving interaction data with storage mode: {storage_mode}")
    if not storage_mode:
        print("DEBUG: Storage disabled, skipping save")
        return
        
    try:
        mongo_db = get_mongo_client()
        timestamp = datetime.datetime.utcnow()
        session_id = cl.user_session.get("id", "unknown")
        
        if storage_mode == "chat_history":
            # Save full chat history format
            chat_collection = mongo_db[CHAT_HISTORY_COLLECTION]
            
            # Save user message
            user_message = {
                "session_id": session_id,
                "timestamp": timestamp,
                "role": "user",
                "content": user_input
            }
            chat_collection.insert_one(user_message)
            
            # Save AI response
            ai_message = {
                "session_id": session_id,
                "timestamp": timestamp,
                "role": "assistant", 
                "content": ai_response
            }
            chat_collection.insert_one(ai_message)
            
            print(f"DEBUG: Saved chat history for session {session_id}")
            
        elif storage_mode == "questions":
            # Save questions format
            questions_collection = mongo_db[QUESTIONS_COLLECTION]
            
            question_doc = {
                "session_id": session_id,
                "timestamp": timestamp,
                "question": user_input,
            }
            questions_collection.insert_one(question_doc)
            
            print(f"DEBUG: Saved question for session {session_id}")
            
    except Exception as e:
        print(f"DEBUG: Error saving interaction data: {e}")


def get_user_data_by_session(session_id):
    """Retrieve user data from USERS_COLLECTION by session_id."""
    try:
        mongo_db = get_mongo_client()
        users_collection = mongo_db[USERS_COLLECTION]
        
        user_data = users_collection.find_one({"session_id": session_id})
        
        if user_data:
            print(f"DEBUG: Retrieved user data for session {session_id}")
            return user_data
        else:
            print(f"DEBUG: No user data found for session {session_id}")
            return None
            
    except Exception as e:
        print(f"DEBUG: Error retrieving user data by session: {e}")
        return None


def get_chat_history_with_user_data(session_id=None, limit=None):
    """Retrieve chat history with associated user data."""
    try:
        mongo_db = get_mongo_client()
        chat_collection = mongo_db[CHAT_HISTORY_COLLECTION]
        users_collection = mongo_db[USERS_COLLECTION]
        
        # Build query
        query = {}
        if session_id:
            query["session_id"] = session_id
            
        # Get chat history
        cursor = chat_collection.find(query).sort("timestamp", -1)
        if limit:
            cursor = cursor.limit(limit)
            
        chat_history = list(cursor)
        
        # Enrich with user data
        for chat in chat_history:
            user_data = users_collection.find_one({"session_id": chat["session_id"]})
            if user_data:
                chat["user_data"] = {
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "mobile": user_data.get("mobile"),
                    "faculty": user_data.get("faculty")
                }
        
        return chat_history
        
    except Exception as e:
        print(f"DEBUG: Error retrieving chat history with user data: {e}")
        return []


def get_questions_with_user_data(session_id=None, limit=None):
    """Retrieve questions with associated user data."""
    try:
        mongo_db = get_mongo_client()
        questions_collection = mongo_db[QUESTIONS_COLLECTION]
        users_collection = mongo_db[USERS_COLLECTION]
        
        # Build query
        query = {}
        if session_id:
            query["session_id"] = session_id
            
        # Get questions
        cursor = questions_collection.find(query).sort("timestamp", -1)
        if limit:
            cursor = cursor.limit(limit)
            
        questions = list(cursor)
        
        # Enrich with user data
        for question in questions:
            user_data = users_collection.find_one({"session_id": question["session_id"]})
            if user_data:
                question["user_data"] = {
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "mobile": user_data.get("mobile"),
                    "faculty": user_data.get("faculty")
                }
        
        return questions
        
    except Exception as e:
        print(f"DEBUG: Error retrieving questions with user data: {e}")
        return []
