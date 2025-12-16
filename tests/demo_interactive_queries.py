#!/usr/bin/env python3
"""
Interactive Query Console for Logistics MCP Orchestrator
Try real-time queries interactively
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
HEADERS = {
    "Authorization": "Bearer dev-api-key-12345",
    "Content-Type": "application/json"
}


async def call_tool(tool_name: str, arguments: dict):
    """Call a tool and return result"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/messages",
            json=payload,
            headers=HEADERS,
            timeout=10.0
        )
        return response.json()


async def demo_query_1():
    """Find all containers currently in transit"""
    print("\n" + "="*70)
    print("🔍 QUERY 1: 'Show me all containers currently in transit'")
    print("="*70)
    
    result = await call_tool("search_shipments", {
        "status": "IN_TRANSIT",
        "limit": 10
    })
    
    shipments = result.get("result", {}).get("results", [])
    print(f"\nFound {len(shipments)} containers in transit:\n")
    
    for ship in shipments:
        print(f"📦 {ship['id']}")
        print(f"   Vessel: {ship['tracking']['vessel']}")
        print(f"   Location: {ship['tracking']['location']['name']}")
        print(f"   ETA: {ship['schedule']['eta']}")
        print()


async def demo_query_2():
    """Check what's arriving tomorrow"""
    print("\n" + "="*70)
    print("📅 QUERY 2: 'What shipments are expected to arrive soon?'")
    print("="*70)
    
    result = await call_tool("search_shipments", {
        "limit": 10
    })
    
    all_shipments = result.get("result", {}).get("results", [])
    print(f"\nUpcoming arrivals:\n")
    
    # Sort by ETA
    sorted_ships = sorted(all_shipments, key=lambda x: x['schedule']['eta'])
    
    for ship in sorted_ships[:5]:
        eta_date = ship['schedule']['eta'].split('T')[0]
        print(f"📅 {eta_date} - {ship['id']}")
        print(f"   Container: {ship['tracking']['container']}")
        print(f"   Status: {ship['status']['code']}")
        print()


async def demo_query_3():
    """Find specific customer's shipments"""
    print("\n" + "="*70)
    print("🔎 QUERY 3: 'Track all shipments for a specific route'")
    print("="*70)
    print("Searching for: Shanghai → Los Angeles route\n")
    
    result = await call_tool("search_shipments", {
        "limit": 20
    })
    
    all_shipments = result.get("result", {}).get("results", [])
    
    # Filter by route (simulated - looking for China/LA mentions)
    route_shipments = [s for s in all_shipments if 
                      'China' in s['tracking']['location']['name'] or 
                      'Shanghai' in s['tracking']['location']['name']]
    
    print(f"Found {len(route_shipments)} shipments on this route:\n")
    
    for ship in route_shipments:
        print(f"🚢 {ship['id']}")
        print(f"   Vessel: {ship['tracking']['vessel']}")
        print(f"   From: {ship['tracking']['location']['name']}")
        print(f"   Status: {ship['status']['code']}")
        print()


async def demo_query_4():
    """Risk assessment query"""
    print("\n" + "="*70)
    print("⚠️  QUERY 4: 'Show me shipments that need attention'")
    print("="*70)
    
    result = await call_tool("search_shipments", {
        "risk_flag": True,
        "limit": 10
    })
    
    risky = result.get("result", {}).get("results", [])
    print(f"\n🚨 {len(risky)} shipments require attention:\n")
    
    for i, ship in enumerate(risky, 1):
        print(f"{i}. {ship['id']} - PRIORITY: HIGH")
        print(f"   Issue: {ship['status']['code']}")
        print(f"   Location: {ship['tracking']['location']['name']}")
        print(f"   Notes: {ship['flags']['agent_notes'][:80]}...")
        print()


async def demo_query_5():
    """Detailed vessel tracking"""
    print("\n" + "="*70)
    print("🌍 QUERY 5: 'Where is the MSC GULSUN right now?'")
    print("="*70)
    
    result = await call_tool("track_shipment", {
        "identifier": "JOB-2025-001",
        "source": "local"
    })
    
    shipment = result.get("result", {}).get("shipment", {})
    if shipment:
        loc = shipment['tracking']['location']
        print(f"\n📍 VESSEL POSITION:")
        print(f"   Vessel: {shipment['tracking']['vessel']}")
        print(f"   Voyage: {shipment['tracking']['voyage']}")
        print(f"   ")
        print(f"   Current Location: {loc['name']}")
        print(f"   Latitude: {loc['lat']}")
        print(f"   Longitude: {loc['lng']}")
        print(f"   ")
        print(f"   Status: {shipment['status']['code']}")
        print(f"   ETA: {shipment['schedule']['eta']}")
        print()


async def demo_query_6():
    """Performance metrics"""
    print("\n" + "="*70)
    print("📊 QUERY 6: 'Give me operational statistics'")
    print("="*70)
    
    result = await call_tool("search_shipments", {
        "limit": 20
    })
    
    all_shipments = result.get("result", {}).get("results", [])
    
    # Calculate stats
    total = len(all_shipments)
    in_transit = sum(1 for s in all_shipments if s['status']['code'] == 'IN_TRANSIT')
    delayed = sum(1 for s in all_shipments if s['status']['code'] == 'DELAYED')
    delivered = sum(1 for s in all_shipments if s['status']['code'] == 'DELIVERED')
    risky = sum(1 for s in all_shipments if s['flags']['is_risk'])
    
    print(f"\n📈 OPERATIONAL METRICS:")
    print(f"   Total Active Shipments: {total}")
    print(f"   ")
    print(f"   Status Breakdown:")
    print(f"      ✈️  In Transit: {in_transit} ({100*in_transit/total:.1f}%)")
    print(f"      ⏱️  Delayed: {delayed} ({100*delayed/total:.1f}%)")
    print(f"      ✅ Delivered: {delivered} ({100*delivered/total:.1f}%)")
    print(f"   ")
    print(f"   Risk Level:")
    print(f"      ⚠️  High Risk: {risky} ({100*risky/total:.1f}%)")
    print(f"      ✅ Normal: {total-risky} ({100*(total-risky)/total:.1f}%)")
    print()
    
    # On-time performance
    on_time_rate = ((total - delayed) / total * 100) if total > 0 else 0
    print(f"   📊 On-Time Performance: {on_time_rate:.1f}%")
    print()


async def main():
    """Run all demo queries"""
    print("\n" + "="*70)
    print("🌍 LOGISTICS MCP ORCHESTRATOR - INTERACTIVE QUERIES")
    print("="*70)
    print("Demonstrating realistic queries you can run against the system")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    try:
        # Run each query with a pause
        await demo_query_1()
        await asyncio.sleep(2)
        
        await demo_query_2()
        await asyncio.sleep(2)
        
        await demo_query_3()
        await asyncio.sleep(2)
        
        await demo_query_4()
        await asyncio.sleep(2)
        
        await demo_query_5()
        await asyncio.sleep(2)
        
        await demo_query_6()
        
        print("\n" + "="*70)
        print("✅ ALL INTERACTIVE QUERIES COMPLETED!")
        print("="*70)
        print("\nThese queries demonstrate:")
        print("  • Real-time shipment tracking")
        print("  • Multi-criteria search")
        print("  • Risk assessment")
        print("  • Operational analytics")
        print("  • Vessel positioning")
        print("  • Performance metrics")
        print("\nAll data retrieved in real-time from the MCP server!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
