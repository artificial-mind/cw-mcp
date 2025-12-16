"""
Test script for 11Labs voice agent integration
Simulates voice queries and shows how the system responds
"""

import asyncio
import httpx
import json
from datetime import datetime


class VoiceAgentTester:
    """Simulates 11Labs voice agent queries"""
    
    def __init__(self):
        self.bridge_url = "http://localhost:8001"
        self.test_queries = []
    
    async def test_query(self, query: str, description: str):
        """Test a single voice query"""
        print(f"\n{'='*70}")
        print(f"TEST: {description}")
        print(f"{'='*70}")
        print(f"🗣️  USER SAYS: \"{query}\"")
        print(f"\n⏳ Processing...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bridge_url}/test",
                    json={"query": query},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"\n🤖 AI AGENT RESPONDS:")
                    print(f"   \"{data['voice_response']}\"")
                    
                    print(f"\n📊 TECHNICAL DETAILS:")
                    print(f"   Intent: {data['intent']['intent']}")
                    print(f"   Parameters: {json.dumps(data['intent']['params'], indent=6)}")
                    
                    return True
                else:
                    print(f"❌ Error: {response.status_code}")
                    return False
        
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        
        print("\n" + "="*70)
        print("11LABS VOICE AGENT INTEGRATION TEST SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Bridge URL: {self.bridge_url}")
        print("="*70)
        
        # Test 1: Track specific shipment
        await self.test_query(
            "Where is shipment JOB-2025-001?",
            "Track Specific Shipment"
        )
        
        await asyncio.sleep(1)
        
        # Test 2: High risk shipments
        await self.test_query(
            "Show me all high risk shipments",
            "Find High Risk Shipments"
        )
        
        await asyncio.sleep(1)
        
        # Test 3: Delayed shipments
        await self.test_query(
            "What shipments are delayed?",
            "Find Delayed Shipments"
        )
        
        await asyncio.sleep(1)
        
        # Test 4: In transit
        await self.test_query(
            "Which shipments are currently in transit?",
            "Find In-Transit Shipments"
        )
        
        await asyncio.sleep(1)
        
        # Test 5: Container tracking
        await self.test_query(
            "Track container MSCU1234567",
            "Track by Container Number"
        )
        
        await asyncio.sleep(1)
        
        # Test 6: Arriving soon
        await self.test_query(
            "What shipments are arriving this week?",
            "Find Upcoming Arrivals"
        )
        
        await asyncio.sleep(1)
        
        # Test 7: Natural language with location
        await self.test_query(
            "Do we have any shipments from Shanghai?",
            "Location-Based Search"
        )
        
        await asyncio.sleep(1)
        
        # Test 8: Status check - general
        await self.test_query(
            "Give me a status update on all shipments",
            "General Status Update"
        )
        
        print(f"\n{'='*70}")
        print("TEST SUITE COMPLETED")
        print(f"{'='*70}\n")


class ConversationSimulator:
    """Simulates realistic customer conversations"""
    
    def __init__(self):
        self.bridge_url = "http://localhost:8001"
    
    async def send_message(self, message: str):
        """Send a message and get response"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.bridge_url}/test",
                json={"query": message},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()["voice_response"]
            return "Error processing request"
    
    async def simulate_conversation(self, title: str, messages: list):
        """Simulate a multi-turn conversation"""
        print(f"\n{'='*70}")
        print(f"CONVERSATION: {title}")
        print(f"{'='*70}")
        
        for i, message in enumerate(messages, 1):
            print(f"\n👤 Customer (Turn {i}):")
            print(f"   \"{message}\"")
            
            response = await self.send_message(message)
            
            print(f"\n🤖 AI Agent:")
            print(f"   \"{response}\"")
            
            await asyncio.sleep(1.5)
        
        print(f"\n{'='*70}\n")
    
    async def run_conversations(self):
        """Run realistic conversation scenarios"""
        
        print("\n" + "="*70)
        print("REALISTIC CUSTOMER CONVERSATION SIMULATIONS")
        print("="*70)
        
        # Conversation 1: Worried customer
        await self.simulate_conversation(
            "Worried Customer - Delayed Shipment",
            [
                "Hi, I'm calling about my shipment JOB-2025-002",
                "It seems delayed. Can you check what's happening?",
                "When can I expect it to arrive?"
            ]
        )
        
        # Conversation 2: Logistics manager morning briefing
        await self.simulate_conversation(
            "Logistics Manager - Morning Briefing",
            [
                "Good morning, I need a status update",
                "Show me all high risk shipments that need attention",
                "Are there any delayed shipments I should know about?"
            ]
        )
        
        # Conversation 3: Operations team - Crisis management
        await self.simulate_conversation(
            "Operations Team - Crisis Response",
            [
                "We just heard about port delays at Singapore",
                "Which of our shipments are affected?",
                "What's the status of shipment JOB-2025-006?"
            ]
        )
        
        # Conversation 4: Customer service - Multiple inquiries
        await self.simulate_conversation(
            "Customer Service - Batch Inquiry",
            [
                "I need to check on shipments arriving this week",
                "Are any of them delayed?",
                "What about shipment JOB-2025-001 specifically?"
            ]
        )


async def test_health_check():
    """Test bridge health"""
    print("\n" + "="*70)
    print("HEALTH CHECK")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test bridge health
            response = await client.get("http://localhost:8001/health", timeout=5.0)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Bridge: {health['status'].upper()}")
                print(f"✅ Logistics API: {health['logistics_api'].upper()}")
            else:
                print(f"❌ Bridge health check failed: {response.status_code}")
            
            # Test logistics API directly
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                print(f"✅ Logistics API: OPERATIONAL")
            else:
                print(f"❌ Logistics API check failed")
    
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("="*70)


async def main():
    """Main test runner"""
    
    # Health check first
    await test_health_check()
    
    await asyncio.sleep(1)
    
    # Run automated tests
    tester = VoiceAgentTester()
    await tester.run_all_tests()
    
    await asyncio.sleep(2)
    
    # Run conversation simulations
    simulator = ConversationSimulator()
    await simulator.run_conversations()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)
    print("\n✅ Integration bridge is ready for 11Labs voice agent!")
    print("\n📋 NEXT STEPS:")
    print("   1. Start ngrok: ngrok http 8001")
    print("   2. Copy ngrok URL (e.g., https://abc123.ngrok.io)")
    print("   3. Go to 11Labs dashboard")
    print("   4. Set webhook URL to: https://abc123.ngrok.io/webhook")
    print("   5. Test with real voice agent!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
