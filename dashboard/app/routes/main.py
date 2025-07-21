"""
Application route handlers
"""

from fastapi import Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

from app.core.config import settings
from app.services.file_service import handle_file_upload

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


async def home(request: Request) -> HTMLResponse:
    """
    Display home/upload page - redirect to dashboard for better UX
    
    Args:
        request: FastAPI request object
        
    Returns:
        Redirect to dashboard or upload page HTML
    """
    # Redirect to dashboard for better user experience
    return RedirectResponse("/dashboard", status_code=HTTP_302_FOUND)


async def upload_page(request: Request) -> HTMLResponse:
    """
    Display dedicated upload page
    
    Args:
        request: FastAPI request object
        
    Returns:
        Upload page HTML
    """
    return templates.TemplateResponse("upload.html", {"request": request})


async def upload_file(file: UploadFile = File(...)):
    """
    Handle file upload
    
    Args:
        file: Uploaded file from form
        
    Returns:
        JSON response with upload status
    """
    return await handle_file_upload(file)
