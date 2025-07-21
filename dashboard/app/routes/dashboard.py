"""
Dashboard route handlers
"""

from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from fastapi.responses import JSONResponse

from app.services.auth_service import update_password, verify_user
from app.core.config import settings

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


async def dashboard(request: Request) -> HTMLResponse:
    """
    Display dashboard page with user info and options
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dashboard page HTML
    """
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": user
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
