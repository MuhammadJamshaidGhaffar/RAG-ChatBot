"""
Authentication route handlers
"""

from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

from app.services.auth_service import verify_user
from app.core.config import settings

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


async def login_page(request: Request) -> HTMLResponse:
    """
    Display login page
    
    Args:
        request: FastAPI request object
        
    Returns:
        Login page HTML or redirect to home if already authenticated
    """
    # If already authenticated, redirect to home page
    if request.session.get("user"):
        return RedirectResponse("/", status_code=HTTP_302_FOUND)
    
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Handle login form submission
    
    Args:
        request: FastAPI request object
        username: Username from form
        password: Password from form
        
    Returns:
        Redirect to home on success, or login page with error on failure
    """
    print(f"DEBUG: Attempting login for user: {username}")

    if verify_user(username, password):
        print(f"DEBUG: User {username} verified successfully")
        request.session["user"] = {"username": username}
        return RedirectResponse("/", status_code=HTTP_302_FOUND)
    print(f"DEBUG: Invalid credentials for user: {username}")
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "error": "Invalid credentials"
    })


async def logout(request: Request) -> RedirectResponse:
    """
    Handle user logout
    
    Args:
        request: FastAPI request object
        
    Returns:
        Redirect to login page
    """
    request.session.clear()
    return RedirectResponse("/login", status_code=HTTP_302_FOUND)
