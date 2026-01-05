"""
Test script for ML-powered delay prediction.
Tests the predictive_delay_detection tool with real shipments from the database.
"""
import asyncio
import sys
sys.path.insert(0, 'src')

from tools import predictive_delay_detection
from database.database import get_db_context
from database.crud import ShipmentCRUD


async def test_delay_prediction():
    """Test delay prediction on shipments from the database."""
    print("=" * 70)
    print("🔮 Testing ML-Powered Delay Prediction")
    print("=" * 70)
    
    # Get shipments from database
    async with get_db_context() as db:
        shipments = await ShipmentCRUD.search(db, limit=100)
        
        if not shipments:
            print("\n❌ No shipments found in database!")
            print("Run python src/quick_seed.py to create test data.")
            return
        
        print(f"\n✅ Found {len(shipments)} shipments in database")
        print("\nTesting delay predictions on first 3 shipments:\n")
        
        # Test predictions on first 3 shipments
        for i, shipment in enumerate(shipments[:3], 1):
            print(f"\n{'=' * 70}")
            print(f"Test {i}: Shipment {shipment.id}")
            print(f"{'=' * 70}")
            print(f"Route: {shipment.origin_port} → {shipment.destination_port}")
            print(f"Vessel: {shipment.vessel_name}")
            print(f"Container: {shipment.container_no}")
            print(f"Current Status: {shipment.status_code}")
            print(f"Risk Flag: {'Yes' if shipment.risk_flag else 'No'}")
            
            # Run ML prediction
            try:
                result = await predictive_delay_detection(shipment.id)
                
                print(f"\n🤖 ML PREDICTION:")
                print(f"  Will Delay: {result['will_delay']}")
                print(f"  Confidence: {result['confidence']}")
                print(f"  Delay Probability: {result['delay_probability']:.1%}")
                
                if result['risk_factors']:
                    print(f"\n⚠️  RISK FACTORS:")
                    for factor in result['risk_factors']:
                        print(f"    • {factor}")
                
                print(f"\n💡 RECOMMENDATION:")
                print(f"  {result['recommendation']}")
                
                # Show prediction alignment with actual status
                if shipment.status_code and 'delay' in shipment.status_code.lower():
                    aligned = result['will_delay']
                    emoji = "✅" if aligned else "❌"
                    print(f"\n{emoji} Prediction {'MATCHES' if aligned else 'DOES NOT MATCH'} actual status (DELAYED)")
                elif shipment.status_code:
                    aligned = not result['will_delay']
                    emoji = "✅" if aligned else "❌"
                    print(f"\n{emoji} Prediction {'MATCHES' if aligned else 'DOES NOT MATCH'} actual status ({shipment.status_code.upper()})")
                
            except Exception as e:
                print(f"\n❌ ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("✅ Testing complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_delay_prediction())
