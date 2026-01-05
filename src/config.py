"""
Configuration management for Logistics MCP Orchestrator Server
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = True
    
    # Authentication
    API_KEY: str = "dev-api-key-12345"
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    # Database
    # Use /tmp for Render deployment (filesystem is read-only except /tmp)
    DATABASE_URL: str = "sqlite+aiosqlite:////tmp/logistics.db"
    
    # External APIs (Placeholders)
    LOGITUDE_API_URL: str = "https://api.logitude.com"
    LOGITUDE_API_KEY: str = "placeholder-key"
    DPWORLD_API_URL: str = "https://api.dpworld.com"
    DPWORLD_API_KEY: str = "placeholder-key"
    TRACKING_API_URL: str = "https://api.tracking.com"
    TRACKING_API_KEY: str = "placeholder-key"
    
    # Vessel Tracking API (VesselFinder or similar)
    # Leave empty to use mock data, provide API key for real AIS data
    VESSELFINDER_API_KEY: Optional[str] = None
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
