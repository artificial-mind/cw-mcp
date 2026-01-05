"""
Vessel Tracking Adapter with Real API + Mock Fallback

Supports:
- VesselFinder API (real AIS data when API key provided)
- Mock data fallback (realistic simulation for testing/demo)
"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class VesselTrackingAdapter:
    """
    Vessel tracking with real API + mock fallback.
    
    Real API: VesselFinder (https://www.vesselfinder.com/api)
    Fallback: Realistic mock data for demo/testing
    """
    
    # VesselFinder API endpoints (if using real API)
    VESSELFINDER_BASE = "https://api.vesselfinder.com/vesselfinder"
    
    # Mock vessel database (realistic shipping routes)
    MOCK_VESSELS = {
        "MAERSK ESSEX": {
            "imo": "9632506",
            "mmsi": "219024000",
            "vessel_type": "Container Ship",
            "flag": "Denmark",
            "dwt": 200285,
            "year_built": 2015,
            "route": "Asia-Europe",
            "current_voyage": {
                "from_port": "Shanghai",
                "to_port": "Rotterdam",
                "departure": "2026-01-01T08:00:00Z",
                "eta": "2026-01-18T14:00:00Z"
            }
        },
        "MSC GULSUN": {
            "imo": "9839286",
            "mmsi": "636092430",
            "vessel_type": "Container Ship",
            "flag": "Liberia",
            "dwt": 232618,
            "year_built": 2019,
            "route": "Trans-Pacific",
            "current_voyage": {
                "from_port": "Los Angeles",
                "to_port": "Singapore",
                "departure": "2026-01-03T10:00:00Z",
                "eta": "2026-01-20T08:00:00Z"
            }
        },
        "COSCO SHIPPING UNIVERSE": {
            "imo": "9795432",
            "mmsi": "477005900",
            "vessel_type": "Container Ship",
            "flag": "Hong Kong",
            "dwt": 199988,
            "year_built": 2018,
            "route": "Asia-North America",
            "current_voyage": {
                "from_port": "Ningbo",
                "to_port": "Long Beach",
                "departure": "2026-01-02T06:00:00Z",
                "eta": "2026-01-16T18:00:00Z"
            }
        },
        "EVER GIVEN": {
            "imo": "9811000",
            "mmsi": "353136000",
            "vessel_type": "Container Ship",
            "flag": "Panama",
            "dwt": 199629,
            "year_built": 2018,
            "route": "Asia-Europe",
            "current_voyage": {
                "from_port": "Yantian",
                "to_port": "Felixstowe",
                "departure": "2026-01-04T12:00:00Z",
                "eta": "2026-01-25T10:00:00Z"
            }
        },
        "CMA CGM ANTOINE DE SAINT EXUPERY": {
            "imo": "9454436",
            "mmsi": "228339600",
            "vessel_type": "Container Ship",
            "flag": "France",
            "dwt": 154792,
            "year_built": 2018,
            "route": "Asia-Europe",
            "current_voyage": {
                "from_port": "Busan",
                "to_port": "Le Havre",
                "departure": "2026-01-03T14:00:00Z",
                "eta": "2026-01-22T16:00:00Z"
            }
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize vessel tracking adapter.
        
        Args:
            api_key: Optional VesselFinder API key. If not provided, uses mock data.
        """
        self.api_key = api_key
        self.use_real_api = bool(api_key)
        self.client = httpx.AsyncClient(timeout=10.0) if self.use_real_api else None
        
        if self.use_real_api:
            logger.info("🚢 VesselTracking: Using real VesselFinder API")
        else:
            logger.info("🚢 VesselTracking: Using mock data (no API key provided)")
    
    async def search_vessel(self, vessel_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for vessel by name.
        
        Args:
            vessel_name: Vessel name (e.g., "MAERSK ESSEX")
            
        Returns:
            Vessel metadata or None if not found
        """
        vessel_name_upper = vessel_name.upper().strip()
        
        if self.use_real_api:
            return await self._search_vessel_real(vessel_name_upper)
        else:
            return self._search_vessel_mock(vessel_name_upper)
    
    async def get_vessel_position(
        self, 
        vessel_name: Optional[str] = None,
        imo: Optional[str] = None,
        mmsi: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get current vessel position and navigation data.
        
        Args:
            vessel_name: Vessel name
            imo: IMO number (alternative to vessel_name)
            mmsi: MMSI number (alternative to vessel_name)
            
        Returns:
            Current position, speed, heading, status, ETA
        """
        if self.use_real_api:
            return await self._get_position_real(vessel_name, imo, mmsi)
        else:
            return self._get_position_mock(vessel_name, imo, mmsi)
    
    # ============== REAL API METHODS ==============
    
    async def _search_vessel_real(self, vessel_name: str) -> Optional[Dict[str, Any]]:
        """Search vessel using VesselFinder API"""
        try:
            url = f"{self.VESSELFINDER_BASE}/vessels"
            params = {
                "userkey": self.api_key,
                "name": vessel_name
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                vessel = data[0]
                return {
                    "imo": vessel.get("IMO"),
                    "mmsi": vessel.get("MMSI"),
                    "vessel_name": vessel.get("NAME"),
                    "vessel_type": vessel.get("TYPE"),
                    "flag": vessel.get("FLAG"),
                    "dwt": vessel.get("DWT"),
                    "year_built": vessel.get("YEAR")
                }
            return None
            
        except Exception as e:
            logger.error(f"VesselFinder API search error: {e}")
            logger.info("Falling back to mock data...")
            return self._search_vessel_mock(vessel_name)
    
    async def _get_position_real(
        self, 
        vessel_name: Optional[str],
        imo: Optional[str],
        mmsi: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Get position using VesselFinder API"""
        try:
            url = f"{self.VESSELFINDER_BASE}/vesselsonmap"
            params = {"userkey": self.api_key}
            
            if imo:
                params["imo"] = imo
            elif mmsi:
                params["mmsi"] = mmsi
            elif vessel_name:
                # First search to get IMO/MMSI
                vessel_info = await self._search_vessel_real(vessel_name)
                if vessel_info and vessel_info.get("imo"):
                    params["imo"] = vessel_info["imo"]
                else:
                    logger.warning(f"Could not find IMO for {vessel_name}")
                    return self._get_position_mock(vessel_name, imo, mmsi)
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                vessel = data[0]
                return {
                    "vessel_name": vessel.get("NAME"),
                    "imo": vessel.get("IMO"),
                    "mmsi": vessel.get("MMSI"),
                    "position": {
                        "lat": vessel.get("LAT"),
                        "lon": vessel.get("LON"),
                        "timestamp": vessel.get("TIMESTAMP")
                    },
                    "navigation": {
                        "speed": vessel.get("SPEED"),
                        "heading": vessel.get("COURSE"),
                        "status": vessel.get("NAVSTAT")
                    },
                    "destination": vessel.get("DESTINATION"),
                    "eta": vessel.get("ETA"),
                    "data_source": "VesselFinder API"
                }
            return None
            
        except Exception as e:
            logger.error(f"VesselFinder API position error: {e}")
            logger.info("Falling back to mock data...")
            return self._get_position_mock(vessel_name, imo, mmsi)
    
    # ============== MOCK DATA METHODS ==============
    
    def _search_vessel_mock(self, vessel_name: str) -> Optional[Dict[str, Any]]:
        """Search vessel in mock database"""
        vessel = self.MOCK_VESSELS.get(vessel_name)
        if vessel:
            return {
                "imo": vessel["imo"],
                "mmsi": vessel["mmsi"],
                "vessel_name": vessel_name,
                "vessel_type": vessel["vessel_type"],
                "flag": vessel["flag"],
                "dwt": vessel["dwt"],
                "year_built": vessel["year_built"],
                "data_source": "Mock Data"
            }
        
        # If not in database, check partial matches
        for name, data in self.MOCK_VESSELS.items():
            if vessel_name in name or name in vessel_name:
                return {
                    "imo": data["imo"],
                    "mmsi": data["mmsi"],
                    "vessel_name": name,
                    "vessel_type": data["vessel_type"],
                    "flag": data["flag"],
                    "dwt": data["dwt"],
                    "year_built": data["year_built"],
                    "data_source": "Mock Data"
                }
        
        return None
    
    def _get_position_mock(
        self,
        vessel_name: Optional[str],
        imo: Optional[str],
        mmsi: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Get simulated position from mock database"""
        # Find vessel by name, IMO, or MMSI
        vessel_data = None
        vessel_key = None
        
        if vessel_name:
            vessel_name_upper = vessel_name.upper().strip()
            vessel_data = self.MOCK_VESSELS.get(vessel_name_upper)
            vessel_key = vessel_name_upper
            
            # Try partial match
            if not vessel_data:
                for name, data in self.MOCK_VESSELS.items():
                    if vessel_name_upper in name or name in vessel_name_upper:
                        vessel_data = data
                        vessel_key = name
                        break
        
        elif imo:
            for name, data in self.MOCK_VESSELS.items():
                if data["imo"] == imo:
                    vessel_data = data
                    vessel_key = name
                    break
        
        elif mmsi:
            mmsi_str = str(mmsi)
            for name, data in self.MOCK_VESSELS.items():
                if data["mmsi"] == mmsi_str:
                    vessel_data = data
                    vessel_key = name
                    break
        
        if not vessel_data:
            return None
        
        # Calculate simulated position based on route progress
        position = self._simulate_position(vessel_data)
        
        return {
            "vessel_name": vessel_key,
            "imo": vessel_data["imo"],
            "mmsi": vessel_data["mmsi"],
            "vessel_type": vessel_data["vessel_type"],
            "flag": vessel_data["flag"],
            "position": position["position"],
            "navigation": position["navigation"],
            "destination": vessel_data["current_voyage"]["to_port"],
            "eta": vessel_data["current_voyage"]["eta"],
            "voyage_progress": position["progress"],
            "data_source": "Mock Data (Simulated)"
        }
    
    def _simulate_position(self, vessel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate realistic vessel position based on route and time.
        Uses simple linear interpolation for demo purposes.
        """
        voyage = vessel_data["current_voyage"]
        route = vessel_data["route"]
        
        # Define route coordinates (major shipping routes)
        ROUTES = {
            "Asia-Europe": {
                "start": {"lat": 31.2, "lon": 121.5},  # Shanghai
                "end": {"lat": 51.9, "lon": 4.5}        # Rotterdam
            },
            "Trans-Pacific": {
                "start": {"lat": 33.7, "lon": -118.2},  # Los Angeles
                "end": {"lat": 1.3, "lon": 103.9}       # Singapore
            },
            "Asia-North America": {
                "start": {"lat": 29.9, "lon": 121.6},  # Ningbo
                "end": {"lat": 33.7, "lon": -118.2}     # Long Beach
            }
        }
        
        route_coords = ROUTES.get(route, ROUTES["Asia-Europe"])
        
        # Calculate voyage progress (0.0 to 1.0)
        try:
            departure_time = datetime.fromisoformat(voyage["departure"].replace('Z', '+00:00'))
            eta_time = datetime.fromisoformat(voyage["eta"].replace('Z', '+00:00'))
            current_time = datetime.now(departure_time.tzinfo)
            
            total_duration = (eta_time - departure_time).total_seconds()
            elapsed = (current_time - departure_time).total_seconds()
            progress = min(max(elapsed / total_duration, 0.0), 1.0)
        except:
            progress = 0.5  # Default to midpoint
        
        # Interpolate position
        lat = route_coords["start"]["lat"] + (route_coords["end"]["lat"] - route_coords["start"]["lat"]) * progress
        lon = route_coords["start"]["lon"] + (route_coords["end"]["lon"] - route_coords["start"]["lon"]) * progress
        
        # Add small random variation for realism
        lat += random.uniform(-0.5, 0.5)
        lon += random.uniform(-0.5, 0.5)
        
        # Calculate heading (approximate)
        d_lat = route_coords["end"]["lat"] - route_coords["start"]["lat"]
        d_lon = route_coords["end"]["lon"] - route_coords["start"]["lon"]
        import math
        heading = int((math.atan2(d_lon, d_lat) * 180 / math.pi) % 360)
        
        # Typical container ship speeds
        speed = round(random.uniform(18.0, 22.0), 1)  # knots
        
        return {
            "position": {
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "navigation": {
                "speed": speed,
                "heading": heading,
                "status": "Under way using engine"
            },
            "progress": f"{int(progress * 100)}%"
        }
    
    async def close(self):
        """Close HTTP client if using real API"""
        if self.client:
            await self.client.aclose()
