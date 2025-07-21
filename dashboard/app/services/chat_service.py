"""
Chat service for handling conversation storage based on configuration
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from database.mongo_client import get_mongo_client
from app.services.config_service import config_service


class ChatService:
    """Service for managing chat conversations and storage"""
    
    def __init__(self):
        self.db = get_mongo_client()
        self.chats_collection = self.db.chats
        self.questions_collection = self.db.questions
    
    def save_chat_interaction(self, user_id: str, question: str, answer: str, 
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save chat interaction based on current configuration
        
        Args:
            user_id: User identifier
            question: User's question
            answer: AI's response
            metadata: Additional metadata (sources, timestamps, etc.)
            
        Returns:
            Success status
        """
        try:
            # Get current storage setting
            storage_setting = config_service.get_chat_storage_setting()
            
            if not storage_setting.get("enabled", True):
                return True  # Storage disabled, consider as success
            
            timestamp = datetime.now().isoformat()
            base_data = {
                "user_id": user_id,
                "question": question,
                "timestamp": timestamp,
                "metadata": metadata or {}
            }
            
            if storage_setting.get("save_full_chat", True):
                # Save full conversation
                chat_data = {
                    **base_data,
                    "answer": answer,
                    "type": "full_chat"
                }
                self.chats_collection.insert_one(chat_data)
            else:
                # Save only questions
                question_data = {
                    **base_data,
                    "type": "question_only"
                }
                self.questions_collection.insert_one(question_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving chat interaction: {str(e)}")
            return False
    
    def get_user_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get user's chat history based on current storage setting
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            
        Returns:
            List of chat records
        """
        try:
            storage_setting = config_service.get_chat_storage_setting()
            
            if storage_setting.get("save_full_chat", True):
                # Get full conversations
                cursor = self.chats_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(limit)
            else:
                # Get questions only
                cursor = self.questions_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            print(f"❌ Error getting chat history: {str(e)}")
            return []
    
    def get_chat_statistics(self) -> Dict[str, Any]:
        """Get chat storage statistics"""
        try:
            storage_setting = config_service.get_chat_storage_setting()
            
            if storage_setting.get("save_full_chat", True):
                total_chats = self.chats_collection.count_documents({})
                collection_type = "Full Conversations"
                collection_name = "chats"
            else:
                total_chats = self.questions_collection.count_documents({})
                collection_type = "Questions Only"
                collection_name = "questions"
            
            return {
                "total_interactions": total_chats,
                "storage_type": collection_type,
                "collection": collection_name,
                "setting": storage_setting
            }
            
        except Exception as e:
            print(f"❌ Error getting chat statistics: {str(e)}")
            return {
                "total_interactions": 0,
                "storage_type": "Unknown",
                "collection": "none",
                "setting": {}
            }
    
    def delete_all_chat_data(self) -> bool:
        """Delete all chat data (for testing or privacy purposes)"""
        try:
            self.chats_collection.delete_many({})
            self.questions_collection.delete_many({})
            return True
        except Exception as e:
            print(f"❌ Error deleting chat data: {str(e)}")
            return False


# Global chat service instance
chat_service = ChatService()


# Example usage functions for integration
def save_conversation(user_id: str, question: str, answer: str, sources: List[str] = None):
    """
    Convenience function to save a conversation
    
    Args:
        user_id: User identifier
        question: User's question
        answer: AI's response
        sources: List of source documents used
    """
    metadata = {
        "sources": sources or [],
        "response_length": len(answer),
        "question_length": len(question)
    }
    
    return chat_service.save_chat_interaction(user_id, question, answer, metadata)


def get_recent_chats(user_id: str, count: int = 10):
    """
    Get recent chats for a user
    
    Args:
        user_id: User identifier
        count: Number of recent chats to retrieve
        
    Returns:
        List of recent chat records
    """
    return chat_service.get_user_chat_history(user_id, count)
