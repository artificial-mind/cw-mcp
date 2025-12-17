"""
Logistics MCP Server using FastMCP
Simplified implementation that works seamlessly with 11Labs
"""
import os
import logging
from datetime import datetime
from typing import Optional
from fastmcp import FastMCP
from database.database import init_db, get_db_context
from database.models import Shipment
from sqlalchemy import select

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

# Initialize database on startup
import asyncio
asyncio.run(init_db())
logger.info("✅ Database initialized")


@mcp.tool()
async def search_shipments(
    risk_flag: Optional[bool] = None,
    status_code: Optional[str] = None,
    container_no: Optional[str] = None,
    master_bill: Optional[str] = None,
    limit: int = 10
) -> dict:
    """
    Search and filter shipments by various criteria.
    
    Args:
        risk_flag: Filter by risk status (true/false)
        status_code: Filter by status code (e.g., 'IN_TRANSIT', 'DELIVERED')
        container_no: Filter by container number
        master_bill: Filter by master bill of lading number
        limit: Maximum number of results to return
    
    Returns:
        Dictionary with shipment results and count
    """
    logger.info(f"🔍 Searching shipments: risk={risk_flag}, status={status_code}, container={container_no}, bill={master_bill}, limit={limit}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment)
            
            logger.info(f"📊 Executing database query...")
            
            # Apply filters
            if risk_flag is not None:
                query = query.where(Shipment.risk_flag == risk_flag)
            if status_code:
                query = query.where(Shipment.status_code == status_code)
            if container_no:
                query = query.where(Shipment.container_no.like(f"%{container_no}%"))
            if master_bill:
                query = query.where(Shipment.master_bill.like(f"%{master_bill}%"))
            
            query = query.limit(limit)
            result = await session.execute(query)
            shipments = result.scalars().all()
            
            logger.info(f"📊 Database returned {len(shipments)} shipments")
            
            shipment_list = [
                {
                    "job_id": s.job_id,
                    "container_no": s.container_no,
                    "master_bill": s.master_bill,
                    "status": s.status_code,
                    "risk_flag": s.risk_flag,
                    "origin": s.origin_port,
                    "destination": s.destination_port,
                    "eta": s.eta.isoformat() if s.eta else None
                }
                for s in shipments
            ]
            
            logger.info(f"✅ Found {len(shipment_list)} shipments")
            if shipment_list:
                logger.info(f"✅ First shipment: {shipment_list[0]}")
            else:
                logger.warning("⚠️ No shipments found in database!")
            return {
                "success": True,
                "count": len(shipment_list),
                "results": shipment_list
            }
    
    except Exception as e:
        logger.error(f"❌ Error searching shipments: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def track_shipment(identifier: str) -> dict:
    """
    Get detailed tracking information for a specific shipment.
    
    Args:
        identifier: Job ID, container number, or bill of lading number
    
    Returns:
        Detailed shipment tracking information
    """
    logger.info(f"📦 Tracking shipment: {identifier}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment).where(
                (Shipment.job_id == identifier) |
                (Shipment.container_no == identifier) |
                (Shipment.master_bill == identifier)
            )
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                logger.warning(f"⚠️ Shipment not found: {identifier}")
                return {
                    "success": False,
                    "error": f"Shipment not found: {identifier}"
                }
            
            tracking_data = {
                "success": True,
                "shipment": {
                    "job_id": shipment.job_id,
                    "container_no": shipment.container_no,
                    "master_bill": shipment.master_bill,
                    "status": shipment.status_code,
                    "risk_flag": shipment.risk_flag,
                    "origin": shipment.origin_port,
                    "destination": shipment.destination_port,
                    "eta": shipment.eta.isoformat() if shipment.eta else None,
                    "vessel": shipment.vessel_name,
                    "voyage": shipment.voyage_number,
                    "notes": shipment.notes or []
                }
            }
            
            logger.info(f"✅ Shipment tracked: {shipment.job_id}")
            return tracking_data
    
    except Exception as e:
        logger.error(f"❌ Error tracking shipment: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def update_shipment_eta(
    identifier: str,
    new_eta: str,
    reason: Optional[str] = None
) -> dict:
    """
    Update the estimated arrival time for a shipment.
    
    Args:
        identifier: Job ID, container number, or bill of lading
        new_eta: New ETA in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        reason: Optional reason for the ETA change
    
    Returns:
        Success status and updated shipment info
    """
    logger.info(f"⏰ Updating ETA for {identifier} to {new_eta}")
    
    try:
        from dateutil.parser import parse
        new_eta_dt = parse(new_eta)
        
        async with get_db_context() as session:
            query = select(Shipment).where(
                (Shipment.job_id == identifier) |
                (Shipment.container_no == identifier) |
                (Shipment.master_bill == identifier)
            )
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                return {
                    "success": False,
                    "error": f"Shipment not found: {identifier}"
                }
            
            old_eta = shipment.eta
            shipment.eta = new_eta_dt
            shipment.updated_at = datetime.utcnow()
            
            # Add note about ETA change
            notes = shipment.notes or []
            note_text = f"ETA updated from {old_eta} to {new_eta_dt}"
            if reason:
                note_text += f". Reason: {reason}"
            notes.append({
                "timestamp": datetime.utcnow().isoformat(),
                "note": note_text,
                "type": "eta_update"
            })
            shipment.notes = notes
            
            await session.commit()
            
            logger.info(f"✅ ETA updated for {shipment.job_id}")
            return {
                "success": True,
                "message": f"ETA updated for {shipment.job_id}",
                "old_eta": old_eta.isoformat() if old_eta else None,
                "new_eta": new_eta_dt.isoformat()
            }
    
    except Exception as e:
        logger.error(f"❌ Error updating ETA: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def set_risk_flag(
    identifier: str,
    is_risk: bool,
    reason: Optional[str] = None
) -> dict:
    """
    Flag a shipment as high-risk or remove the risk flag.
    
    Args:
        identifier: Job ID, container number, or bill of lading
        is_risk: True to flag as risk, False to clear risk flag
        reason: Optional reason for the risk flag change
    
    Returns:
        Success status and updated shipment info
    """
    logger.info(f"🚨 Setting risk flag for {identifier} to {is_risk}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment).where(
                (Shipment.job_id == identifier) |
                (Shipment.container_no == identifier) |
                (Shipment.master_bill == identifier)
            )
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                return {
                    "success": False,
                    "error": f"Shipment not found: {identifier}"
                }
            
            shipment.risk_flag = is_risk
            shipment.updated_at = datetime.utcnow()
            
            # Add note about risk flag change
            notes = shipment.notes or []
            note_text = f"Risk flag {'SET' if is_risk else 'CLEARED'}"
            if reason:
                note_text += f". Reason: {reason}"
            notes.append({
                "timestamp": datetime.utcnow().isoformat(),
                "note": note_text,
                "type": "risk_update"
            })
            shipment.notes = notes
            
            await session.commit()
            
            logger.info(f"✅ Risk flag updated for {shipment.job_id}")
            return {
                "success": True,
                "message": f"Risk flag {'set' if is_risk else 'cleared'} for {shipment.job_id}",
                "risk_flag": is_risk
            }
    
    except Exception as e:
        logger.error(f"❌ Error setting risk flag: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def add_agent_note(
    identifier: str,
    note: str,
    agent_name: Optional[str] = None
) -> dict:
    """
    Add an operational note to a shipment record.
    
    Args:
        identifier: Job ID, container number, or bill of lading
        note: The note text to add
        agent_name: Optional name of the agent adding the note
    
    Returns:
        Success status
    """
    logger.info(f"📝 Adding note to {identifier}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment).where(
                (Shipment.job_id == identifier) |
                (Shipment.container_no == identifier) |
                (Shipment.master_bill == identifier)
            )
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                return {
                    "success": False,
                    "error": f"Shipment not found: {identifier}"
                }
            
            notes = shipment.notes or []
            new_note = {
                "timestamp": datetime.utcnow().isoformat(),
                "note": note,
                "type": "agent_note"
            }
            if agent_name:
                new_note["agent"] = agent_name
            
            notes.append(new_note)
            shipment.notes = notes
            shipment.updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"✅ Note added to {shipment.job_id}")
            return {
                "success": True,
                "message": f"Note added to {shipment.job_id}"
            }
    
    except Exception as e:
        logger.error(f"❌ Error adding note: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_server_status(include_details: bool = False) -> dict:
    """
    Get the current status and health of the MCP server.
    
    Args:
        include_details: Whether to include detailed metrics
    
    Returns:
        Server status information
    """
    logger.info("🏥 Getting server status")
    
    status = {
        "status": "healthy",
        "server": "logistics-orchestrator",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
    
    if include_details:
        status["details"] = {
            "tools_registered": 6,
            "database": "connected",
            "transport": "FastMCP SSE"
        }
    
    return status


# Run the server
if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 Starting Logistics MCP Server with FastMCP")
    logger.info(f"📡 Port: {PORT}")
    logger.info(f"🔧 Tools: 6 (search, track, update_eta, risk_flag, note, status)")
    logger.info("="*60)
    
    try:
        mcp.run(transport="sse", host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        import sys
        sys.exit(1)
