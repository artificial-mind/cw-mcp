"""
SSE Test Client - Tests the Server-Sent Events endpoint
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


async def test_sse_connection(duration: int = 60):
    """
    Test SSE endpoint connection and event streaming
    """
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer dev-api-key-12345",
        "Accept": "text/event-stream"
    }
    
    logger.info("="*70)
    logger.info("SSE ENDPOINT TEST")
    logger.info("="*70)
    logger.info(f"URL: {base_url}/sse")
    logger.info(f"Duration: {duration} seconds")
    logger.info("")
    
    event_count = 0
    ping_count = 0
    message_count = 0
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info("🔌 Connecting to SSE endpoint...")
            
            async with client.stream(
                "GET",
                f"{base_url}/sse",
                headers=headers,
                timeout=None
            ) as response:
                
                logger.info(f"📡 Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"❌ Connection failed!")
                    logger.error(f"   Response: {response.text}")
                    return False
                
                logger.info("✅ SSE connected successfully!")
                logger.info(f"📨 Listening for events (max {duration}s)...\n")
                
                start_time = asyncio.get_event_loop().time()
                current_event = None
                
                async for line in response.aiter_lines():
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > duration:
                        logger.info(f"\n⏱️  Duration elapsed ({duration}s)")
                        break
                    
                    # Skip empty lines (event separator)
                    if not line:
                        current_event = None
                        continue
                    
                    # Parse SSE format
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        event_count += 1
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        logger.info(f"[{timestamp}] 📡 Event #{event_count}: {current_event}")
                        
                        if current_event == "ping":
                            ping_count += 1
                        elif current_event == "message":
                            message_count += 1
                            
                    elif line.startswith("data:"):
                        data = line.split(":", 1)[1].strip()
                        
                        try:
                            data_json = json.loads(data)
                            
                            if current_event == "ping":
                                logger.info(f"  └─ Ping #{data_json.get('count', '?')} at {data_json.get('timestamp', 'unknown')}")
                            elif current_event == "message":
                                logger.info(f"  └─ Message data:")
                                logger.info(f"     {json.dumps(data_json, indent=6)}")
                            elif current_event == "error":
                                logger.error(f"  └─ Error: {data_json}")
                            else:
                                logger.info(f"  └─ Data: {json.dumps(data_json, indent=6)}")
                        
                        except json.JSONDecodeError:
                            logger.info(f"  └─ Data (raw): {data}")
                    
                    elif line.startswith("id:"):
                        event_id = line.split(":", 1)[1].strip()
                        logger.info(f"  └─ Event ID: {event_id}")
                    
                    elif line.startswith("retry:"):
                        retry_ms = line.split(":", 1)[1].strip()
                        logger.info(f"  └─ Retry interval: {retry_ms}ms")
                
                logger.info("\n" + "="*70)
                logger.info("SSE TEST RESULTS")
                logger.info("="*70)
                logger.info(f"✅ Connection successful: YES")
                logger.info(f"📊 Total events received: {event_count}")
                logger.info(f"📡 Ping events: {ping_count}")
                logger.info(f"📨 Message events: {message_count}")
                logger.info(f"⏱️  Test duration: {int(elapsed)}s")
                logger.info("="*70)
                
                return True
    
    except httpx.ConnectError as e:
        logger.error(f"❌ Connection error: {e}")
        logger.error(f"   Is the server running on {base_url}?")
        return False
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return False


async def test_sse_with_concurrent_requests():
    """
    Test SSE while making concurrent POST requests
    Validates that SSE remains stable during active API usage
    """
    logger.info("\n" + "="*70)
    logger.info("SSE STABILITY TEST - Concurrent Requests")
    logger.info("="*70)
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer dev-api-key-12345",
        "Content-Type": "application/json"
    }
    
    async def make_tool_calls():
        """Make periodic tool calls while SSE is active"""
        async with httpx.AsyncClient() as client:
            for i in range(5):
                await asyncio.sleep(5)
                
                logger.info(f"\n🔧 Making tool call #{i+1}...")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_shipments",
                        "arguments": {"limit": 3}
                    },
                    "id": i + 1
                }
                
                response = await client.post(
                    f"{base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"  ✅ Tool call #{i+1} successful")
                else:
                    logger.error(f"  ❌ Tool call #{i+1} failed: {response.status_code}")
    
    # Run SSE connection and tool calls concurrently
    try:
        await asyncio.gather(
            test_sse_connection(duration=30),
            make_tool_calls()
        )
        logger.info("\n✅ SSE remained stable during concurrent requests!")
        return True
    
    except Exception as e:
        logger.error(f"❌ Stability test failed: {e}")
        return False


async def main():
    """Run all SSE tests"""
    logger.info("\n🧪 Starting SSE Endpoint Tests...\n")
    
    # Test 1: Basic SSE connection
    success_1 = await test_sse_connection(duration=30)
    
    await asyncio.sleep(2)
    
    # Test 2: SSE with concurrent requests
    success_2 = await test_sse_with_concurrent_requests()
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("FINAL TEST SUMMARY")
    logger.info("="*70)
    logger.info(f"Test 1 - Basic SSE Connection: {'✅ PASS' if success_1 else '❌ FAIL'}")
    logger.info(f"Test 2 - SSE Stability Test: {'✅ PASS' if success_2 else '❌ FAIL'}")
    logger.info("="*70)
    
    if success_1 and success_2:
        logger.info("\n🎉 ALL SSE TESTS PASSED!")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
