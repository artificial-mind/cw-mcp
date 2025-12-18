#!/usr/bin/env python3
"""
Local test script to verify database and tools work correctly
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.database import init_db, get_db_context
from database.models import Shipment
from sqlalchemy import select

async def test_database():
    """Test database has data"""
    print("="*60)
    print("🧪 Testing Database Locally")
    print("="*60)
    
    await init_db()
    print("✅ Database initialized")
    
    async with get_db_context() as session:
        # Count all shipments
        result = await session.execute(select(Shipment))
        all_shipments = result.scalars().all()
        print(f"\n📊 Total shipments in database: {len(all_shipments)}")
        
        if all_shipments:
            print("\n📦 Sample shipments:")
            for s in all_shipments[:3]:
                print(f"  - {s.id}: {s.container_no} ({s.status_code}) - {s.vessel_name}")
        
        # Test search by status
        print(f"\n🔍 Testing search for DELAYED shipments:")
        result = await session.execute(
            select(Shipment).where(Shipment.status_code == 'DELAYED')
        )
        delayed = result.scalars().all()
        print(f"  Found {len(delayed)} delayed shipments")
        for s in delayed:
            print(f"  - {s.id}: {s.container_no} - {s.status_description}")
        
        # Test search by risk flag
        print(f"\n🚨 Testing search for high-risk shipments:")
        result = await session.execute(
            select(Shipment).where(Shipment.risk_flag == True)
        )
        risky = result.scalars().all()
        print(f"  Found {len(risky)} high-risk shipments")
        for s in risky:
            print(f"  - {s.id}: {s.container_no} - Risk: {s.risk_flag}")
        
        # Test track by ID
        print(f"\n📦 Testing track shipment 'job-2025-001':")
        result = await session.execute(
            select(Shipment).where(Shipment.id == 'job-2025-001')
        )
        shipment = result.scalar_one_or_none()
        if shipment:
            print(f"  ✅ Found: {shipment.master_bill}")
            print(f"     Container: {shipment.container_no}")
            print(f"     Vessel: {shipment.vessel_name}")
            print(f"     Route: {shipment.origin_port} → {shipment.destination_port}")
            print(f"     Status: {shipment.status_code}")
        else:
            print("  ❌ Not found!")
    
    print("\n" + "="*60)
    print("✅ Database test complete!")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(test_database())
