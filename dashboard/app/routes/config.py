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
