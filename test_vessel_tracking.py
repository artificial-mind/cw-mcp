"""
Test the real_time_vessel_tracking MCP tool
"""
import asyncio
import sys
sys.path.insert(0, '/Users/testing/Documents/cw/cw-ai-server/src')

from adapters.vessel_tracking_adapter import VesselTrackingAdapter


async def test_vessel_tracking():
    """Test vessel tracking with mock data"""
    print("=" * 60)
    print("Testing Vessel Tracking Adapter")
    print("=" * 60)
    
    # Initialize with no API key (uses mock data)
    tracker = VesselTrackingAdapter(api_key=None)
    
    # Test 1: Search for vessel
    print("\n✅ Test 1: Search for MAERSK ESSEX")
    vessel_info = await tracker.search_vessel("MAERSK ESSEX")
    if vessel_info:
        print(f"   Found: {vessel_info['vessel_name']}")
        print(f"   IMO: {vessel_info['imo']}")
        print(f"   MMSI: {vessel_info['mmsi']}")
        print(f"   Type: {vessel_info['vessel_type']}")
        print(f"   Flag: {vessel_info['flag']}")
    else:
        print("   ❌ Vessel not found")
    
    # Test 2: Get vessel position
    print("\n✅ Test 2: Get position for MAERSK ESSEX")
    position_data = await tracker.get_vessel_position(vessel_name="MAERSK ESSEX")
    if position_data:
        print(f"   Position: {position_data['position']['lat']}, {position_data['position']['lon']}")
        print(f"   Speed: {position_data['navigation']['speed']} knots")
        print(f"   Heading: {position_data['navigation']['heading']}°")
        print(f"   Status: {position_data['navigation']['status']}")
        print(f"   Destination: {position_data['destination']}")
        print(f"   ETA: {position_data['eta']}")
        print(f"   Progress: {position_data.get('voyage_progress', 'N/A')}")
        print(f"   Source: {position_data['data_source']}")
    else:
        print("   ❌ Position not found")
    
    # Test 3: Try other vessels
    print("\n✅ Test 3: Test other mock vessels")
    test_vessels = ["MSC GULSUN", "EVER GIVEN", "COSCO SHIPPING UNIVERSE"]
    for vessel in test_vessels:
        result = await tracker.search_vessel(vessel)
        if result:
            print(f"   ✓ {vessel} - {result['vessel_type']}")
        else:
            print(f"   ✗ {vessel} - Not found")
    
    # Test 4: Try non-existent vessel
    print("\n✅ Test 4: Search for non-existent vessel")
    result = await tracker.search_vessel("FAKE SHIP 123")
    if result:
        print(f"   Unexpected: Found {result}")
    else:
        print("   ✓ Correctly returned None for non-existent vessel")
    
    await tracker.close()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_vessel_tracking())
