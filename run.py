#!/usr/bin/env python3
"""
Entry point for Logistics MCP Orchestrator Server
Ensures proper PYTHONPATH for src/ directory
"""
import sys
import os
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).resolve().parent

# Add src directory to Python path
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Change to script directory (important for relative paths)
os.chdir(script_dir)

# Import and run server
from server import app, settings
import uvicorn

if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("LOGISTICS MCP ORCHESTRATOR SERVER")
    logger.info("=" * 60)
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path includes: {src_dir}")
    
    uvicorn.run(
        app,  # Pass app object directly instead of string
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
