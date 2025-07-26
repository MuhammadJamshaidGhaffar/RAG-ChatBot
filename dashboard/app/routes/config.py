"""
Configuration route handlers
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.config_service import config_service


class ChatStorageToggle(BaseModel):
    """Model for chat storage toggle request"""
    save_full_chat: bool


class GeminiApiKeyUpdate(BaseModel):
    """Model for Gemini API key update request"""
    api_key: str


async def get_chat_storage_setting(request: Request) -> JSONResponse:
    """
    Get current chat storage setting
    
    Returns:
        JSON response with current setting
    """
    try:
        setting = config_service.get_chat_storage_setting()
        return JSONResponse(content={
            "success": True,
            "setting": setting
        })
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"Error getting setting: {str(e)}"
            },
            status_code=500
        )


async def update_chat_storage_setting(toggle_data: ChatStorageToggle) -> JSONResponse:
    """
    Update chat storage setting
    
    Args:
        toggle_data: New setting data
        
    Returns:
        JSON response with update status
    """
    try:
        success = config_service.update_chat_storage_setting(toggle_data.save_full_chat)
        
        if success:
            setting_type = "full conversations" if toggle_data.save_full_chat else "questions only"
            return JSONResponse(content={
                "success": True,
                "message": f"✅ Chat storage updated to save {setting_type}",
                "setting": config_service.get_chat_storage_setting()
            })
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "❌ Failed to update setting"
                },
                status_code=500
            )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"❌ Error updating setting: {str(e)}"
            },
            status_code=500
        )


async def get_all_settings(request: Request) -> JSONResponse:
    """
    Get all configuration settings
    
    Returns:
        JSON response with all settings
    """
    try:
        settings = config_service.get_all_settings()
        return JSONResponse(content={
            "success": True,
            "settings": settings
        })
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"Error getting settings: {str(e)}"
            },
            status_code=500
        )


async def get_gemini_api_key(request: Request) -> JSONResponse:
    """
    Get current Gemini API key (masked for security)
    
    Returns:
        JSON response with masked API key
    """
    try:
        api_key = config_service.get_gemini_api_key()
        # Mask the API key for security - show only first 4 and last 4 characters
        if api_key and len(api_key) > 8:
            masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
        elif api_key:
            masked_key = "*" * len(api_key)
        else:
            masked_key = ""
            
        return JSONResponse(content={
            "success": True,
            "api_key": masked_key,
            "is_configured": bool(api_key)
        })
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"Error getting API key: {str(e)}"
            },
            status_code=500
        )


async def update_gemini_api_key(api_key_data: GeminiApiKeyUpdate) -> JSONResponse:
    """
    Update Gemini API key
    
    Args:
        api_key_data: New API key data
        
    Returns:
        JSON response with update status
    """
    try:
        success = config_service.update_gemini_api_key(api_key_data.api_key)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "✅ Gemini API key updated successfully"
            })
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "❌ Failed to update API key"
                },
                status_code=500
            )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"❌ Error updating API key: {str(e)}"
            },
            status_code=500
        )
