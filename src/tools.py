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
    
    # Vessel tracking
    mcp.tool()(real_time_vessel_tracking)
    
    # System
    mcp.tool()(get_server_status)
    
    logger.info("✅ All 13 tools registered successfully!")
