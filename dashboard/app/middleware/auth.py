"""
Authentication and other middleware components
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that protects routes requiring login.
    Redirects unauthenticated users to the login page.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Routes that don't require authentication
        self.public_routes = {
            "/login",     # Login page and form submission
            "/static",    # Static files (CSS, JS, images)
            "/docs",      # API documentation (optional)
            "/redoc",     # Alternative API documentation (optional)
        }
    
    async def dispatch(self, request, call_next):
        """
        Process each request to check authentication
        
        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/route handler
            
        Returns:
            HTTP response (either from route handler or redirect to login)
        """
        path = request.url.path
        
        # Allow access to public routes without authentication
        if any(path.startswith(route) for route in self.public_routes):
            return await call_next(request)
        
        # Check if user is authenticated for protected routes
        if not request.session.get("user"):
            return RedirectResponse("/login", status_code=HTTP_302_FOUND)
        
        # User is authenticated, proceed to route handler
        return await call_next(request)
