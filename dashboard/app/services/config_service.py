"""
Configuration service for managing application settings
"""

import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from database.mongo_client import get_mongo_client


class ConfigurationService:
    """Service for managing application configuration settings"""
    
    def __init__(self):
        self.db = get_mongo_client()
        self.config_collection = self.db.config
        self._ensure_default_config()
    
    def _ensure_default_config(self):
        """Ensure default configuration exists"""
        try:
            # Check if config document exists
            existing_config = self.config_collection.find_one({"_id": "app_settings"})
            
            if not existing_config:
                # Create default configuration
                default_config = {
                    "_id": "app_settings",
                    "save_full_chat": True,  # Default: save full conversations
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                self.config_collection.insert_one(default_config)
                print("✅ Default configuration created")
        except Exception as e:
            print(f"❌ Error ensuring default config: {str(e)}")
    
    def get_chat_storage_setting(self) -> Dict[str, Any]:
        """Get current chat storage configuration"""
        try:
            config = self.config_collection.find_one({"_id": "app_settings"})
            if config:
                return config.get("chat_storage", {
                    "save_full_chat": True,
                    "save_questions_only": False,
                    "enabled": True
                })
            return {
                "save_full_chat": True,
                "save_questions_only": False,
                "enabled": True
            }
        except Exception as e:
            print(f"❌ Error getting chat storage setting: {str(e)}")
            return {
                "save_full_chat": True,
                "save_questions_only": False,
                "enabled": True
            }
    
    def update_chat_storage_setting(self, save_full_chat: bool) -> bool:
        """
        Update chat storage setting
        
        Args:
            save_full_chat: If True, save full conversations; if False, save questions only
            
        Returns:
            Success status
        """
        try:
            update_data = {
                "$set": {
                    "chat_storage.save_full_chat": save_full_chat,
                    "chat_storage.save_questions_only": not save_full_chat,
                    "updated_at": datetime.now().isoformat()
                }
            }
            
            result = self.config_collection.update_one(
                {"_id": "app_settings"},
                update_data,
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"❌ Error updating chat storage setting: {str(e)}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        try:
            config = self.config_collection.find_one({"_id": "app_settings"})
            if config:
                # Remove MongoDB _id for cleaner response
                config.pop("_id", None)
                return config
            return {}
        except Exception as e:
            print(f"❌ Error getting all settings: {str(e)}")
            return {}


# Global configuration service instance
config_service = ConfigurationService()
