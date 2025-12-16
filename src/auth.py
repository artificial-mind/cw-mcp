"""
FastAPI middleware for authentication
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> bool:
    """
    Verify API key from Bearer token
    Returns True if valid, raises HTTPException if invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token
    token = credentials.credentials
    
    # Verify against configured API key
    if token != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True


class AuthMiddleware:
    """
    Middleware to verify API key on all requests
    Can be disabled for health checks and documentation
    """
    
    EXEMPT_PATHS = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Only check HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Skip auth for exempt paths
        path = scope["path"]
        if any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS):
            await self.app(scope, receive, send)
            return
        
        # For MCP SSE endpoint, authentication is handled by the MCP protocol itself
        # So we'll allow it through here
        if path.startswith("/sse") or path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return
        
        # For other paths, verify Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        
        if not auth_header.startswith("Bearer "):
            await self._send_error(send, 401, "Missing Bearer token")
            return
        
        token = auth_header.replace("Bearer ", "")
        if token != settings.API_KEY:
            await self._send_error(send, 403, "Invalid API key")
            return
        
        # Authentication successful
        await self.app(scope, receive, send)
    
    async def _send_error(self, send, status_code: int, detail: str):
        """Send error response"""
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": f'{{"error": "{detail}"}}'.encode(),
        })
