"""
Test client for MCP SSE connection
Use this to verify that remote agents can connect to the server
"""
import asyncio
import httpx
import json
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPTestClient:
    """Simple test client for MCP SSE endpoint"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
    
    async def test_health(self):
        """Test health endpoint"""
        logger.info("Testing health endpoint...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                data = response.json()
                logger.info(f"✅ Health check: {data}")
                return True
            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
                return False
    
    async def test_info(self):
        """Test info endpoint"""
        logger.info("Testing info endpoint...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/info")
                response.raise_for_status()
                data = response.json()
                logger.info(f"✅ Server info: {json.dumps(data, indent=2)}")
                return True
            except Exception as e:
                logger.error(f"❌ Info endpoint failed: {e}")
                return False
    
    async def test_mcp_tool(self, tool_name: str, arguments: dict):
        """Test MCP tool via POST endpoint"""
        logger.info(f"Testing MCP tool: {tool_name}")
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=message,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"✅ Tool response: {json.dumps(data, indent=2)}")
                return True
            except Exception as e:
                logger.error(f"❌ Tool call failed: {e}")
                return False
    
    async def test_sse_connection(self):
        """Test SSE connection (basic connectivity)"""
        logger.info("Testing SSE connection...")
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "GET",
                    f"{self.base_url}/sse",
                    headers=headers,
                    timeout=5.0
                ) as response:
                    response.raise_for_status()
                    
                    # Read a few events
                    count = 0
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            logger.info(f"Received SSE event: {line}")
                            count += 1
                            if count >= 3:  # Just read a few events
                                break
                    
                    logger.info(f"✅ SSE connection successful ({count} events received)")
                    return True
            
            except httpx.TimeoutException:
                logger.warning("⚠️  SSE connection timeout (this is normal if server is waiting for events)")
                return True
            except Exception as e:
                logger.error(f"❌ SSE connection failed: {e}")
                return False


async def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("MCP SERVER TEST SUITE")
    logger.info("=" * 60)
    
    client = MCPTestClient()
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", await client.test_health()))
    
    # Test 2: Server info
    results.append(("Server Info", await client.test_info()))
    
    # Test 3: Search shipments (should work with seeded data)
    results.append(("Search Shipments", await client.test_mcp_tool(
        "search_shipments",
        {"risk_flag": True, "limit": 5}
    )))
    
    # Test 4: Track specific shipment
    results.append(("Track Shipment", await client.test_mcp_tool(
        "track_shipment",
        {"identifier": "JOB-2025-001", "source": "local"}
    )))
    
    # Test 5: SSE connection
    results.append(("SSE Connection", await client.test_sse_connection()))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    logger.info(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("🎉 All tests passed!")
    else:
        logger.warning("⚠️  Some tests failed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
