"""
Comprehensive Test Suite for Logistics MCP Orchestrator
Tests all endpoints, tools, SSE, and AI agent functionality
"""
import asyncio
import json
import httpx
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


BASE_URL = "http://localhost:8000"
HEADERS = {
    "Authorization": "Bearer dev-api-key-12345",
    "Content-Type": "application/json"
}


class TestResults:
    """Track test results"""
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_pass(self, name, details=""):
        self.tests.append({"name": name, "status": "PASS", "details": details})
        self.passed += 1
        logger.info(f"✅ PASS: {name}")
        if details:
            logger.info(f"   {details}")
    
    def add_fail(self, name, error):
        self.tests.append({"name": name, "status": "FAIL", "error": str(error)})
        self.failed += 1
        logger.error(f"❌ FAIL: {name}")
        logger.error(f"   Error: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        logger.info("\n" + "="*70)
        logger.info("TEST SUITE SUMMARY")
        logger.info("="*70)
        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {self.passed} ({100*self.passed/total if total>0 else 0:.1f}%)")
        logger.info(f"Failed: {self.failed}")
        logger.info("="*70)
        
        if self.failed == 0:
            logger.info("🎉 ALL TESTS PASSED!")
            return True
        else:
            logger.error(f"❌ {self.failed} TEST(S) FAILED")
            return False


async def test_health_endpoint(results: TestResults):
    """Test 1: Health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            if data.get("data", {}).get("status") != "healthy":
                raise Exception(f"Unexpected response: {data}")
            
            results.add_pass("Health Endpoint", f"Server is healthy")
    
    except Exception as e:
        results.add_fail("Health Endpoint", e)


async def test_info_endpoint(results: TestResults):
    """Test 2: Info endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/info", headers=HEADERS, timeout=5.0)
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            tools = data.get("data", {}).get("available_tools", [])
            
            expected_tools = ["track_shipment", "update_shipment_eta", "set_risk_flag", 
                            "add_agent_note", "search_shipments"]
            
            if not all(tool in tools for tool in expected_tools):
                raise Exception(f"Missing tools. Found: {tools}")
            
            results.add_pass("Info Endpoint", f"All 5 tools listed")
    
    except Exception as e:
        results.add_fail("Info Endpoint", e)


async def test_search_shipments_tool(results: TestResults):
    """Test 3: search_shipments tool"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "search_shipments",
                    "arguments": {"risk_flag": True, "limit": 5}
                },
                "id": 1
            }
            
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            result = data.get("result", {})
            
            if not result.get("success"):
                raise Exception(f"Tool call failed: {result}")
            
            count = result.get("count", 0)
            results_list = result.get("results", [])
            
            if count == 0 or len(results_list) == 0:
                raise Exception("No risky shipments found in database")
            
            results.add_pass("search_shipments Tool", f"Found {count} risky shipments")
    
    except Exception as e:
        results.add_fail("search_shipments Tool", e)


async def test_track_shipment_tool(results: TestResults):
    """Test 4: track_shipment tool"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "track_shipment",
                    "arguments": {"identifier": "JOB-2025-001", "source": "local"}
                },
                "id": 2
            }
            
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            result = data.get("result", {})
            
            if not result.get("success"):
                raise Exception(f"Tool call failed: {result}")
            
            shipment = result.get("shipment", {})
            if not shipment.get("id"):
                raise Exception(f"No shipment data returned")
            
            results.add_pass("track_shipment Tool", f"Retrieved {shipment.get('id')}")
    
    except Exception as e:
        results.add_fail("track_shipment Tool", e)


async def test_update_eta_tool(results: TestResults):
    """Test 5: update_shipment_eta tool"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_shipment_eta",
                    "arguments": {
                        "shipment_id": "JOB-2025-003",
                        "new_eta": "2025-12-30T15:00:00",
                        "reason": "Test update - port congestion delay"
                    }
                },
                "id": 3
            }
            
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            result = data.get("result", {})
            
            if not result.get("success"):
                raise Exception(f"Tool call failed: {result}")
            
            results.add_pass("update_shipment_eta Tool", 
                           f"Updated {result.get('shipment_id')} ETA")
    
    except Exception as e:
        results.add_fail("update_shipment_eta Tool", e)


async def test_set_risk_flag_tool(results: TestResults):
    """Test 6: set_risk_flag tool"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "set_risk_flag",
                    "arguments": {
                        "shipment_id": "JOB-2025-004",
                        "is_risk": True,
                        "reason": "Test: Potential customs delay detected"
                    }
                },
                "id": 4
            }
            
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            result = data.get("result", {})
            
            if not result.get("success"):
                raise Exception(f"Tool call failed: {result}")
            
            results.add_pass("set_risk_flag Tool", 
                           f"Set risk flag on {result.get('shipment_id')}")
    
    except Exception as e:
        results.add_fail("set_risk_flag Tool", e)


async def test_add_agent_note_tool(results: TestResults):
    """Test 7: add_agent_note tool"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "add_agent_note",
                    "arguments": {
                        "shipment_id": "JOB-2025-005",
                        "note": "Test note: AI agent monitoring - weather conditions normal"
                    }
                },
                "id": 5
            }
            
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Status code: {response.status_code}")
            
            data = response.json()
            result = data.get("result", {})
            
            if not result.get("success"):
                raise Exception(f"Tool call failed: {result}")
            
            results.add_pass("add_agent_note Tool", 
                           f"Added note to {result.get('shipment_id')}")
    
    except Exception as e:
        results.add_fail("add_agent_note Tool", e)


async def test_sse_connection(results: TestResults):
    """Test 8: SSE endpoint connection and events"""
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"{BASE_URL}/sse",
                headers=HEADERS,
                timeout=None
            ) as response:
                
                if response.status_code != 200:
                    raise Exception(f"Status code: {response.status_code}")
                
                # Read first few events (max 20 seconds)
                event_count = 0
                start_time = asyncio.get_event_loop().time()
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("event:"):
                        event_count += 1
                    
                    # Check if we received at least 2 events (init + tools list)
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if event_count >= 2 or elapsed > 20:
                        break
                
                if event_count < 2:
                    raise Exception(f"Only received {event_count} events, expected at least 2")
                
                results.add_pass("SSE Connection", f"Received {event_count} events successfully")
    
    except Exception as e:
        results.add_fail("SSE Connection", e)


async def test_standard_data_format(results: TestResults):
    """Test 9: Standard data format compliance"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "track_shipment",
                    "arguments": {"identifier": "JOB-2025-002"}
                },
                "id": 9
            }
            
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            
            data = response.json()
            shipment = data.get("result", {}).get("shipment", {})
            
            # Check required fields
            required = ["id", "tracking", "schedule", "status", "flags"]
            missing = [f for f in required if f not in shipment]
            
            if missing:
                raise Exception(f"Missing required fields: {missing}")
            
            # Check nested structure
            tracking = shipment.get("tracking", {})
            if "container" not in tracking or "vessel" not in tracking:
                raise Exception("tracking object missing required fields")
            
            schedule = shipment.get("schedule", {})
            if "eta" not in schedule or "etd" not in schedule:
                raise Exception("schedule object missing required fields")
            
            results.add_pass("Standard Data Format", "All required fields present")
    
    except Exception as e:
        results.add_fail("Standard Data Format", e)


async def test_authentication(results: TestResults):
    """Test 10: Authentication requirement"""
    try:
        async with httpx.AsyncClient() as client:
            # Try without auth header
            response = await client.get(f"{BASE_URL}/info", timeout=5.0)
            
            if response.status_code == 200:
                raise Exception("Authentication not enforced - request succeeded without API key")
            
            if response.status_code != 401 and response.status_code != 403:
                raise Exception(f"Expected 401/403, got {response.status_code}")
            
            results.add_pass("Authentication", "API key required as expected")
    
    except Exception as e:
        results.add_fail("Authentication", e)


async def main():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("🧪 LOGISTICS MCP ORCHESTRATOR - COMPREHENSIVE TEST SUITE")
    logger.info("="*70)
    logger.info(f"Target: {BASE_URL}")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70 + "\n")
    
    results = TestResults()
    
    # Run all tests
    logger.info("Running tests...\n")
    
    await test_health_endpoint(results)
    await asyncio.sleep(0.5)
    
    await test_info_endpoint(results)
    await asyncio.sleep(0.5)
    
    await test_authentication(results)
    await asyncio.sleep(0.5)
    
    await test_search_shipments_tool(results)
    await asyncio.sleep(0.5)
    
    await test_track_shipment_tool(results)
    await asyncio.sleep(0.5)
    
    await test_update_eta_tool(results)
    await asyncio.sleep(0.5)
    
    await test_set_risk_flag_tool(results)
    await asyncio.sleep(0.5)
    
    await test_add_agent_note_tool(results)
    await asyncio.sleep(0.5)
    
    await test_standard_data_format(results)
    await asyncio.sleep(0.5)
    
    await test_sse_connection(results)
    
    # Print summary
    logger.info("\n")
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
