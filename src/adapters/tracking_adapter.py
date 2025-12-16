"""
Generic Tracking API Adapter - Mock implementation
"""
from typing import Dict, Any
from datetime import datetime
import logging

from .base_adapter import BaseLogisticsAdapter, AdapterError
from config import settings

logger = logging.getLogger(__name__)


class TrackingAPIAdapter(BaseLogisticsAdapter):
    """
    Adapter for generic container tracking APIs (e.g., Container Tracking API, TrackTrace)
    This is a MOCK implementation - replace with real API calls in production
    """
    
    def __init__(self):
        super().__init__(
            api_url=settings.TRACKING_API_URL,
            api_key=settings.TRACKING_API_KEY
        )
    
    async def normalize_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize generic tracking API response to our standard format
        """
        try:
            # Generic tracking APIs often use a flat structure
            tracking_data = raw_data.get("data", {})
            
            return {
                "id": tracking_data.get("tracking_number") or tracking_data.get("reference"),
                "tracking": {
                    "container": tracking_data.get("container_number"),
                    "vessel": tracking_data.get("vessel"),
                    "voyage": tracking_data.get("voyage"),
                    "location": {
                        "lat": tracking_data.get("latitude"),
                        "lng": tracking_data.get("longitude"),
                        "name": tracking_data.get("location")
                    }
                },
                "schedule": {
                    "etd": tracking_data.get("departure_time"),
                    "eta": tracking_data.get("arrival_time")
                },
                "status": {
                    "code": self._normalize_status_code(tracking_data.get("status")),
                    "description": tracking_data.get("status_description")
                },
                "flags": {
                    "is_risk": False,
                    "agent_notes": None
                },
                "metadata": {
                    "master_bill": tracking_data.get("bill_of_lading"),
                    "created_at": tracking_data.get("first_tracked"),
                    "updated_at": tracking_data.get("last_update")
                }
            }
        except Exception as e:
            raise AdapterError(
                "Failed to normalize Tracking API response",
                vendor="TrackingAPI",
                original_error=e
            )
    
    def _normalize_status_code(self, tracking_status: str) -> str:
        """Map tracking API status codes to our standard codes"""
        if not tracking_status:
            return "UNKNOWN"
        
        status_upper = tracking_status.upper()
        status_map = {
            "PENDING": "BOOKED",
            "BOOKED": "BOOKED",
            "IN TRANSIT": "IN_TRANSIT",
            "TRANSIT": "IN_TRANSIT",
            "AT PORT": "AT_PORT",
            "PORT": "AT_PORT",
            "CUSTOMS": "CUSTOMS_HOLD",
            "DELIVERED": "DELIVERED",
            "COMPLETE": "DELIVERED",
            "DELAYED": "DELAYED",
            "EXCEPTION": "DELAYED"
        }
        
        for key, value in status_map.items():
            if key in status_upper:
                return value
        
        return "UNKNOWN"
    
    async def fetch_shipment(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch shipment from generic Tracking API
        MOCK: Returns simulated data instead of real API call
        """
        logger.info(f"[MOCK] Fetching shipment {identifier} from Tracking API")
        
        # MOCK response - simulating generic tracking API format
        mock_raw_data = {
            "success": True,
            "data": {
                "tracking_number": identifier,
                "container_number": "OOLU4567891",
                "bill_of_lading": "OOLU456789123",
                "vessel": "OOCL HONG KONG",
                "voyage": "087N",
                "location": "Port of Rotterdam",
                "latitude": 51.9244,
                "longitude": 4.4777,
                "departure_time": "2025-11-28T14:00:00Z",
                "arrival_time": "2025-12-15T09:00:00Z",
                "status": "AT PORT",
                "status_description": "Container arrived at port, awaiting customs clearance",
                "first_tracked": "2025-11-28T14:00:00Z",
                "last_update": datetime.utcnow().isoformat()
            }
        }
        
        return await self.normalize_response(mock_raw_data)
    
    async def update_shipment(
        self,
        identifier: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Push update to Tracking API
        MOCK: Simulates successful update
        Note: Most tracking APIs are read-only, but we implement this for consistency
        """
        logger.info(f"[MOCK] Updating shipment {identifier} in Tracking API: {update_data}")
        
        # MOCK: Always succeeds (though real tracking APIs typically don't allow updates)
        logger.warning("Tracking API typically does not support updates - this is a mock")
        return True
