"""
MCP Tools for Logistics Orchestrator
These tools are exposed to AI agents via the MCP protocol
"""
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent

from database.database import get_db_context
from database.crud import ShipmentCRUD, AuditLogCRUD
from adapters import LogitudeAdapter, DPWorldAdapter, TrackingAPIAdapter, AdapterError

logger = logging.getLogger(__name__)


class LogisticsTools:
    """Container for all logistics MCP tools"""
    
    def __init__(self, server: Server):
        self.server = server
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools with the MCP server"""
        
        # Tool 1: Track Shipment
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="track_shipment",
                    description=(
                        "Fetch comprehensive shipment data by tracking number, container number, or "
                        "master bill of lading. Returns standardized tracking information including "
                        "vessel details, location, schedule, and status. Data is fetched from both "
                        "external APIs (Logitude, DP World) and local cache with risk flags and agent notes."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "identifier": {
                                "type": "string",
                                "description": "Shipment ID, container number, or master bill of lading"
                            },
                            "source": {
                                "type": "string",
                                "enum": ["local", "logitude", "dpworld", "tracking"],
                                "description": "Data source to query (default: local)",
                                "default": "local"
                            }
                        },
                        "required": ["identifier"]
                    }
                ),
                Tool(
                    name="update_shipment_eta",
                    description=(
                        "Update the Estimated Time of Arrival (ETA) for a shipment. Implements dual-write "
                        "pattern: updates both local database and attempts to push to external API (Logitude). "
                        "Creates audit log with reasoning. Use this when vessel delays or schedule changes occur."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "shipment_id": {
                                "type": "string",
                                "description": "The shipment ID to update"
                            },
                            "new_eta": {
                                "type": "string",
                                "description": "New ETA in ISO 8601 format (e.g., '2025-12-25T14:30:00')"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Explanation for the ETA change (e.g., 'Weather delay in Suez Canal')"
                            }
                        },
                        "required": ["shipment_id", "new_eta", "reason"]
                    }
                ),
                Tool(
                    name="set_risk_flag",
                    description=(
                        "Flag a shipment as high-risk or remove the risk flag. Risk flags help prioritize "
                        "shipments that need attention (e.g., major delays, angry customers, customs issues). "
                        "This field is stored locally and not synced to external APIs."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "shipment_id": {
                                "type": "string",
                                "description": "The shipment ID to flag"
                            },
                            "is_risk": {
                                "type": "boolean",
                                "description": "True to flag as risk, False to remove flag"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why this shipment is flagged (e.g., 'Customer escalation due to delay')"
                            }
                        },
                        "required": ["shipment_id", "is_risk", "reason"]
                    }
                ),
                Tool(
                    name="add_agent_note",
                    description=(
                        "Add or update agent notes for a shipment. Use this to record important observations, "
                        "customer communications, or action items that don't fit into structured fields. "
                        "Notes are stored locally and persist across queries."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "shipment_id": {
                                "type": "string",
                                "description": "The shipment ID to add notes to"
                            },
                            "note": {
                                "type": "string",
                                "description": "The note text to add or append"
                            },
                            "append": {
                                "type": "boolean",
                                "description": "If true, append to existing notes. If false, replace (default: true)",
                                "default": True
                            }
                        },
                        "required": ["shipment_id", "note"]
                    }
                ),
                Tool(
                    name="search_shipments",
                    description=(
                        "Search for shipments using flexible filters. Can search by container number, "
                        "master bill, status code, or risk flag. Returns list of matching shipments in "
                        "standard format. Useful for finding all delayed shipments, risky cargo, etc."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "container_no": {
                                "type": "string",
                                "description": "Filter by container number (partial match supported)"
                            },
                            "master_bill": {
                                "type": "string",
                                "description": "Filter by master bill of lading (partial match supported)"
                            },
                            "status_code": {
                                "type": "string",
                                "enum": ["BOOKED", "IN_TRANSIT", "AT_PORT", "CUSTOMS_HOLD", "DELIVERED", "DELAYED"],
                                "description": "Filter by status code"
                            },
                            "risk_flag": {
                                "type": "boolean",
                                "description": "Filter by risk flag (true = only risky, false = only safe)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 50)",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 200
                            }
                        }
                    }
                )
            ]
        
        # Tool implementations
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Route tool calls to appropriate handlers"""
            try:
                if name == "track_shipment":
                    result = await self.track_shipment(**arguments)
                elif name == "update_shipment_eta":
                    result = await self.update_shipment_eta(**arguments)
                elif name == "set_risk_flag":
                    result = await self.set_risk_flag(**arguments)
                elif name == "add_agent_note":
                    result = await self.add_agent_note(**arguments)
                elif name == "search_shipments":
                    result = await self.search_shipments(**arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                import json
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]
            
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)
                import json
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "status": "failed"
                    }, indent=2)
                )]
    
    async def track_shipment(
        self,
        identifier: str,
        source: str = "local"
    ) -> Dict[str, Any]:
        """Fetch shipment data from specified source"""
        
        logger.info(f"Tracking shipment {identifier} from source: {source}")
        
        try:
            if source == "local":
                # Query local database
                async with get_db_context() as db:
                    # Try to find by ID first
                    shipment = await ShipmentCRUD.get_by_id(db, identifier)
                    
                    # If not found, try container number
                    if not shipment:
                        shipment = await ShipmentCRUD.get_by_container(db, identifier)
                    
                    # If not found, try master bill
                    if not shipment:
                        shipment = await ShipmentCRUD.get_by_master_bill(db, identifier)
                    
                    if not shipment:
                        return {
                            "error": f"Shipment {identifier} not found in local database",
                            "suggestion": "Try using source='logitude' or 'dpworld' to query external APIs"
                        }
                    
                    return {
                        "success": True,
                        "source": "local",
                        "data": shipment.to_standard_format()
                    }
            
            elif source == "logitude":
                async with LogitudeAdapter() as adapter:
                    data = await adapter.fetch_shipment(identifier)
                    return {
                        "success": True,
                        "source": "logitude",
                        "data": data
                    }
            
            elif source == "dpworld":
                async with DPWorldAdapter() as adapter:
                    data = await adapter.fetch_shipment(identifier)
                    return {
                        "success": True,
                        "source": "dpworld",
                        "data": data
                    }
            
            elif source == "tracking":
                async with TrackingAPIAdapter() as adapter:
                    data = await adapter.fetch_shipment(identifier)
                    return {
                        "success": True,
                        "source": "tracking",
                        "data": data
                    }
            
            else:
                return {"error": f"Unknown source: {source}"}
        
        except AdapterError as e:
            return {
                "error": f"External API error: {e.message}",
                "vendor": e.vendor,
                "fallback": "Try querying local database with source='local'"
            }
        except Exception as e:
            logger.error(f"Unexpected error in track_shipment: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def update_shipment_eta(
        self,
        shipment_id: str,
        new_eta: str,
        reason: str
    ) -> Dict[str, Any]:
        """Update ETA with dual-write pattern"""
        
        logger.info(f"Updating ETA for {shipment_id} to {new_eta}")
        
        try:
            # Parse new ETA
            try:
                eta_dt = datetime.fromisoformat(new_eta.replace('Z', '+00:00'))
            except ValueError:
                return {"error": "Invalid ETA format. Use ISO 8601 (e.g., '2025-12-25T14:30:00')"}
            
            async with get_db_context() as db:
                # Get current shipment
                shipment = await ShipmentCRUD.get_by_id(db, shipment_id)
                if not shipment:
                    return {"error": f"Shipment {shipment_id} not found"}
                
                old_eta = shipment.eta
                
                # Attempt external API update (with retry logic in adapter)
                external_success = False
                external_error = None
                
                try:
                    async with LogitudeAdapter() as adapter:
                        external_success = await adapter.update_shipment(
                            shipment_id,
                            {"eta": new_eta}
                        )
                except Exception as e:
                    external_error = str(e)
                    logger.warning(f"External API update failed: {e}")
                
                # Update local database regardless of external API result
                await ShipmentCRUD.update(db, shipment_id, {"eta": eta_dt})
                
                # Create audit log
                await AuditLogCRUD.create(
                    db,
                    shipment_id=shipment_id,
                    action="UPDATE_ETA",
                    reason=reason,
                    field_name="eta",
                    old_value=old_eta.isoformat() if old_eta else None,
                    new_value=new_eta,
                    agent_id="ai-agent"
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "shipment_id": shipment_id,
                    "old_eta": old_eta.isoformat() if old_eta else None,
                    "new_eta": new_eta,
                    "local_update": "success",
                    "external_update": "success" if external_success else "failed",
                    "external_error": external_error,
                    "note": "ETA updated in local database" + (
                        " and external API" if external_success else " but external API update failed"
                    )
                }
        
        except Exception as e:
            logger.error(f"Error updating ETA: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def set_risk_flag(
        self,
        shipment_id: str,
        is_risk: bool,
        reason: str
    ) -> Dict[str, Any]:
        """Set or remove risk flag on shipment"""
        
        logger.info(f"Setting risk flag for {shipment_id}: {is_risk}")
        
        try:
            async with get_db_context() as db:
                shipment = await ShipmentCRUD.get_by_id(db, shipment_id)
                if not shipment:
                    return {"error": f"Shipment {shipment_id} not found"}
                
                old_value = shipment.risk_flag
                
                # Update risk flag
                await ShipmentCRUD.update(db, shipment_id, {"risk_flag": is_risk})
                
                # Create audit log
                await AuditLogCRUD.create(
                    db,
                    shipment_id=shipment_id,
                    action="SET_RISK_FLAG" if is_risk else "CLEAR_RISK_FLAG",
                    reason=reason,
                    field_name="risk_flag",
                    old_value=str(old_value),
                    new_value=str(is_risk),
                    agent_id="ai-agent"
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "shipment_id": shipment_id,
                    "risk_flag": is_risk,
                    "previous_value": old_value,
                    "note": f"Risk flag {'set' if is_risk else 'cleared'} successfully"
                }
        
        except Exception as e:
            logger.error(f"Error setting risk flag: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def add_agent_note(
        self,
        shipment_id: str,
        note: str,
        append: bool = True
    ) -> Dict[str, Any]:
        """Add or update agent notes"""
        
        logger.info(f"Adding note to {shipment_id}")
        
        try:
            async with get_db_context() as db:
                shipment = await ShipmentCRUD.get_by_id(db, shipment_id)
                if not shipment:
                    return {"error": f"Shipment {shipment_id} not found"}
                
                old_notes = shipment.agent_notes
                
                # Append or replace
                if append and old_notes:
                    new_notes = f"{old_notes}\n{note}"
                else:
                    new_notes = note
                
                # Update notes
                await ShipmentCRUD.update(db, shipment_id, {"agent_notes": new_notes})
                
                # Create audit log
                await AuditLogCRUD.create(
                    db,
                    shipment_id=shipment_id,
                    action="ADD_NOTE",
                    reason="Agent added observation/note",
                    field_name="agent_notes",
                    old_value=old_notes,
                    new_value=new_notes,
                    agent_id="ai-agent"
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "shipment_id": shipment_id,
                    "note_added": note,
                    "full_notes": new_notes
                }
        
        except Exception as e:
            logger.error(f"Error adding note: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def search_shipments(
        self,
        container_no: Optional[str] = None,
        master_bill: Optional[str] = None,
        status_code: Optional[str] = None,
        risk_flag: Optional[bool] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search shipments with filters"""
        
        logger.info(f"Searching shipments with filters")
        
        try:
            async with get_db_context() as db:
                shipments = await ShipmentCRUD.search(
                    db,
                    container_no=container_no,
                    master_bill=master_bill,
                    status_code=status_code,
                    risk_flag=risk_flag,
                    limit=limit
                )
                
                return {
                    "success": True,
                    "count": len(shipments),
                    "filters_applied": {
                        "container_no": container_no,
                        "master_bill": master_bill,
                        "status_code": status_code,
                        "risk_flag": risk_flag
                    },
                    "results": [s.to_standard_format() for s in shipments]
                }
        
        except Exception as e:
            logger.error(f"Error searching shipments: {e}", exc_info=True)
            return {"error": str(e)}
