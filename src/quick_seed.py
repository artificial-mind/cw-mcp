"""
Quick seed script - only seeds if database is completely empty
"""
import asyncio
import logging
from datetime import datetime
from database.database import init_db, get_db_context
from database.models import Shipment
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_seed():
    """Seed database only if empty"""
    try:
        print("="*60)
        print("🌱 QUICK SEED: Checking database status...")
        print("="*60)
        logger.info("Checking database...")
        await init_db()
        
        async with get_db_context() as session:
            # Check if data exists
            result = await session.execute(select(Shipment).limit(1))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"✅ Database already has data (found shipment: {existing.id})")
                logger.info(f"✅ Database already has data (found shipment: {existing.id})")
                return
            
            print("📦 Database is empty - seeding with sample data...")
            logger.info("📦 Database is empty - seeding with sample data...")
            
            # Create shipments directly (using lowercase IDs for consistency)
            shipments = [
                Shipment(id='job-2025-001', master_bill='MAEU123456789', container_no='MSCU1234567',
                        vessel_name='MSC GULSUN', voyage_number='025W', origin_port='Shanghai, China',
                        destination_port='Los Angeles, USA', status_code='IN_TRANSIT',
                        status_description='Container loaded on vessel, departed from Port of Shanghai',
                        etd=datetime(2025, 12, 10, 8, 0), eta=datetime(2025, 12, 25, 14, 30),
                        current_location='South China Sea', current_lat='22.3193', current_lng='114.1694',
                        risk_flag=False),
                Shipment(id='job-2025-002', master_bill='COSU987654321', container_no='COSU9876543',
                        vessel_name='COSCO SHIPPING UNIVERSE', voyage_number='012E', origin_port='Hong Kong',
                        destination_port='Rotterdam, Netherlands', status_code='DELAYED',
                        status_description='Vessel delayed by 48 hours due to adverse weather in Suez Canal',
                        etd=datetime(2025, 12, 5, 10, 0), eta=datetime(2025, 12, 22, 16, 0),
                        current_location='Suez Canal', current_lat='30.5234', current_lng='32.3426',
                        risk_flag=True, agent_notes='Client notified about delay. Requested urgent update on ETA.'),
                Shipment(id='job-2025-003', master_bill='HLCU555666777', container_no='HLCU5556667',
                        vessel_name='HAPAG-LLOYD BERLIN EXPRESS', voyage_number='033E', origin_port='Singapore',
                        destination_port='Hamburg, Germany', status_code='DELIVERED',
                        status_description='Container delivered to consignee warehouse',
                        etd=datetime(2025, 11, 20, 14, 0), eta=datetime(2025, 12, 15, 9, 0),
                        current_location='Hamburg Port', current_lat='53.5511', current_lng='9.9937',
                        risk_flag=False, agent_notes='Delivery completed successfully. POD received.'),
                Shipment(id='job-2025-004', master_bill='OOLU333444555', container_no='OOLU3334445',
                        vessel_name='OOCL HONG KONG', voyage_number='021W', origin_port='Ningbo, China',
                        destination_port='Long Beach, USA', status_code='IN_TRANSIT',
                        status_description='Container on vessel, smooth transit across Pacific',
                        etd=datetime(2025, 12, 8, 16, 30), eta=datetime(2025, 12, 24, 11, 0),
                        current_location='Pacific Ocean', current_lat='32.7157', current_lng='-152.3456',
                        risk_flag=False),
                Shipment(id='job-2025-005', master_bill='CMAU654321987', container_no='CMAU6543219',
                        vessel_name='CMA CGM ANTOINE DE SAINT EXUPERY', voyage_number='056W',
                        origin_port='Marseille, France', destination_port='New York, USA', status_code='IN_TRANSIT',
                        status_description='Container transiting through Mediterranean Sea',
                        etd=datetime(2025, 12, 12, 7, 30), eta=datetime(2025, 12, 28, 15, 0),
                        current_location='Mediterranean Sea', current_lat='36.8968', current_lng='14.4424',
                        risk_flag=False),
                Shipment(id='job-2025-006', master_bill='EGLV111222333', container_no='EGLV1112223',
                        vessel_name='EVER GIVEN', voyage_number='019E', origin_port='Kaohsiung, Taiwan',
                        destination_port='Felixstowe, UK', status_code='DELAYED',
                        status_description='Port congestion at Singapore, vessel waiting for berth',
                        etd=datetime(2025, 12, 8, 12, 0), eta=datetime(2025, 12, 20, 10, 0),
                        current_location='Port of Singapore', current_lat='1.2644', current_lng='103.8223',
                        risk_flag=True, agent_notes='High priority shipment. Customer anxious about delays.'),
                Shipment(id='job-2025-007', master_bill='YMLU888777666', container_no='YMLU8887776',
                        vessel_name='YANG MING WISDOM', voyage_number='042N', origin_port='Tokyo, Japan',
                        destination_port='Los Angeles, USA', status_code='AT_PORT',
                        status_description='Container discharged at Port of LA, in transit to warehouse',
                        etd=datetime(2025, 11, 25, 9, 0), eta=datetime(2025, 12, 16, 8, 30),
                        current_location='Port of Los Angeles', current_lat='33.7361', current_lng='-118.2644',
                        risk_flag=False, agent_notes='Awaiting truck pickup for final mile delivery.'),
                Shipment(id='job-2025-008', master_bill='ONEY555444333', container_no='ONEY5554443',
                        vessel_name='ONE APUS', voyage_number='028W', origin_port='Busan, South Korea',
                        destination_port='Seattle, USA', status_code='IN_TRANSIT',
                        status_description='Container en route across Pacific Ocean',
                        etd=datetime(2025, 12, 11, 5, 0), eta=datetime(2025, 12, 26, 20, 0),
                        current_location='Pacific Ocean', current_lat='35.6762', current_lng='-140.1234',
                        risk_flag=False),
                Shipment(id='job-2025-009', master_bill='ZIMU999888777', container_no='ZIMU9998887',
                        vessel_name='ZIM SAMMY OFER', voyage_number='064S', origin_port='Haifa, Israel',
                        destination_port='Dubai, UAE', status_code='CUSTOMS_HOLD',
                        status_description='Container held at customs - documentation discrepancy',
                        etd=datetime(2025, 11, 30, 11, 0), eta=datetime(2025, 12, 17, 13, 0),
                        current_location='Port of Jebel Ali', current_lat='25.0095', current_lng='55.1136',
                        risk_flag=True, agent_notes='URGENT: Missing commercial invoice. Coordinating with shipper.'),
                Shipment(id='job-2025-010', master_bill='MSMU777666555', container_no='MSMU7776665',
                        vessel_name='MSC MAYA', voyage_number='015E', origin_port='Mumbai, India',
                        destination_port='Antwerp, Belgium', status_code='IN_TRANSIT',
                        status_description='Container on vessel, smooth sailing expected',
                        etd=datetime(2025, 12, 13, 6, 30), eta=datetime(2025, 12, 30, 17, 0),
                        current_location='Indian Ocean', current_lat='-10.4475', current_lng='70.3321',
                        risk_flag=False, agent_notes='Standard shipment, no issues reported.'),
            ]
            
            for shipment in shipments:
                session.add(shipment)
            
            await session.commit()
            print(f"✅ Seeded {len(shipments)} shipments successfully!")
            print("="*60)
            logger.info(f"✅ Seeded {len(shipments)} shipments successfully!")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    asyncio.run(quick_seed())
