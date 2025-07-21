"""
Application configuration and settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration"""
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Directory settings
    UPLOADS_DIR = "uploads"
    TEMPLATES_DIR = "templates"
    STATIC_DIR = "static"
    
    # Application settings
    APP_NAME = "Document Upload Dashboard"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.UPLOADS_DIR, exist_ok=True)
        os.makedirs(cls.STATIC_DIR, exist_ok=True)


# Global settings instance
settings = Settings()
