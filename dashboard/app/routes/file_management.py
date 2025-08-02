"""
File management route handlers
"""

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

from app.services.file_service import get_uploaded_files_list, delete_uploaded_file
from app.core.config import settings

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


async def list_files(request: Request) -> HTMLResponse:
    """
    Display file management page with uploaded files
    
    Args:
        request: FastAPI request object
        
    Returns:
        File management page HTML
    """
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    
    # Get list of uploaded files
    files = get_uploaded_files_list()
    
    return templates.TemplateResponse("file_management.html", {
        "request": request, 
        "user": user,
        "files": files
    })


async def delete_file(request: Request, filename: str):
    """
    Delete a file from the knowledge base
    
    Args:
        request: FastAPI request object
        filename: Name of the file to delete
        
    Returns:
        JSON response with deletion result
    """
    user = request.session.get("user")
    if not user:
        return JSONResponse(
            content={"success": False, "message": "Unauthorized"}, 
            status_code=401
        )
    
    # Delete the file
    result = delete_uploaded_file(filename)
    
    if result["success"]:
        return JSONResponse(content={
            "success": True, 
            "message": result["message"],
            "deleted_count": result.get("deleted_count", 0)
        })
    else:
        return JSONResponse(
            content={"success": False, "message": result["message"]}, 
            status_code=400
        )


async def get_files_json(request: Request):
    """
    Get list of uploaded files as JSON
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with list of files
    """
    user = request.session.get("user")
    if not user:
        return JSONResponse(
            content={"success": False, "message": "Unauthorized"}, 
            status_code=401
        )
    
    # Get list of uploaded files
    files = get_uploaded_files_list()
    
    return JSONResponse(content={
        "success": True,
        "files": files
    })
