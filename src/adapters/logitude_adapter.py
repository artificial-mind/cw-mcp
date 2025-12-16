"""
Logitude API Adapter - Mock implementation
"""
from typing import Dict, Any
from datetime import datetime
import logging

from .base_adapter import BaseLogisticsAdapter, AdapterError
from config import settings

logger = logging.getLogger(__name__)


class LogitudeAdapter(BaseLogisticsAdapter):
    """
    Adapter for Logitude World logistics platform
    This is a MOCK implementation - replace with real API calls in production
    """
    
    def __init__(self):
        super().__init__(
            api_url=settings.LOGITUDE_API_URL,
            api_key=settings.LOGITUDE_API_KEY
        )
    
    async def normalize_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Logitude's response format to our standard format
        Logitude uses different field names than our standard
        """
        try:
            # Logitude uses camelCase and nested structures
            return {
                "id": raw_data.get("referenceNumber"),
                "tracking": {
                    "container": raw_data.get("containerDetails", {}).get("number"),
                    "vessel": raw_data.get("vesselInfo", {}).get("name"),
                    "voyage": raw_data.get("vesselInfo", {}).get("voyageNumber"),
                    "location": {
                        "lat": raw_data.get("currentPosition", {}).get("latitude"),
                        "lng": raw_data.get("currentPosition", {}).get("longitude"),
                        "name": raw_data.get("currentPosition", {}).get("locationName")
                    }
                },
                "schedule": {
                    "etd": raw_data.get("departureDate"),
                    "eta": raw_data.get("arrivalDate")
                },
                "status": {
                    "code": self._normalize_status_code(raw_data.get("statusCode")),
                    "description": raw_data.get("statusMessage")
                },
                "flags": {
                    "is_risk": False,  # Not provided by external API
                    "agent_notes": None  # Not provided by external API
                },
                "metadata": {
                    "master_bill": raw_data.get("masterBillOfLading"),
                    "created_at": raw_data.get("createdAt"),
                    "updated_at": raw_data.get("lastUpdated")
                }
            }
        except Exception as e:
            raise AdapterError(
                "Failed to normalize Logitude response",
                vendor="Logitude",
                original_error=e
            )
    
    def _normalize_status_code(self, logitude_status: str) -> str:
        """Map Logitude status codes to our standard codes"""
        status_map = {
            "BOOKING_CONFIRMED": "BOOKED",
            "CONTAINER_LOADED": "IN_TRANSIT",
            "VESSEL_DEPARTED": "IN_TRANSIT",
            "IN_TRANSIT": "IN_TRANSIT",
            "PORT_ARRIVAL": "AT_PORT",
            "CUSTOMS_CLEARANCE": "CUSTOMS_HOLD",
            "DELIVERED": "DELIVERED",
            "EXCEPTION": "DELAYED"
        }
        return status_map.get(logitude_status, "UNKNOWN")
    
    async def fetch_shipment(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch shipment from Logitude API
        MOCK: Returns simulated data instead of real API call
        """
        logger.info(f"[MOCK] Fetching shipment {identifier} from Logitude")
        
        # In production, this would be:
        # raw_data = await self._make_request("GET", f"/shipments/{identifier}")
        
        # MOCK response - simulating Logitude's format
        mock_raw_data = {
            "referenceNumber": identifier,
            "masterBillOfLading": "MAEU123456789",
            "containerDetails": {
                "number": "MSCU1234567",
                "type": "40HC",
                "seal": "SL123456"
            },
            "vesselInfo": {
                "name": "MSC GULSUN",
                "voyageNumber": "025W",
                "imo": "9454436"
            },
            "currentPosition": {
                "latitude": 22.3193,
                "longitude": 114.1694,
                "locationName": "South China Sea"
            },
            "departureDate": "2025-12-10T08:00:00Z",
            "arrivalDate": "2025-12-25T14:30:00Z",
            "statusCode": "IN_TRANSIT",
            "statusMessage": "Container loaded on vessel, departed from Port of Shanghai",
            "createdAt": "2025-12-09T10:00:00Z",
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        return await self.normalize_response(mock_raw_data)
    
    async def update_shipment(
        self,
        identifier: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Push update to Logitude API
        MOCK: Simulates successful update
        """
        logger.info(f"[MOCK] Updating shipment {identifier} in Logitude: {update_data}")
        
        # In production, this would be:
        # response = await self._make_request(
        #     "PATCH",
        #     f"/shipments/{identifier}",
        #     json=update_data
        # )
        # return response.get("success", False)
        
        # MOCK: Always succeeds
        return True
