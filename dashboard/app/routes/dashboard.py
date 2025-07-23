"""
Dashboard route handlers
"""

from datetime import datetime
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from fastapi.responses import JSONResponse

from app.services.auth_service import update_password, verify_user
from app.services.file_service import get_knowledge_base_stats
from app.core.config import settings

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


async def dashboard(request: Request) -> HTMLResponse:
    """
    Display dashboard page with user info and Ask Nour statistics
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dashboard page HTML
    """
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    
    # Get real statistics from Pinecone
    stats = get_knowledge_base_stats()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": user,
        "current_time": datetime.now(),
        "stats": stats,
        "chatbot_url": settings.CHATBOT_PUBLIC_URL
    })


async def change_password(request: Request, current_password: str = Form(...), 
                         new_password: str = Form(...), confirm_password: str = Form(...)):
    """
    Handle password change request
    
    Args:
        request: FastAPI request object
        current_password: Current password
        new_password: New password
        confirm_password: Confirmation of new password
        
    Returns:
        JSON response with success or error message
    """
    user = request.session.get("user")
    if not user:
        return JSONResponse(content={"success": False, "message": "Not authenticated"}, status_code=401)
    
    # Validate new password
    if len(new_password) < 8:
        return JSONResponse(content={"success": False, "message": "Password must be at least 8 characters long"})
    
    if new_password != confirm_password:
        return JSONResponse(content={"success": False, "message": "New passwords do not match"})
    
    # Verify current password and update
    if not verify_user(user["username"], current_password):
        return JSONResponse(content={"success": False, "message": "Current password is incorrect"})
    
    # Update password
    if update_password(user["username"], new_password):
        return JSONResponse(content={"success": True, "message": "Password updated successfully"})
    else:
        return JSONResponse(content={"success": False, "message": "Failed to update password"})
