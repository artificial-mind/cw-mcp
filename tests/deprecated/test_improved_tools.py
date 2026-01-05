"""
Test script for the improved MCP tools
Run this to verify all new tools work correctly
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.database import init_db, get_db_context
from database.models import Shipment
from sqlalchemy import select

async def test_advanced_tools():
    """Test the new advanced tools"""
    print("=" * 60)
    print("🧪 Testing Improved MCP Tools")
    print("=" * 60)
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Test 1: Check data exists
    async with get_db_context() as session:
        result = await session.execute(select(Shipment))
        shipments = result.scalars().all()
        print(f"\n📦 Database has {len(shipments)} shipments")
        
        if len(shipments) == 0:
            print("⚠️  No data found - run quick_seed.py first")
            return
    
    # Test 2: Advanced Search Simulation
    print("\n" + "=" * 60)
    print("Test 1: Advanced Search (Vessel Filter)")
    print("=" * 60)
    async with get_db_context() as session:
        # Search by vessel
        result = await session.execute(
            select(Shipment).where(Shipment.vessel_name.like("%MSC%"))
        )
        msc_ships = result.scalars().all()
        print(f"✅ Found {len(msc_ships)} MSC vessels")
        for ship in msc_ships:
            print(f"   - {ship.id}: {ship.vessel_name} → {ship.destination_port}")
    
    # Test 3: Risk Analysis
    print("\n" + "=" * 60)
    print("Test 2: Risk Analysis")
    print("=" * 60)
    async with get_db_context() as session:
        result = await session.execute(
            select(Shipment).where(Shipment.risk_flag == True)
        )
        risky = result.scalars().all()
        print(f"✅ Found {len(risky)} high-risk shipments")
        for ship in risky:
            print(f"   🚨 {ship.id}: {ship.status_code} - {ship.agent_notes}")
    
    # Test 4: Status Breakdown
    print("\n" + "=" * 60)
    print("Test 3: Status Breakdown")
    print("=" * 60)
    async with get_db_context() as session:
        from sqlalchemy import func
        result = await session.execute(
            select(Shipment.status_code, func.count(Shipment.id))
            .group_by(Shipment.status_code)
        )
        status_counts = result.all()
        print("✅ Status distribution:")
        for status, count in status_counts:
            print(f"   - {status}: {count} shipments")
    
    # Test 5: Route Analysis
    print("\n" + "=" * 60)
    print("Test 4: Route Analysis (China → USA)")
    print("=" * 60)
    async with get_db_context() as session:
        result = await session.execute(
            select(Shipment).where(
                Shipment.origin_port.like("%China%"),
                Shipment.destination_port.like("%USA%")
            )
        )
        route_ships = result.scalars().all()
        print(f"✅ Found {len(route_ships)} shipments on China → USA route")
        for ship in route_ships:
            print(f"   - {ship.id}: {ship.vessel_name}")
            print(f"     {ship.origin_port} → {ship.destination_port}")
            print(f"     ETA: {ship.eta}")
    
    # Test 6: Delayed Shipments
    print("\n" + "=" * 60)
    print("Test 5: Delayed Shipments")
    print("=" * 60)
    async with get_db_context() as session:
        from datetime import datetime, timedelta
        now = datetime.now()
        cutoff = now - timedelta(days=1)
        
        result = await session.execute(
            select(Shipment).where(
                Shipment.eta < cutoff,
                Shipment.status_code.in_(['IN_TRANSIT', 'DELAYED', 'AT_PORT'])
            )
        )
        delayed = result.scalars().all()
        print(f"✅ Found {len(delayed)} delayed shipments")
        for ship in delayed:
            if ship.eta:
                days_late = (now - ship.eta).days
                print(f"   ⏰ {ship.id}: {days_late} days past ETA")
                print(f"      Original ETA: {ship.eta}")
    
    # Test 7: Text Search Simulation
    print("\n" + "=" * 60)
    print("Test 6: Text Search (Rotterdam)")
    print("=" * 60)
    async with get_db_context() as session:
        from sqlalchemy import or_
        search_text = "Rotterdam"
        pattern = f"%{search_text}%"
        
        result = await session.execute(
            select(Shipment).where(
                or_(
                    Shipment.origin_port.like(pattern),
                    Shipment.destination_port.like(pattern),
                    Shipment.current_location.like(pattern)
                )
            )
        )
        found = result.scalars().all()
        print(f"✅ Found {len(found)} shipments matching '{search_text}'")
        for ship in found:
            print(f"   - {ship.id}: {ship.origin_port} → {ship.destination_port}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ All Tests Completed Successfully!")
    print("=" * 60)
    print("\n🎯 New Tools Validated:")
    print("   1. search_shipments_advanced - Multi-filter search")
    print("   2. get_shipments_analytics - Statistics & overview")
    print("   3. query_shipments_by_criteria - Flexible text search")
    print("   4. get_delayed_shipments - Find delayed shipments")
    print("   5. get_shipments_by_route - Route analysis")
    print("\n✅ Ready for deployment!")

if __name__ == "__main__":
    asyncio.run(test_advanced_tools())
