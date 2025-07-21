"""
FastAPI Dashboard Application
Main entry point for the document upload and management system.
"""

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Local imports
from app.core.config import settings
from app.middleware.auth import AuthMiddleware
from app.routes.auth import login_page, login_submit, logout
from app.routes.main import home, upload_file, upload_page
from app.routes.dashboard import dashboard, change_password


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        Configured FastAPI application instance
    """
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG
    )
    
    # Add middleware (order matters - last added executes first)
    app.add_middleware(AuthMiddleware)  # Authentication check
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)  # Session management
    
    # Mount static files
    app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
    
    # Create necessary directories
    settings.create_directories()
    
    return app


# Create app instance
app = create_app()


# ==================== ROUTE DEFINITIONS ====================

# Authentication routes
@app.get("/login")
async def get_login_page(request: Request):
    """Login page"""
    return await login_page(request)


@app.post("/login")
async def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Login form submission"""
    return await login_submit(request, username, password)


@app.get("/logout")
async def get_logout(request: Request):
    """User logout"""
    return await logout(request)


# Application routes
@app.get("/")
async def get_home(request: Request):
    """Home/upload page"""
    return await home(request)


@app.get("/dashboard")
async def get_dashboard(request: Request):
    """Dashboard page"""
    return await dashboard(request)


@app.get("/upload-page")
async def get_upload_page(request: Request):
    """Upload page"""
    return await upload_page(request)


@app.post("/upload")
async def post_upload(file: UploadFile = File(...)):
    """File upload endpoint"""
    return await upload_file(file)


@app.post("/change-password")
async def post_change_password(request: Request, current_password: str = Form(...), 
                              new_password: str = Form(...), confirm_password: str = Form(...)):
    """Change password endpoint"""
    return await change_password(request, current_password, new_password, confirm_password)


# ==================== APPLICATION STARTUP ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=settings.DEBUG
    )
