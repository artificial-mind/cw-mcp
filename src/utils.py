"""
Utility functions and helpers
"""
import logging
from datetime import datetime
from typing import Any, Dict
import sys


def setup_logging(debug: bool = False):
    """Configure logging for the application"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logistics_mcp.log')
        ]
    )
    
    # Reduce noise from httpx and uvicorn
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def format_response(
    success: bool,
    data: Any = None,
    error: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Format standard API response
    """
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error:
        response["error"] = error
    
    response.update(kwargs)
    return response


def validate_iso_datetime(date_string: str) -> bool:
    """Validate ISO 8601 datetime string"""
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """Mask API key for logging"""
    if len(api_key) <= visible_chars:
        return "*" * len(api_key)
    return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)
