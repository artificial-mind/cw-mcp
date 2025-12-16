"""
Real-Time Logistics Operations Demo
Simulates realistic queries and operations that would happen in production
"""
import asyncio
import json
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

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


class LogisticsOperationsDemo:
    """Simulate real-time logistics operations"""
    
    def __init__(self):
        self.request_id = 0
    
    def _next_id(self):
        self.request_id += 1
        return self.request_id
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Call a tool and return result"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self._next_id()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/messages",
                json=payload,
                headers=HEADERS,
                timeout=10.0
            )
            return response.json()


async def scenario_morning_briefing(ops: LogisticsOperationsDemo):
    """
    Scenario 1: Morning Operations Briefing
    Operations manager starts the day checking critical shipments
    """
    logger.info("\n" + "="*70)
    logger.info("📅 SCENARIO 1: MORNING OPERATIONS BRIEFING")
    logger.info("="*70)
    logger.info("Time: 8:00 AM - Operations Manager Login")
    logger.info("")
    
    # Query 1: Check all high-risk shipments
    logger.info("🔍 Query 1: 'Show me all high-risk shipments'")
    result = await ops.call_tool("search_shipments", {
        "risk_flag": True,
        "limit": 10
    })
    
    risky = result.get("result", {}).get("results", [])
    logger.info(f"   Found {len(risky)} high-risk shipments:")
    for ship in risky:
        logger.info(f"   ⚠️  {ship['id']} - {ship['tracking']['vessel']}")
        logger.info(f"      Status: {ship['status']['code']} | ETA: {ship['schedule']['eta']}")
        logger.info(f"      Risk: {ship['flags']['agent_notes'][:60]}...")
    
    await asyncio.sleep(2)
    
    # Query 2: Check delayed shipments
    logger.info("\n🔍 Query 2: 'How many shipments are delayed?'")
    result = await ops.call_tool("search_shipments", {
        "status": "DELAYED",
        "limit": 10
    })
    
    delayed = result.get("result", {}).get("results", [])
    logger.info(f"   Found {len(delayed)} delayed shipments")
    
    await asyncio.sleep(2)
    
    # Query 3: Get specific container details
    logger.info("\n🔍 Query 3: 'Track container COSU9876543'")
    result = await ops.call_tool("search_shipments", {
        "container_no": "COSU9876543",
        "limit": 1
    })
    
    container = result.get("result", {}).get("results", [])
    if container:
        c = container[0]
        logger.info(f"   Container: {c['tracking']['container']}")
        logger.info(f"   Vessel: {c['tracking']['vessel']}")
        logger.info(f"   Current Location: {c['tracking']['location']['name']}")
        logger.info(f"   ETA: {c['schedule']['eta']}")
    
    logger.info("\n✅ Morning briefing complete!")


async def scenario_customer_emergency(ops: LogisticsOperationsDemo):
    """
    Scenario 2: Customer Emergency Call
    Customer calls about urgent shipment - need immediate status
    """
    logger.info("\n" + "="*70)
    logger.info("☎️  SCENARIO 2: CUSTOMER EMERGENCY CALL")
    logger.info("="*70)
    logger.info("Time: 10:30 AM - Customer Service Hotline")
    logger.info("Customer: 'Where is my shipment JOB-2025-002? It should have arrived!'")
    logger.info("")
    
    # Query: Track specific shipment
    logger.info("🔍 Agent Query: 'Track JOB-2025-002'")
    result = await ops.call_tool("track_shipment", {
        "identifier": "JOB-2025-002",
        "source": "local"
    })
    
    shipment = result.get("result", {}).get("shipment", {})
    if shipment:
        logger.info(f"\n📦 Shipment Details:")
        logger.info(f"   ID: {shipment['id']}")
        logger.info(f"   Status: {shipment['status']['code']}")
        logger.info(f"   Current Location: {shipment['tracking']['location']['name']}")
        logger.info(f"   Original ETA: {shipment['schedule']['eta']}")
        logger.info(f"   Vessel: {shipment['tracking']['vessel']}")
        
        if shipment['flags']['is_risk']:
            logger.info(f"\n   ⚠️  HIGH RISK STATUS")
            logger.info(f"   Reason: {shipment['flags']['agent_notes']}")
    
    await asyncio.sleep(2)
    
    # Action: Update customer with new ETA
    new_eta = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%S")
    logger.info(f"\n✏️  Agent Action: 'Update ETA to {new_eta}'")
    result = await ops.call_tool("update_shipment_eta", {
        "shipment_id": "JOB-2025-002",
        "new_eta": new_eta,
        "reason": "Suez Canal congestion - vessel delayed by severe weather conditions"
    })
    
    if result.get("result", {}).get("success"):
        logger.info(f"   ✅ ETA updated successfully")
        logger.info(f"   New ETA: {result['result']['new_eta']}")
    
    await asyncio.sleep(2)
    
    # Add note about customer interaction
    logger.info(f"\n📝 Agent Action: 'Add note about customer call'")
    await ops.call_tool("add_agent_note", {
        "shipment_id": "JOB-2025-002",
        "note": "Customer called at 10:30 AM very concerned about delay. "
               "Explained situation with Suez Canal congestion. "
               "Customer accepted new ETA. Promised to send email confirmation."
    })
    logger.info(f"   ✅ Note added to shipment record")
    
    logger.info("\n✅ Customer emergency handled!")


async def scenario_proactive_monitoring(ops: LogisticsOperationsDemo):
    """
    Scenario 3: AI Agent Proactive Monitoring
    AI continuously monitors shipments and flags issues
    """
    logger.info("\n" + "="*70)
    logger.info("🤖 SCENARIO 3: AI AGENT PROACTIVE MONITORING")
    logger.info("="*70)
    logger.info("Time: 2:00 PM - AI Agent Automated Scan")
    logger.info("")
    
    # AI scans all shipments
    logger.info("🔍 AI Query: 'Scan all shipments for potential issues'")
    result = await ops.call_tool("search_shipments", {
        "limit": 10
    })
    
    all_shipments = result.get("result", {}).get("results", [])
    logger.info(f"   Scanning {len(all_shipments)} active shipments...")
    
    await asyncio.sleep(1)
    
    # AI identifies a potential issue
    logger.info("\n🚨 AI ALERT: Detected potential customs delay")
    logger.info("   Shipment: JOB-2025-009")
    logger.info("   Reason: Container at customs hold for 2+ days")
    logger.info("   Recommendation: Flag as high-risk and notify ops team")
    
    await asyncio.sleep(2)
    
    # AI takes action
    logger.info("\n⚡ AI Action 1: Setting risk flag")
    result = await ops.call_tool("set_risk_flag", {
        "shipment_id": "JOB-2025-009",
        "is_risk": True,
        "reason": "AI DETECTED: Customs hold exceeding normal timeframe. "
                 "Missing commercial invoice may cause significant delay. "
                 "Recommend immediate intervention from customs broker."
    })
    
    if result.get("result", {}).get("success"):
        logger.info(f"   ✅ Risk flag set")
    
    await asyncio.sleep(1)
    
    logger.info("\n⚡ AI Action 2: Adding detailed analysis")
    await ops.call_tool("add_agent_note", {
        "shipment_id": "JOB-2025-009",
        "note": "AI ANALYSIS [2:00 PM]: Predictive model indicates 85% probability "
               "of delay exceeding 5 days if not resolved within 24 hours. "
               "Similar cases historically required customs broker intervention. "
               "Recommended action: Contact broker immediately. "
               "Alternative: Reroute to alternate port if documentation cannot be resolved."
    })
    logger.info(f"   ✅ Analysis added to shipment")
    
    logger.info("\n✅ AI monitoring cycle complete!")


async def scenario_bulk_status_check(ops: LogisticsOperationsDemo):
    """
    Scenario 4: Weekly Status Report
    Management requests status of all shipments by status
    """
    logger.info("\n" + "="*70)
    logger.info("📊 SCENARIO 4: WEEKLY STATUS REPORT")
    logger.info("="*70)
    logger.info("Time: 4:00 PM - Weekly Management Review")
    logger.info("")
    
    # Get all shipments
    logger.info("🔍 Query: 'Generate status report for all active shipments'")
    result = await ops.call_tool("search_shipments", {
        "limit": 20
    })
    
    all_shipments = result.get("result", {}).get("results", [])
    
    # Analyze by status
    status_counts = {}
    risk_count = 0
    
    for ship in all_shipments:
        status = ship['status']['code']
        status_counts[status] = status_counts.get(status, 0) + 1
        if ship['flags']['is_risk']:
            risk_count += 1
    
    logger.info(f"\n📈 SHIPMENT STATUS BREAKDOWN:")
    logger.info(f"   Total Active Shipments: {len(all_shipments)}")
    for status, count in status_counts.items():
        logger.info(f"   {status}: {count}")
    logger.info(f"   High-Risk Shipments: {risk_count}")
    
    await asyncio.sleep(2)
    
    # Identify top concerns
    logger.info(f"\n⚠️  TOP CONCERNS:")
    risky = [s for s in all_shipments if s['flags']['is_risk']]
    for i, ship in enumerate(risky[:3], 1):
        logger.info(f"   {i}. {ship['id']} - {ship['status']['code']}")
        logger.info(f"      Location: {ship['tracking']['location']['name']}")
        logger.info(f"      Issue: {ship['flags']['agent_notes'][:70]}...")
    
    logger.info("\n✅ Status report complete!")


async def scenario_realtime_tracking(ops: LogisticsOperationsDemo):
    """
    Scenario 5: Real-Time Container Tracking
    Customer portal queries for live container position
    """
    logger.info("\n" + "="*70)
    logger.info("🗺️  SCENARIO 5: REAL-TIME CONTAINER TRACKING")
    logger.info("="*70)
    logger.info("Time: 5:30 PM - Customer Portal Query")
    logger.info("Customer tracking container on web portal")
    logger.info("")
    
    # Track by container number
    container_no = "MSCU1234567"
    logger.info(f"🔍 Customer Query: 'Where is container {container_no}?'")
    result = await ops.call_tool("search_shipments", {
        "container_no": container_no,
        "limit": 1
    })
    
    containers = result.get("result", {}).get("results", [])
    if containers:
        ship = containers[0]
        logger.info(f"\n📍 LIVE TRACKING INFORMATION:")
        logger.info(f"   Container: {ship['tracking']['container']}")
        logger.info(f"   Vessel: {ship['tracking']['vessel']}")
        logger.info(f"   Voyage: {ship['tracking']['voyage']}")
        logger.info(f"   ")
        logger.info(f"   🌍 Current Position:")
        logger.info(f"      Location: {ship['tracking']['location']['name']}")
        logger.info(f"      Coordinates: {ship['tracking']['location']['lat']}, {ship['tracking']['location']['lng']}")
        logger.info(f"   ")
        logger.info(f"   📅 Schedule:")
        logger.info(f"      Departed: {ship['schedule']['etd']}")
        logger.info(f"      Estimated Arrival: {ship['schedule']['eta']}")
        logger.info(f"   ")
        logger.info(f"   📊 Status: {ship['status']['code']}")
        logger.info(f"      {ship['status']['description']}")
        
        if ship['flags']['is_risk']:
            logger.info(f"   ")
            logger.info(f"   ⚠️  ALERT: This shipment is flagged as high-risk")
            logger.info(f"      {ship['flags']['agent_notes']}")
    else:
        logger.info(f"   ❌ Container {container_no} not found")
    
    logger.info("\n✅ Real-time tracking query complete!")


async def scenario_crisis_management(ops: LogisticsOperationsDemo):
    """
    Scenario 6: Crisis Management - Port Strike
    Urgent situation requiring immediate action on multiple shipments
    """
    logger.info("\n" + "="*70)
    logger.info("🚨 SCENARIO 6: CRISIS MANAGEMENT - PORT STRIKE")
    logger.info("="*70)
    logger.info("Time: 7:00 PM - URGENT ALERT")
    logger.info("NEWS: Major port strike announced at Port of Singapore")
    logger.info("All operations halted for 48-72 hours")
    logger.info("")
    
    # Find all affected shipments
    logger.info("🔍 Emergency Query: 'Find all shipments going to Port of Singapore'")
    result = await ops.call_tool("search_shipments", {
        "limit": 20
    })
    
    all_shipments = result.get("result", {}).get("results", [])
    affected = [s for s in all_shipments if "Singapore" in s['tracking']['location']['name']]
    
    logger.info(f"   🚨 FOUND {len(affected)} AFFECTED SHIPMENTS")
    
    await asyncio.sleep(2)
    
    # Take action on each affected shipment
    for ship in affected:
        logger.info(f"\n⚡ Processing: {ship['id']}")
        logger.info(f"   Vessel: {ship['tracking']['vessel']}")
        
        # Flag as high risk
        logger.info(f"   → Setting high-risk flag...")
        await ops.call_tool("set_risk_flag", {
            "shipment_id": ship['id'],
            "is_risk": True,
            "reason": "CRISIS: Port strike at Singapore. All operations suspended 48-72 hours. "
                     "Vessel may be diverted to alternate port or experience significant delay."
        })
        
        await asyncio.sleep(0.5)
        
        # Update ETA
        new_eta = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
        logger.info(f"   → Updating ETA to +5 days...")
        await ops.call_tool("update_shipment_eta", {
            "shipment_id": ship['id'],
            "new_eta": new_eta,
            "reason": "Port strike at Singapore causing significant delays"
        })
        
        await asyncio.sleep(0.5)
        
        # Add detailed note
        logger.info(f"   → Adding crisis management note...")
        await ops.call_tool("add_agent_note", {
            "shipment_id": ship['id'],
            "note": f"CRISIS RESPONSE [{datetime.now().strftime('%H:%M')}]: "
                   f"Port strike identified. Customer notification sent. "
                   f"Monitoring for alternative routing options. "
                   f"Escalated to senior management for decision on diversion."
        })
        
        logger.info(f"   ✅ {ship['id']} processed")
    
    logger.info(f"\n🚨 CRISIS RESPONSE COMPLETE")
    logger.info(f"   {len(affected)} shipments flagged and updated")
    logger.info(f"   Customer notifications queued")
    logger.info(f"   Management briefing prepared")
    
    logger.info("\n✅ Crisis management protocol executed!")


async def main():
    """Run all real-time scenarios"""
    logger.info("\n" + "="*70)
    logger.info("🌍 LOGISTICS MCP ORCHESTRATOR - REAL-TIME OPERATIONS DEMO")
    logger.info("="*70)
    logger.info("Simulating a full day of logistics operations")
    logger.info("")
    
    ops = LogisticsOperationsDemo()
    
    try:
        # Morning operations
        await scenario_morning_briefing(ops)
        await asyncio.sleep(3)
        
        # Customer emergency
        await scenario_customer_emergency(ops)
        await asyncio.sleep(3)
        
        # AI monitoring
        await scenario_proactive_monitoring(ops)
        await asyncio.sleep(3)
        
        # Status reporting
        await scenario_bulk_status_check(ops)
        await asyncio.sleep(3)
        
        # Real-time tracking
        await scenario_realtime_tracking(ops)
        await asyncio.sleep(3)
        
        # Crisis management
        await scenario_crisis_management(ops)
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("🎉 FULL DAY SIMULATION COMPLETE")
        logger.info("="*70)
        logger.info("Operations Performed:")
        logger.info(f"   • Morning briefing queries: 3")
        logger.info(f"   • Customer emergency handled: 1")
        logger.info(f"   • AI proactive alerts: 1")
        logger.info(f"   • Status reports generated: 1")
        logger.info(f"   • Real-time tracking queries: 1")
        logger.info(f"   • Crisis responses: Multiple shipments")
        logger.info(f"")
        logger.info(f"   Total API calls: ~{ops.request_id}")
        logger.info("="*70)
        logger.info("✅ All scenarios executed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during demo: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
