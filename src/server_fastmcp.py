"""
Logistics MCP Server using FastMCP
Simplified implementation that works seamlessly with 11Labs
"""
import os
import logging
import asyncio
from fastmcp import FastMCP
from database.database import init_db, get_db_context
from database.models import Shipment
from sqlalchemy import select
from tools import register_tools

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get port from environment (Render sets this)
PORT = int(os.environ.get("PORT", 8000))

# Initialize FastMCP
mcp = FastMCP(
    name="logistics-orchestrator",
    version="1.0.0"
)


async def setup_database():
    """Initialize database and seed if necessary"""
    await init_db()
    logger.info("✅ Database initialized")
    
    # Check if database needs seeding
    async with get_db_context() as session:
        result = await session.execute(select(Shipment).limit(1))
        existing = result.scalar_one_or_none()
        
        if not existing:
            logger.info("📦 Database is empty - importing seed data...")
            from quick_seed import quick_seed
            await quick_seed()
        else:
            logger.info(f"✅ Database ready with existing data (found shipment: {existing.id})")


# Initialize database
asyncio.run(setup_database())

# Register all tools
register_tools(mcp)


# Run the server
if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 Starting Logistics MCP Server with FastMCP")
    logger.info(f"📡 Port: {PORT}")
    logger.info(f"🔧 Tools: 11 registered")
    logger.info("   Core: search, track, update_eta, set_risk, add_note")
    logger.info("   Advanced: advanced_search, analytics, query, delayed, route")
    logger.info("   System: server_status")
    logger.info("="*60)
    
    try:
        mcp.run(transport="sse", host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        import sys
        sys.exit(1)
