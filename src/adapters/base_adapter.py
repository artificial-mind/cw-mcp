"""
Base adapter class for external logistics APIs
All adapters must inherit from this and implement the normalize_response method
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class BaseLogisticsAdapter(ABC):
    """
    Abstract base class for logistics API adapters
    Handles dirty work of calling external APIs and normalizing messy JSON
    """
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=self._get_headers(),
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Logistics-MCP-Orchestrator/1.0"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        Raises exception if all retries fail
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        last_exception = None
        
        for attempt in range(settings.MAX_RETRIES):
            try:
                response = await self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error on attempt {attempt + 1}/{settings.MAX_RETRIES}: "
                    f"{e.response.status_code} - {e.response.text}"
                )
                last_exception = e
                
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise
            
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning(
                    f"Connection error on attempt {attempt + 1}/{settings.MAX_RETRIES}: {e}"
                )
                last_exception = e
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_exception = e
                raise
            
            # Wait before retry (except on last attempt)
            if attempt < settings.MAX_RETRIES - 1:
                import asyncio
                await asyncio.sleep(settings.RETRY_DELAY * (attempt + 1))
        
        # All retries failed
        raise Exception(
            f"External API unavailable after {settings.MAX_RETRIES} attempts. "
            f"Last error: {last_exception}"
        )
    
    @abstractmethod
    async def normalize_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert vendor-specific JSON to our standard format
        Must be implemented by each adapter
        
        Returns:
            Dictionary in standard format matching Shipment.to_standard_format()
        """
        pass
    
    @abstractmethod
    async def fetch_shipment(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch shipment data from external API
        Returns normalized data in standard format
        """
        pass
    
    @abstractmethod
    async def update_shipment(
        self,
        identifier: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Push update to external API
        Returns True if successful, False otherwise
        """
        pass


class AdapterError(Exception):
    """Custom exception for adapter errors"""
    
    def __init__(self, message: str, vendor: str, original_error: Optional[Exception] = None):
        self.message = message
        self.vendor = vendor
        self.original_error = original_error
        super().__init__(self.message)
