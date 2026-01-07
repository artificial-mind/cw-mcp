"""
MCP Tools for Logistics Orchestrator
All tool implementations for the FastMCP server
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import httpx

from database.database import get_db_context
from database.models import Shipment
from sqlalchemy import select, func, or_, and_
from adapters.vessel_tracking_adapter import VesselTrackingAdapter
from config import settings

logger = logging.getLogger(__name__)

# Initialize vessel tracking adapter (with API key if provided, otherwise mock)
vessel_tracker = VesselTrackingAdapter(api_key=settings.VESSELFINDER_API_KEY)

# Analytics Engine URL
ANALYTICS_ENGINE_URL = settings.ANALYTICS_ENGINE_URL if hasattr(settings, 'ANALYTICS_ENGINE_URL') else "http://localhost:8002"


# ============================================================================
# BASIC SEARCH & TRACKING TOOLS
# ============================================================================

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
            
            shipment_list = [
                {
                    "id": s.id,
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
                (Shipment.id == identifier) |
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
                    "id": shipment.id,
                    "container_no": shipment.container_no,
                    "master_bill": shipment.master_bill,
                    "status": shipment.status_code,
                    "risk_flag": shipment.risk_flag,
                    "origin": shipment.origin_port,
                    "destination": shipment.destination_port,
                    "eta": shipment.eta.isoformat() if shipment.eta else None,
                    "vessel": shipment.vessel_name,
                    "voyage": shipment.voyage_number,
                    "notes": shipment.agent_notes or []
                }
            }
            
            logger.info(f"✅ Shipment tracked: {shipment.id}")
            return tracking_data
    
    except Exception as e:
        logger.error(f"❌ Error tracking shipment: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# SHIPMENT UPDATE TOOLS
# ============================================================================

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
                (Shipment.id == identifier) |
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
            
            logger.info(f"✅ ETA updated for {shipment.id}")
            return {
                "success": True,
                "message": f"ETA updated for {shipment.id}",
                "old_eta": old_eta.isoformat() if old_eta else None,
                "new_eta": new_eta_dt.isoformat()
            }
    
    except Exception as e:
        logger.error(f"❌ Error updating ETA: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


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
                (Shipment.id == identifier) |
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
            
            logger.info(f"✅ Risk flag updated for {shipment.id}")
            return {
                "success": True,
                "message": f"Risk flag {'set' if is_risk else 'cleared'} for {shipment.id}",
                "risk_flag": is_risk
            }
    
    except Exception as e:
        logger.error(f"❌ Error setting risk flag: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


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
                (Shipment.id == identifier) |
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
            
            logger.info(f"✅ Note added to {shipment.id}")
            return {
                "success": True,
                "message": f"Note added to {shipment.id}"
            }
    
    except Exception as e:
        logger.error(f"❌ Error adding note: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# ADVANCED SEARCH TOOLS
# ============================================================================

async def search_shipments_advanced(
    vessel_name: Optional[str] = None,
    voyage_number: Optional[str] = None,
    origin_port: Optional[str] = None,
    destination_port: Optional[str] = None,
    status_codes: Optional[List[str]] = None,
    risk_flag: Optional[bool] = None,
    eta_from: Optional[str] = None,
    eta_to: Optional[str] = None,
    current_location: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    Advanced search with multiple filters for shipments. Supports complex queries.
    
    Args:
        vessel_name: Filter by vessel name (partial match)
        voyage_number: Filter by voyage number (partial match)
        origin_port: Filter by origin port (partial match)
        destination_port: Filter by destination port (partial match)
        status_codes: List of status codes to filter by (e.g., ['IN_TRANSIT', 'DELAYED'])
        risk_flag: Filter by risk status (true/false)
        eta_from: Filter shipments arriving after this date (YYYY-MM-DD)
        eta_to: Filter shipments arriving before this date (YYYY-MM-DD)
        current_location: Filter by current location (partial match)
        limit: Maximum number of results (default 20)
    
    Returns:
        Dictionary with filtered shipment results
    """
    logger.info(f"🔍 Advanced search: vessel={vessel_name}, voyage={voyage_number}, origin={origin_port}, dest={destination_port}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment)
            
            # Apply filters
            if vessel_name:
                query = query.where(Shipment.vessel_name.like(f"%{vessel_name}%"))
            if voyage_number:
                query = query.where(Shipment.voyage_number.like(f"%{voyage_number}%"))
            if origin_port:
                query = query.where(Shipment.origin_port.like(f"%{origin_port}%"))
            if destination_port:
                query = query.where(Shipment.destination_port.like(f"%{destination_port}%"))
            if status_codes:
                query = query.where(Shipment.status_code.in_(status_codes))
            if risk_flag is not None:
                query = query.where(Shipment.risk_flag == risk_flag)
            if current_location:
                query = query.where(Shipment.current_location.like(f"%{current_location}%"))
            
            # Date range filters
            if eta_from:
                from dateutil.parser import parse
                eta_from_dt = parse(eta_from)
                query = query.where(Shipment.eta >= eta_from_dt)
            if eta_to:
                from dateutil.parser import parse
                eta_to_dt = parse(eta_to)
                query = query.where(Shipment.eta <= eta_to_dt)
            
            query = query.limit(limit)
            result = await session.execute(query)
            shipments = result.scalars().all()
            
            shipment_list = [
                {
                    "id": s.id,
                    "container_no": s.container_no,
                    "master_bill": s.master_bill,
                    "vessel_name": s.vessel_name,
                    "voyage_number": s.voyage_number,
                    "status": s.status_code,
                    "status_description": s.status_description,
                    "risk_flag": s.risk_flag,
                    "origin": s.origin_port,
                    "destination": s.destination_port,
                    "current_location": s.current_location,
                    "eta": s.eta.isoformat() if s.eta else None,
                    "etd": s.etd.isoformat() if s.etd else None
                }
                for s in shipments
            ]
            
            logger.info(f"✅ Advanced search found {len(shipment_list)} shipments")
            return {
                "success": True,
                "count": len(shipment_list),
                "results": shipment_list
            }
    
    except Exception as e:
        logger.error(f"❌ Error in advanced search: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def query_shipments_by_criteria(
    search_text: Optional[str] = None,
    include_fields: Optional[List[str]] = None,
    sort_by: str = "eta",
    sort_order: str = "asc",
    limit: int = 10
) -> dict:
    """
    Flexible query tool that searches across multiple fields and returns customizable results.
    
    Args:
        search_text: Text to search across container, bill, vessel, ports, location (partial match)
        include_fields: List of fields to include in results (default: all)
        sort_by: Field to sort by (eta, etd, status_code, risk_flag, id)
        sort_order: Sort order (asc or desc)
        limit: Maximum results to return
    
    Returns:
        Dictionary with matching shipments
    """
    logger.info(f"🔎 Querying shipments: search='{search_text}', sort={sort_by} {sort_order}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment)
            
            # Apply text search across multiple fields
            if search_text:
                search_pattern = f"%{search_text}%"
                query = query.where(
                    or_(
                        Shipment.container_no.like(search_pattern),
                        Shipment.master_bill.like(search_pattern),
                        Shipment.vessel_name.like(search_pattern),
                        Shipment.origin_port.like(search_pattern),
                        Shipment.destination_port.like(search_pattern),
                        Shipment.current_location.like(search_pattern),
                        Shipment.status_description.like(search_pattern)
                    )
                )
            
            # Apply sorting
            sort_column = getattr(Shipment, sort_by, Shipment.eta)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            query = query.limit(limit)
            result = await session.execute(query)
            shipments = result.scalars().all()
            
            # Build results with selected fields
            all_fields = [
                "id", "container_no", "master_bill", "vessel_name", "voyage_number",
                "origin_port", "destination_port", "status_code", "status_description",
                "risk_flag", "current_location", "eta", "etd", "agent_notes"
            ]
            
            fields_to_include = include_fields if include_fields else all_fields
            
            shipment_list = []
            for s in shipments:
                ship_dict = {}
                for field in fields_to_include:
                    value = getattr(s, field, None)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    ship_dict[field] = value
                shipment_list.append(ship_dict)
            
            logger.info(f"✅ Query found {len(shipment_list)} shipments")
            return {
                "success": True,
                "count": len(shipment_list),
                "query": {
                    "search_text": search_text,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                },
                "results": shipment_list
            }
    
    except Exception as e:
        logger.error(f"❌ Error querying shipments: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# ANALYTICS & REPORTING TOOLS
# ============================================================================

async def get_shipments_analytics() -> dict:
    """
    Get analytics and statistics about all shipments.
    
    Returns:
        Dictionary with comprehensive statistics including:
        - Total shipments count
        - Count by status
        - Risk flagged shipments
        - Top ports (origin/destination)
        - Vessels in use
        - Delayed shipments
        - Upcoming arrivals (next 7 days)
    """
    logger.info("📊 Getting shipments analytics")
    
    try:
        async with get_db_context() as session:
            # Total count
            total_result = await session.execute(select(func.count(Shipment.id)))
            total_count = total_result.scalar()
            
            # Count by status
            status_result = await session.execute(
                select(Shipment.status_code, func.count(Shipment.id))
                .group_by(Shipment.status_code)
            )
            status_counts = {status: count for status, count in status_result.all()}
            
            # Risk flagged
            risk_result = await session.execute(
                select(func.count(Shipment.id))
                .where(Shipment.risk_flag == True)
            )
            risk_count = risk_result.scalar()
            
            # Top origin ports
            origin_result = await session.execute(
                select(Shipment.origin_port, func.count(Shipment.id))
                .group_by(Shipment.origin_port)
                .order_by(func.count(Shipment.id).desc())
                .limit(5)
            )
            top_origins = [{"port": port, "count": count} for port, count in origin_result.all()]
            
            # Top destination ports
            dest_result = await session.execute(
                select(Shipment.destination_port, func.count(Shipment.id))
                .group_by(Shipment.destination_port)
                .order_by(func.count(Shipment.id).desc())
                .limit(5)
            )
            top_destinations = [{"port": port, "count": count} for port, count in dest_result.all()]
            
            # Active vessels
            vessel_result = await session.execute(
                select(Shipment.vessel_name)
                .distinct()
                .where(Shipment.status_code.in_(['IN_TRANSIT', 'AT_PORT']))
            )
            active_vessels = [v[0] for v in vessel_result.all() if v[0]]
            
            # Upcoming arrivals (next 7 days)
            now = datetime.now()
            week_later = now + timedelta(days=7)
            upcoming_result = await session.execute(
                select(Shipment)
                .where(and_(
                    Shipment.eta >= now,
                    Shipment.eta <= week_later
                ))
                .order_by(Shipment.eta)
            )
            upcoming_shipments = upcoming_result.scalars().all()
            upcoming_list = [
                {
                    "id": s.id,
                    "container_no": s.container_no,
                    "eta": s.eta.isoformat() if s.eta else None,
                    "destination": s.destination_port
                }
                for s in upcoming_shipments
            ]
            
            analytics = {
                "success": True,
                "summary": {
                    "total_shipments": total_count,
                    "risk_flagged": risk_count,
                    "status_breakdown": status_counts,
                    "active_vessels_count": len(active_vessels)
                },
                "details": {
                    "top_origin_ports": top_origins,
                    "top_destination_ports": top_destinations,
                    "active_vessels": active_vessels,
                    "upcoming_arrivals": {
                        "count": len(upcoming_list),
                        "shipments": upcoming_list
                    }
                }
            }
            
            logger.info(f"✅ Analytics generated: {total_count} total shipments")
            return analytics
    
    except Exception as e:
        logger.error(f"❌ Error generating analytics: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def get_delayed_shipments(days_delayed: int = 1) -> dict:
    """
    Find shipments that are delayed beyond their original ETA.
    
    Args:
        days_delayed: Minimum number of days past ETA to consider (default 1)
    
    Returns:
        List of delayed shipments with delay information
    """
    logger.info(f"⏰ Finding shipments delayed by {days_delayed}+ days")
    
    try:
        async with get_db_context() as session:
            now = datetime.now()
            cutoff_date = now - timedelta(days=days_delayed)
            
            query = select(Shipment).where(
                and_(
                    Shipment.eta < cutoff_date,
                    Shipment.status_code.in_(['IN_TRANSIT', 'DELAYED', 'AT_PORT', 'CUSTOMS_HOLD'])
                )
            ).order_by(Shipment.eta.asc())
            
            result = await session.execute(query)
            shipments = result.scalars().all()
            
            delayed_list = []
            for s in shipments:
                if s.eta:
                    days_late = (now - s.eta).days
                    delayed_list.append({
                        "id": s.id,
                        "container_no": s.container_no,
                        "vessel_name": s.vessel_name,
                        "status": s.status_code,
                        "origin": s.origin_port,
                        "destination": s.destination_port,
                        "original_eta": s.eta.isoformat(),
                        "days_delayed": days_late,
                        "risk_flag": s.risk_flag,
                        "agent_notes": s.agent_notes
                    })
            
            logger.info(f"✅ Found {len(delayed_list)} delayed shipments")
            return {
                "success": True,
                "count": len(delayed_list),
                "criteria": f"Delayed by {days_delayed}+ days",
                "results": delayed_list
            }
    
    except Exception as e:
        logger.error(f"❌ Error finding delayed shipments: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def get_shipments_by_route(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    status_filter: Optional[str] = None
) -> dict:
    """
    Get shipments on a specific trade route (origin to destination).
    
    Args:
        origin: Origin port (partial match)
        destination: Destination port (partial match)
        status_filter: Optional status code filter
    
    Returns:
        Shipments on the specified route with summary statistics
    """
    logger.info(f"🌍 Getting shipments on route: {origin} → {destination}")
    
    try:
        async with get_db_context() as session:
            query = select(Shipment)
            
            if origin:
                query = query.where(Shipment.origin_port.like(f"%{origin}%"))
            if destination:
                query = query.where(Shipment.destination_port.like(f"%{destination}%"))
            if status_filter:
                query = query.where(Shipment.status_code == status_filter)
            
            result = await session.execute(query)
            shipments = result.scalars().all()
            
            # Calculate route statistics
            total = len(shipments)
            in_transit = sum(1 for s in shipments if s.status_code == 'IN_TRANSIT')
            delayed = sum(1 for s in shipments if s.status_code == 'DELAYED')
            at_risk = sum(1 for s in shipments if s.risk_flag)
            
            shipment_list = [
                {
                    "id": s.id,
                    "container_no": s.container_no,
                    "vessel_name": s.vessel_name,
                    "status": s.status_code,
                    "origin": s.origin_port,
                    "destination": s.destination_port,
                    "eta": s.eta.isoformat() if s.eta else None,
                    "risk_flag": s.risk_flag
                }
                for s in shipments
            ]
            
            logger.info(f"✅ Found {total} shipments on route")
            return {
                "success": True,
                "route": {
                    "origin": origin,
                    "destination": destination
                },
                "statistics": {
                    "total": total,
                    "in_transit": in_transit,
                    "delayed": delayed,
                    "at_risk": at_risk
                },
                "shipments": shipment_list
            }
    
    except Exception as e:
        logger.error(f"❌ Error getting route shipments: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# PREDICTIVE AI TOOLS
# ============================================================================

async def predictive_delay_detection(identifier: str) -> dict:
    """
    Predict if a shipment will be delayed using ML model.
    
    Uses trained Random Forest classifier to analyze shipment characteristics
    and predict delay probability 48-72 hours in advance.
    
    Args:
        identifier: Shipment ID, container number, or bill of lading
    
    Returns:
        {
            "success": bool,
            "shipment_id": str,
            "will_delay": bool,
            "confidence": float (0-1),
            "delay_probability": float,
            "risk_factors": [str],
            "recommendation": str,
            "model_accuracy": float
        }
    
    Example:
        >>> await predictive_delay_detection("job-2025-001")
        {
            "will_delay": true,
            "confidence": 0.85,
            "delay_probability": 0.78,
            "risk_factors": ["Peak shipping season", "High-risk route"],
            "recommendation": "HIGH RISK: 78% chance of delay. Consider proactive notification."
        }
    """
    logger.info(f"🔮 Predicting delay for: {identifier}")
    
    try:
        # Fetch shipment data
        async with get_db_context() as session:
            query = select(Shipment).where(
                (Shipment.id == identifier) |
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
            
            # Prepare shipment data for prediction
            shipment_data = {
                "id": shipment.id,
                "origin_port": shipment.origin_port,
                "destination_port": shipment.destination_port,
                "vessel_name": shipment.vessel_name,
                "etd": shipment.etd.isoformat() if shipment.etd else None,
                "eta": shipment.eta.isoformat() if shipment.eta else None,
                "risk_flag": shipment.risk_flag,
                "status_code": shipment.status_code,
                "container_type": "40HC"  # Default if not in model
            }
            
            # Call Analytics Engine API for prediction
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.post(
                        f"{ANALYTICS_ENGINE_URL}/predict-delay",
                        json={"shipment_data": shipment_data}
                    )
                    response.raise_for_status()
                    prediction = response.json()
                    
                except httpx.HTTPError as e:
                    logger.error(f"❌ Analytics Engine API error: {e}")
                    return {
                        "success": False,
                        "error": f"Analytics Engine unavailable: {str(e)}"
                    }
            
            if not prediction.get("success"):
                return prediction
            
            # Add shipment context
            prediction["shipment_id"] = shipment.id
            prediction["current_status"] = shipment.status_code
            prediction["origin"] = shipment.origin_port
            prediction["destination"] = shipment.destination_port
            prediction["vessel"] = shipment.vessel_name
            
            logger.info(
                f"✅ Prediction complete: {'DELAYED' if prediction['will_delay'] else 'ON-TIME'} "
                f"(confidence: {prediction['confidence']:.1%})"
            )
            
            return prediction
    
    except Exception as e:
        logger.error(f"❌ Error in delay prediction: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# VESSEL TRACKING TOOLS
# ============================================================================

async def real_time_vessel_tracking(vessel_name: str) -> dict:
    """
    Track a vessel in real-time using AIS (Automatic Identification System) data.
    
    Get live position, speed, heading, status, destination, and ETA for any commercial vessel.
    This tool uses real API data when available, with realistic mock data as fallback.
    
    Args:
        vessel_name: Name of the vessel to track (e.g., "MAERSK ESSEX", "MSC GULSUN", "EVER GIVEN")
    
    Returns:
        Real-time vessel tracking data including:
        - Vessel identification (name, IMO, MMSI, type, flag)
        - Current position (latitude, longitude, timestamp)
        - Navigation data (speed in knots, heading in degrees, status)
        - Destination port and estimated arrival time
        - Data source (API or Mock)
    
    Examples:
        >>> await real_time_vessel_tracking("MAERSK ESSEX")
        {
            "success": True,
            "vessel_name": "MAERSK ESSEX",
            "imo": "9632506",
            "mmsi": "219024000",
            "vessel_type": "Container Ship",
            "position": {"lat": 35.4521, "lon": 115.2341, "timestamp": "2026-01-05T..."},
            "navigation": {"speed": 19.5, "heading": 245, "status": "Under way using engine"},
            "destination": "Rotterdam",
            "eta": "2026-01-18T14:00:00Z",
            "data_source": "Mock Data (Simulated)"
        }
    """
    logger.info(f"🚢 Tracking vessel: {vessel_name}")
    
    try:
        # Search for vessel first
        vessel_info = await vessel_tracker.search_vessel(vessel_name)
        
        if not vessel_info:
            logger.warning(f"⚠️ Vessel not found: {vessel_name}")
            return {
                "success": False,
                "error": f"Vessel not found: {vessel_name}",
                "suggestion": "Available vessels (mock): MAERSK ESSEX, MSC GULSUN, COSCO SHIPPING UNIVERSE, EVER GIVEN, CMA CGM ANTOINE DE SAINT EXUPERY"
            }
        
        # Get current position
        position_data = await vessel_tracker.get_vessel_position(vessel_name=vessel_name)
        
        if not position_data:
            logger.error(f"❌ Could not get position for {vessel_name}")
            return {
                "success": False,
                "error": f"Could not retrieve position data for {vessel_name}"
            }
        
        logger.info(f"✅ Vessel tracked: {vessel_name} at {position_data['position']['lat']}, {position_data['position']['lon']}")
        
        return {
            "success": True,
            **position_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error tracking vessel: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# SYSTEM TOOLS
# ============================================================================

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
            "tools_registered": 11,
            "database": "connected",
            "transport": "FastMCP SSE"
        }
    
    return status


# ============================================================================
# Document Generation Tools (via Analytics Engine)
# ============================================================================

async def generate_bill_of_lading(shipment_id: str) -> dict:
    """
    Generate a Bill of Lading (BOL) PDF document for a shipment.
    
    The Bill of Lading is the most critical shipping document - it serves as:
    - Receipt of goods by the carrier
    - Contract of carriage
    - Document of title to the goods
    
    Args:
        shipment_id: Unique shipment identifier (e.g., "job-2025-001")
    
    Returns:
        dict: {
            "success": bool,
            "document_type": "BILL_OF_LADING",
            "document_number": str,
            "file_path": str,
            "document_url": str,
            "file_size_kb": float
        }
    
    Example:
        >>> result = await generate_bill_of_lading("job-2025-001")
        >>> print(result["document_url"])
        "/documents/BOL_job-2025-001_20260105.pdf"
    """
    try:
        logger.info(f"Generating Bill of Lading for shipment {shipment_id}")
        
        # Get shipment data from database
        async with get_db_context() as session:
            query = select(Shipment).where(Shipment.id == shipment_id)
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                return {
                    "success": False,
                    "error": f"Shipment {shipment_id} not found"
                }
        
        # Prepare BOL data
        bol_data = {
            "shipment_id": shipment_id,
            "carrier_name": shipment.carrier_name if hasattr(shipment, 'carrier_name') else "N/A",
            "vessel_name": shipment.vessel_name or "N/A",
            "voyage_number": shipment.voyage_number or "N/A",
            "port_of_loading": shipment.origin_port or "N/A",
            "port_of_discharge": shipment.destination_port or "N/A",
            
            # Shipper (from shipment or defaults)
            "shipper_name": shipment.shipper_name if hasattr(shipment, 'shipper_name') else "Shipper Name Required",
            "shipper_address": getattr(shipment, 'shipper_address', 'Shipper Address Required'),
            "shipper_city": getattr(shipment, 'shipper_city', shipment.origin_port or ""),
            "shipper_country": getattr(shipment, 'shipper_country', 'Country Required'),
            
            # Consignee (from shipment or defaults)
            "consignee_name": shipment.consignee_name if hasattr(shipment, 'consignee_name') else "Consignee Name Required",
            "consignee_address": shipment.consignee_address if hasattr(shipment, 'consignee_address') else "Consignee Address Required",
            "consignee_city": shipment.consignee_city if hasattr(shipment, 'consignee_city') else shipment.destination_port or "",
            "consignee_country": shipment.consignee_country if hasattr(shipment, 'consignee_country') else "Country Required",
            
            # Container details (simplified - in production, fetch from containers table)
            "containers": [
                {
                    "number": shipment.container_no or "CNTR1234567",
                    "seal_number": getattr(shipment, 'seal_number', 'SEAL001'),
                    "type": getattr(shipment, 'container_type', '40HC'),
                    "package_count": getattr(shipment, 'package_count', 100),
                    "package_type": getattr(shipment, 'package_type', 'CARTONS'),
                    "description": getattr(shipment, 'cargo_description', 'General Cargo'),
                    "weight": getattr(shipment, 'weight_kg', 15000),
                    "volume": getattr(shipment, 'volume_cbm', 67.5)
                }
            ]
        }
        
        # Call analytics engine to generate PDF
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/generate-document",
                json={
                    "document_type": "BOL",
                    "data": bol_data
                }
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"✅ BOL generated: {result.get('document_url')}")
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error generating BOL: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error generating BOL: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def generate_commercial_invoice(shipment_id: str, invoice_number: Optional[str] = None) -> dict:
    """
    Generate a Commercial Invoice PDF for customs clearance.
    
    The Commercial Invoice is required for international shipments and includes:
    - Exporter/Importer details
    - Itemized list of goods with HS codes
    - Pricing, freight, insurance
    - Total declared value for customs
    
    Args:
        shipment_id: Unique shipment identifier
        invoice_number: Optional invoice number (auto-generated if not provided)
    
    Returns:
        dict: {
            "success": bool,
            "document_type": "COMMERCIAL_INVOICE",
            "invoice_number": str,
            "file_path": str,
            "document_url": str,
            "total_amount": float,
            "currency": str
        }
    
    Example:
        >>> result = await generate_commercial_invoice("job-2025-001", "INV-2025-001")
        >>> print(f"Invoice total: {result['currency']} {result['total_amount']}")
    """
    try:
        logger.info(f"Generating Commercial Invoice for shipment {shipment_id}")
        
        # Get shipment data
        async with get_db_context() as session:
            query = select(Shipment).where(Shipment.id == shipment_id)
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                return {
                    "success": False,
                    "error": f"Shipment {shipment_id} not found"
                }
        
        # Generate invoice number if not provided
        if not invoice_number:
            invoice_number = f"INV-{shipment_id}"
        
        # Prepare invoice data
        invoice_data = {
            "shipment_id": shipment_id,
            "invoice_number": invoice_number,
            "po_number": getattr(shipment, 'po_number', 'N/A'),
            
            # Exporter details
            "exporter_name": getattr(shipment, 'shipper_name', 'Exporter Name Required'),
            "exporter_address": getattr(shipment, 'shipper_address', 'Address Required'),
            "exporter_city": getattr(shipment, 'shipper_city', shipment.origin_port or ""),
            "exporter_country": getattr(shipment, 'shipper_country', 'Country Required'),
            "exporter_tax_id": getattr(shipment, 'shipper_tax_id', 'N/A'),
            "exporter_phone": getattr(shipment, 'shipper_phone', 'N/A'),
            
            # Importer details
            "importer_name": getattr(shipment, 'consignee_name', 'Importer Name Required'),
            "importer_address": getattr(shipment, 'consignee_address', 'Address Required'),
            "importer_city": getattr(shipment, 'consignee_city', shipment.destination_port or ""),
            "importer_country": getattr(shipment, 'consignee_country', 'Country Required'),
            "importer_tax_id": getattr(shipment, 'consignee_tax_id', 'N/A'),
            "importer_phone": getattr(shipment, 'consignee_phone', 'N/A'),
            
            # Terms
            "currency": getattr(shipment, 'currency', 'USD'),
            "incoterms": getattr(shipment, 'incoterms', 'FOB'),
            "payment_terms": getattr(shipment, 'payment_terms', 'NET 30'),
            "country_of_origin": getattr(shipment, 'origin_country', 'N/A'),
            
            # Line items (simplified - in production, fetch from line_items table)
            "line_items": [
                {
                    "description": getattr(shipment, 'cargo_description', 'General Cargo'),
                    "part_number": getattr(shipment, 'part_number', 'N/A'),
                    "hs_code": getattr(shipment, 'hs_code', '0000.00.0000'),
                    "quantity": getattr(shipment, 'package_count', 100),
                    "unit": "PCS",
                    "unit_price": getattr(shipment, 'unit_price', 100.00),
                    "country_of_origin": getattr(shipment, 'origin_country', 'N/A')
                }
            ],
            
            # Charges
            "freight_charges": getattr(shipment, 'freight_charges', 2500.00),
            "insurance_charges": getattr(shipment, 'insurance_charges', 300.00),
            "discount_percentage": 0,
            "vat_percentage": 0
        }
        
        # Call analytics engine
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/generate-document",
                json={
                    "document_type": "COMMERCIAL_INVOICE",
                    "data": invoice_data
                }
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"✅ Invoice generated: {result.get('document_url')}")
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error generating invoice: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error generating invoice: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def generate_packing_list(shipment_id: str, packing_list_number: Optional[str] = None) -> dict:
    """
    Generate a Packing List PDF with detailed cargo breakdown.
    
    The Packing List provides detailed information about package contents:
    - Package-by-package breakdown
    - Items within each package
    - Dimensions and weights
    - Special handling instructions
    
    Args:
        shipment_id: Unique shipment identifier
        packing_list_number: Optional packing list number (auto-generated if not provided)
    
    Returns:
        dict: {
            "success": bool,
            "document_type": "PACKING_LIST",
            "packing_list_number": str,
            "file_path": str,
            "document_url": str,
            "total_packages": int,
            "total_weight_kg": float
        }
    
    Example:
        >>> result = await generate_packing_list("job-2025-001")
        >>> print(f"Total packages: {result['total_packages']}")
    """
    try:
        logger.info(f"Generating Packing List for shipment {shipment_id}")
        
        # Get shipment data
        async with get_db_context() as session:
            query = select(Shipment).where(Shipment.id == shipment_id)
            result = await session.execute(query)
            shipment = result.scalar_one_or_none()
            
            if not shipment:
                return {
                    "success": False,
                    "error": f"Shipment {shipment_id} not found"
                }
        
        # Generate packing list number if not provided
        if not packing_list_number:
            packing_list_number = f"PKG-{shipment_id}"
        
        # Prepare packing list data
        packing_data = {
            "shipment_id": shipment_id,
            "packing_list_number": packing_list_number,
            "invoice_number": f"INV-{shipment_id}",
            "bl_number": f"BOL-{shipment_id}",
            "container_number": shipment.container_no or "CNTR1234567",
            
            # Shipper/Consignee
            "shipper_name": getattr(shipment, 'shipper_name', 'Shipper Name Required'),
            "shipper_address": getattr(shipment, 'shipper_address', 'Address Required'),
            "shipper_city": getattr(shipment, 'shipper_city', shipment.origin_port or ""),
            "shipper_country": getattr(shipment, 'shipper_country', 'Country Required'),
            "shipper_contact": getattr(shipment, 'shipper_phone', 'N/A'),
            
            "consignee_name": getattr(shipment, 'consignee_name', 'Consignee Name Required'),
            "consignee_address": getattr(shipment, 'consignee_address', 'Address Required'),
            "consignee_city": getattr(shipment, 'consignee_city', shipment.destination_port or ""),
            "consignee_country": getattr(shipment, 'consignee_country', 'Country Required'),
            "consignee_contact": getattr(shipment, 'consignee_phone', 'N/A'),
            
            # Port info
            "port_of_loading": shipment.origin_port or "N/A",
            "port_of_discharge": shipment.destination_port or "N/A",
            
            # Package details (simplified - in production, fetch from packages table)
            "packages": [
                {
                    "package_id": f"PKG-001",
                    "package_type": getattr(shipment, 'package_type', 'CARTON'),
                    "marks": f"{shipment_id}-001",
                    "length": 120,
                    "width": 80,
                    "height": 100,
                    "volume": 0.96,
                    "gross_weight": getattr(shipment, 'weight_kg', 250.0),
                    "net_weight": getattr(shipment, 'weight_kg', 250.0) * 0.95,
                    "items": [
                        {
                            "description": getattr(shipment, 'cargo_description', 'General Cargo'),
                            "part_number": getattr(shipment, 'part_number', 'N/A'),
                            "quantity": getattr(shipment, 'package_count', 100),
                            "unit_weight": getattr(shipment, 'weight_kg', 250.0) / getattr(shipment, 'package_count', 100),
                            "total_weight": getattr(shipment, 'weight_kg', 250.0) * 0.95
                        }
                    ]
                }
            ],
            
            # Special instructions
            "special_instructions": getattr(shipment, 'special_instructions', ''),
            "is_fragile": getattr(shipment, 'is_fragile', False)
        }
        
        # Call analytics engine
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/generate-document",
                json={
                    "document_type": "PACKING_LIST",
                    "data": packing_data
                }
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"✅ Packing list generated: {result.get('document_url')}")
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error generating packing list: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error generating packing list: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# REAL-TIME TRACKING TOOLS (DAY 6 - TOOLS 12-14)
# ============================================================================

async def track_vessel_realtime(
    vessel_name: Optional[str] = None,
    imo_number: Optional[str] = None,
    mmsi: Optional[str] = None
) -> dict:
    """
    Track vessel in real-time using AIS data.
    
    Provides live position, speed, heading, course, and estimated arrival information
    for ocean vessels. Can search by vessel name, IMO number, or MMSI.
    
    Args:
        vessel_name: Name of the vessel (e.g., "MAERSK SEALAND")
        imo_number: International Maritime Organization number (7 digits)
        mmsi: Maritime Mobile Service Identity (9 digits)
    
    Returns:
        Dictionary with vessel tracking data including:
        - Vessel identification
        - Current GPS position (lat/lon)
        - Speed in knots
        - Heading in degrees
        - Vessel status (underway, at anchor, etc.)
        - Next port of call
        - Estimated time of arrival
    
    Example:
        >>> track_vessel_realtime(vessel_name="MAERSK")
        {
            "success": True,
            "data": {
                "vessel_name": "MAERSK SEALAND",
                "position": {"lat": 37.776995, "lon": -122.420063},
                "speed": 12.64,
                "heading": 273.0,
                "status": "Underway using engine",
                "next_port": "Oakland",
                "eta": "2025-01-25T14:00:00Z"
            }
        }
    """
    logger.info(f"🚢 Tracking vessel: name={vessel_name}, imo={imo_number}, mmsi={mmsi}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/api/vessel/track",
                json={
                    "vessel_name": vessel_name,
                    "imo_number": imo_number,
                    "mmsi": mmsi
                }
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Vessel tracked: {result.get('data', {}).get('vessel_name', 'Unknown')}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error tracking vessel: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error tracking vessel: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def track_multimodal_shipment(shipment_id: str) -> dict:
    """
    Track shipment across multiple transport modes (ocean, rail, truck).
    
    Provides comprehensive journey tracking showing all transport legs from origin
    to destination, including progress percentage, current location, and handoff points
    between different carriers and transport modes.
    
    Args:
        shipment_id: Shipment or job number (e.g., "job-2025-001")
    
    Returns:
        Dictionary with multimodal tracking data including:
        - Overall shipment status and progress percentage
        - Current transport mode and location
        - All transport legs (completed, in-progress, planned)
        - Handoff events between carriers
        - Distance and ETA for each leg
        - Origin and final destination
    
    Example:
        >>> track_multimodal_shipment("job-2025-001")
        {
            "success": True,
            "data": {
                "shipment_id": "job-2025-001",
                "status": "in_transit",
                "progress_percentage": 16.7,
                "journey": [
                    {
                        "leg_number": 1,
                        "mode": "ocean",
                        "from": "Shanghai Port",
                        "to": "Los Angeles Port",
                        "status": "in_transit",
                        "eta": "2025-01-23T14:00:00Z"
                    },
                    {
                        "leg_number": 2,
                        "mode": "rail",
                        "from": "Los Angeles Port",
                        "to": "Chicago Rail Yard",
                        "status": "planned"
                    }
                ]
            }
        }
    """
    logger.info(f"🚚 Tracking multimodal shipment: {shipment_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{ANALYTICS_ENGINE_URL}/api/shipment/{shipment_id}/multimodal-tracking"
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Multimodal shipment tracked: {shipment_id} - {result.get('data', {}).get('progress_percentage', 0)}% complete")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error tracking multimodal shipment: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error tracking multimodal shipment: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def track_container_live(container_number: str) -> dict:
    """
    Track container with live IoT sensor data.
    
    Provides real-time container tracking with comprehensive IoT sensor monitoring
    including GPS location, temperature, humidity, shock detection, door sensors,
    and battery levels. Generates alerts for deviations and security events.
    
    Args:
        container_number: Container number (e.g., "MAEU1234567")
    
    Returns:
        Dictionary with live container tracking data including:
        - Container type and shipment assignment
        - GPS location (latitude/longitude)
        - Temperature monitoring (for reefer containers)
        - Humidity levels
        - Shock/impact events with severity
        - Door open/close event history
        - Battery level percentage
        - Active alerts and warnings
    
    Example:
        >>> track_container_live("MAEU1234567")
        {
            "success": True,
            "data": {
                "container_number": "MAEU1234567",
                "container_type": "40HC Reefer",
                "gps": {
                    "latitude": 37.776995,
                    "longitude": -122.420063,
                    "accuracy_meters": 13
                },
                "temperature": {
                    "temperature_celsius": -15.8,
                    "setpoint_celsius": -18.0,
                    "deviation": 2.2
                },
                "alerts": [
                    {
                        "type": "temperature_deviation",
                        "severity": "medium",
                        "message": "Temperature deviation: 2.2°C from setpoint"
                    }
                ]
            }
        }
    """
    logger.info(f"📦 Tracking container with live sensors: {container_number}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{ANALYTICS_ENGINE_URL}/api/container/{container_number}/live-tracking"
            )
            response.raise_for_status()
            
            result = response.json()
            alerts = result.get('data', {}).get('alert_count', 0)
            logger.info(f"✅ Container tracked: {container_number} - {alerts} active alerts")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error tracking container: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error tracking container: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# CUSTOMER COMMUNICATION TOOLS (Day 7 - Tools 28-30)
# ============================================================================

async def send_status_update(
    shipment_id: str,
    notification_type: str,
    recipient_email: Optional[str] = None,
    recipient_phone: Optional[str] = None,
    channel: str = "email",
    language: str = "en"
) -> dict:
    """
    Send shipment status notification to customer via email or SMS.
    
    Args:
        shipment_id: Shipment ID
        notification_type: Type of notification (departed, in_transit, arrived, customs_cleared, delivered, delay_warning, exception_alert)
        recipient_email: Customer email address
        recipient_phone: Customer phone number (format: +1234567890)
        channel: Delivery channel (email, sms, or both)
        language: Notification language (en, ar, zh)
    
    Returns:
        Dictionary with notification delivery status
    """
    logger.info(f"📧 Sending {notification_type} notification for shipment {shipment_id} via {channel}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/api/notifications/send",
                json={
                    "shipment_id": shipment_id,
                    "notification_type": notification_type,
                    "recipient_email": recipient_email,
                    "recipient_phone": recipient_phone,
                    "language": language
                }
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Notification sent successfully for {shipment_id}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending notification: {e}")
        return {
            "success": False,
            "error": f"Analytics engine error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def generate_customer_portal_link(
    shipment_id: str
) -> str:
    """
    Generate a public tracking link for customer portal access without authentication.
    Customers can use this link to track their shipment for 30 days.
    
    Args:
        shipment_id: Shipment ID to create tracking link for
    
    Returns:
        Public tracking URL string (e.g., https://track.cwlogistics.com/abc-123-xyz)
    """
    logger.info(f"🔗 Generating public tracking link for shipment {shipment_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/api/tracking-link/generate",
                json={"shipment_id": shipment_id}
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                tracking_url = result.get("data", {}).get("tracking_url")
                expires_at = result.get("data", {}).get("valid_until")
                logger.info(f"✅ Tracking link generated: {tracking_url} (valid until {expires_at})")
                return f"Public tracking link: {tracking_url}\nValid until: {expires_at}\n\nShare this link with your customer to track their shipment without logging in."
            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"Failed to generate tracking link: {error_msg}")
                return f"Error: {error_msg}"
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error generating tracking link: {e}")
        return f"Error: Unable to generate tracking link. Analytics engine error: {str(e)}"
    except Exception as e:
        logger.error(f"Error generating tracking link: {e}", exc_info=True)
        return f"Error: {str(e)}"


async def proactive_exception_notification(
    shipment_id: str,
    recipient_email: Optional[str] = None
) -> str:
    """
    Proactively warn customers about potential delays using ML predictions (Tool 30).
    
    Automatically runs ML delay prediction and sends notification if confidence > 70%.
    Includes risk factors and recommended actions.
    
    Args:
        shipment_id: Shipment ID to check for delays
        recipient_email: Customer email (optional, will use shipment default if not provided)
    
    Returns:
        Human-readable warning status with ML confidence and details
    """
    logger.info(f"⚠️ Proactive exception check for shipment {shipment_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {"shipment_id": shipment_id}
            if recipient_email:
                payload["recipient_email"] = recipient_email
            
            response = await client.post(
                f"{ANALYTICS_ENGINE_URL}/api/notifications/proactive-delay-warning",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                data = result.get("data", {})
                warning_sent = data.get("warning_sent", False)
                ml_confidence = data.get("ml_confidence", 0.0)
                
                if warning_sent:
                    risk_factors = data.get("risk_factors", [])
                    delay_hours = data.get("predicted_delay_hours", 0)
                    notification_id = data.get("notification_id", "N/A")
                    
                    risk_msg = ", ".join(risk_factors) if risk_factors else "Multiple factors"
                    
                    logger.info(f"✅ Proactive warning sent: {shipment_id}, confidence={ml_confidence:.1%}")
                    return f"""🔔 Proactive Delay Warning Sent!

Shipment: {shipment_id}
ML Confidence: {ml_confidence:.1%}
Predicted Delay: {delay_hours} hours
Risk Factors: {risk_msg}
Notification ID: {notification_id}

Customer has been automatically notified about the potential delay.
Recommended: Review alternative routing options with logistics coordinator."""
                else:
                    reason = data.get("reason", "Unknown")
                    return f"""✓ No proactive warning needed for {shipment_id}

ML Confidence: {ml_confidence:.1%}
Reason: {reason}

Shipment is on track. No customer notification required at this time."""
            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"Failed to check proactive warning: {error_msg}")
                return f"Error: {error_msg}"
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in proactive exception check: {e}")
        return f"Error: Unable to check for delays. Analytics engine error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in proactive exception notification: {e}", exc_info=True)
        return f"Error: {str(e)}"


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

def register_tools(mcp):
    """
    Register all tools with the FastMCP instance.
    
    Args:
        mcp: FastMCP server instance
    """
    logger.info("📝 Registering all MCP tools...")
    
    # Basic search & tracking
    mcp.tool()(search_shipments)
    mcp.tool()(track_shipment)
    
    # Update tools
    mcp.tool()(update_shipment_eta)
    mcp.tool()(set_risk_flag)
    mcp.tool()(add_agent_note)
    
    # Advanced search
    mcp.tool()(search_shipments_advanced)
    mcp.tool()(query_shipments_by_criteria)
    
    # Analytics & reporting
    mcp.tool()(get_shipments_analytics)
    mcp.tool()(get_delayed_shipments)
    mcp.tool()(get_shipments_by_route)
    
    # Predictive AI
    mcp.tool()(predictive_delay_detection)
    
    # Vessel tracking (legacy)
    mcp.tool()(real_time_vessel_tracking)
    
    # Document generation
    mcp.tool()(generate_bill_of_lading)
    mcp.tool()(generate_commercial_invoice)
    mcp.tool()(generate_packing_list)
    
    # Real-time tracking (Day 6 - Tools 12-14)
    mcp.tool()(track_vessel_realtime)
    mcp.tool()(track_multimodal_shipment)
    mcp.tool()(track_container_live)
    
    # Customer communication (Day 7 - Tools 28-30)
    mcp.tool()(send_status_update)
    mcp.tool()(generate_customer_portal_link)
    mcp.tool()(proactive_exception_notification)
    
    # System
    mcp.tool()(get_server_status)
    
    logger.info("✅ All 22 tools registered successfully!")

