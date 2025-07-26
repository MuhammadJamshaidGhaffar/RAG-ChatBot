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
from app.routes.config import (
    get_chat_storage_setting, 
    update_chat_storage_setting, 
    get_all_settings, 
    ChatStorageToggle,
    get_gemini_api_key,
    update_gemini_api_key,
    GeminiApiKeyUpdate
)


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
    """Legacy file upload endpoint (documents only)"""
    return await upload_file(file)


@app.post("/upload/document")
async def post_upload_document(file: UploadFile = File(...)):
    """Document upload endpoint for knowledge base"""
    from app.services.file_service import process_document_upload
    return process_document_upload(file)


@app.post("/upload/images-csv")
async def post_upload_images_csv(file: UploadFile = File(...)):
    """Images CSV upload endpoint"""
    from app.services.file_service import process_images_csv_upload
    return process_images_csv_upload(file)


@app.post("/upload/videos-csv")
async def post_upload_videos_csv(file: UploadFile = File(...)):
    """Videos CSV upload endpoint"""
    from app.services.file_service import process_videos_csv_upload
    return process_videos_csv_upload(file)


@app.post("/change-password")
async def post_change_password(request: Request, current_password: str = Form(...), 
                              new_password: str = Form(...), confirm_password: str = Form(...)):
    """Change password endpoint"""
    return await change_password(request, current_password, new_password, confirm_password)


# Configuration routes
@app.get("/api/config/chat-storage")
async def get_chat_storage_config(request: Request):
    """Get chat storage configuration"""
    return await get_chat_storage_setting(request)


@app.post("/api/config/chat-storage")
async def post_chat_storage_config(toggle_data: ChatStorageToggle):
    """Update chat storage configuration"""
    return await update_chat_storage_setting(toggle_data)


@app.get("/api/config/all")
async def get_all_config(request: Request):
    """Get all configuration settings"""
    return await get_all_settings(request)


@app.get("/api/config/gemini-api-key")
async def get_gemini_api_key_config(request: Request):
    """Get Gemini API key configuration (masked)"""
    return await get_gemini_api_key(request)


@app.post("/api/config/gemini-api-key")
async def post_gemini_api_key_config(api_key_data: GeminiApiKeyUpdate):
    """Update Gemini API key configuration"""
    return await update_gemini_api_key(api_key_data)


# ==================== APPLICATION STARTUP ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=9000, 
        reload=settings.DEBUG
    )
