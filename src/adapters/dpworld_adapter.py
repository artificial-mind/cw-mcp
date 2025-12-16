"""
DP World API Adapter - Mock implementation
"""
from typing import Dict, Any
from datetime import datetime
import logging

from .base_adapter import BaseLogisticsAdapter, AdapterError
from config import settings

logger = logging.getLogger(__name__)


class DPWorldAdapter(BaseLogisticsAdapter):
    """
    Adapter for DP World terminal operations
    This is a MOCK implementation - replace with real API calls in production
    """
    
    def __init__(self):
        super().__init__(
            api_url=settings.DPWORLD_API_URL,
            api_key=settings.DPWORLD_API_KEY
        )
    
    async def normalize_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize DP World's response format to our standard format
        DP World uses snake_case and different structure
        """
        try:
            return {
                "id": raw_data.get("booking_ref"),
                "tracking": {
                    "container": raw_data.get("container_id"),
                    "vessel": raw_data.get("vessel_name"),
                    "voyage": raw_data.get("voyage_ref"),
                    "location": {
                        "lat": raw_data.get("gps_lat"),
                        "lng": raw_data.get("gps_lng"),
                        "name": raw_data.get("port_name") or raw_data.get("terminal_name")
                    }
                },
                "schedule": {
                    "etd": raw_data.get("scheduled_departure"),
                    "eta": raw_data.get("estimated_arrival")
                },
                "status": {
                    "code": self._normalize_status_code(raw_data.get("operation_status")),
                    "description": raw_data.get("status_details")
                },
                "flags": {
                    "is_risk": False,
                    "agent_notes": None
                },
                "metadata": {
                    "master_bill": raw_data.get("bl_number"),
                    "created_at": raw_data.get("created_date"),
                    "updated_at": raw_data.get("modified_date")
                }
            }
        except Exception as e:
            raise AdapterError(
                "Failed to normalize DP World response",
                vendor="DPWorld",
                original_error=e
            )
    
    def _normalize_status_code(self, dpworld_status: str) -> str:
        """Map DP World status codes to our standard codes"""
        status_map = {
            "GATE_IN": "AT_PORT",
            "YARD_STORAGE": "AT_PORT",
            "VESSEL_LOADING": "IN_TRANSIT",
            "ON_BOARD": "IN_TRANSIT",
            "VESSEL_DISCHARGE": "AT_PORT",
            "GATE_OUT": "DELIVERED",
            "CUSTOMS_INSPECT": "CUSTOMS_HOLD",
            "DELAYED_VESSEL": "DELAYED",
            "AWAITING_DOCS": "CUSTOMS_HOLD"
        }
        return status_map.get(dpworld_status, "UNKNOWN")
    
    async def fetch_shipment(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch shipment from DP World API
        MOCK: Returns simulated data instead of real API call
        """
        logger.info(f"[MOCK] Fetching shipment {identifier} from DP World")
        
        # MOCK response - simulating DP World's format
        mock_raw_data = {
            "booking_ref": identifier,
            "bl_number": "COSU987654321",
            "container_id": "COSU9876543",
            "container_type": "40GP",
            "vessel_name": "COSCO SHIPPING UNIVERSE",
            "voyage_ref": "012E",
            "terminal_name": "Jebel Ali Terminal 1",
            "port_name": "Jebel Ali",
            "gps_lat": 25.0095,
            "gps_lng": 55.1136,
            "scheduled_departure": "2025-12-05T10:00:00Z",
            "estimated_arrival": "2025-12-22T16:00:00Z",
            "operation_status": "ON_BOARD",
            "status_details": "Container on vessel, in transit",
            "created_date": "2025-12-04T08:00:00Z",
            "modified_date": datetime.utcnow().isoformat()
        }
        
        return await self.normalize_response(mock_raw_data)
    
    async def update_shipment(
        self,
        identifier: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Push update to DP World API
        MOCK: Simulates successful update
        """
        logger.info(f"[MOCK] Updating shipment {identifier} in DP World: {update_data}")
        
        # MOCK: Always succeeds
        return True
