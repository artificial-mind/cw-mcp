"""
Database seeding script with realistic logistics data
"""
import asyncio
from datetime import datetime, timedelta
import sys
import logging

from database.database import init_db, get_db_context
from database.crud import ShipmentCRUD, AuditLogCRUD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Realistic sample data
SAMPLE_SHIPMENTS = [
    {
        "id": "JOB-2025-001",
        "master_bill": "MAEU123456789",
        "container_no": "MSCU1234567",
        "vessel_name": "MSC GULSUN",
        "voyage_number": "025W",
        "origin_port": "Shanghai, China",
        "destination_port": "Los Angeles, USA",
        "status_code": "IN_TRANSIT",
        "status_description": "Container loaded on vessel, departed from Port of Shanghai",
        "etd": datetime(2025, 12, 10, 8, 0),
        "eta": datetime(2025, 12, 25, 14, 30),
        "current_location": "South China Sea",
        "current_lat": "22.3193",
        "current_lng": "114.1694",
        "risk_flag": False,
        "agent_notes": None
    },
    {
        "id": "JOB-2025-002",
        "master_bill": "COSU987654321",
        "container_no": "COSU9876543",
        "vessel_name": "COSCO SHIPPING UNIVERSE",
        "voyage_number": "012E",
        "status_code": "DELAYED",
        "status_description": "Vessel delayed by 48 hours due to adverse weather conditions in Suez Canal",
        "etd": datetime(2025, 12, 5, 10, 0),
        "eta": datetime(2025, 12, 22, 16, 0),
        "current_location": "Suez Canal",
        "current_lat": "30.5234",
        "current_lng": "32.3426",
        "risk_flag": True,
        "agent_notes": "Client notified about delay. Requested urgent update on ETA."
    },
    {
        "id": "JOB-2025-003",
        "master_bill": "OOLU456789123",
        "container_no": "OOLU4567891",
        "vessel_name": "OOCL HONG KONG",
        "voyage_number": "087N",
        "status_code": "AT_PORT",
        "status_description": "Container arrived at Port of Rotterdam, awaiting customs clearance",
        "etd": datetime(2025, 11, 28, 14, 0),
        "eta": datetime(2025, 12, 15, 9, 0),
        "current_location": "Port of Rotterdam",
        "current_lat": "51.9244",
        "current_lng": "4.4777",
        "risk_flag": False,
        "agent_notes": "Customs documents submitted. Expecting clearance within 24 hours."
    },
    {
        "id": "JOB-2025-004",
        "master_bill": "HLCU789456123",
        "container_no": "HLCU7894561",
        "vessel_name": "HAPAG-LLOYD EXPRESS",
        "voyage_number": "034S",
        "status_code": "DELIVERED",
        "status_description": "Container delivered to final destination warehouse",
        "etd": datetime(2025, 11, 20, 6, 0),
        "eta": datetime(2025, 12, 8, 11, 0),
        "current_location": "Hamburg Warehouse District",
        "current_lat": "53.5511",
        "current_lng": "9.9937",
        "risk_flag": False,
        "agent_notes": "Successful delivery. Client confirmed receipt of goods."
    },
    {
        "id": "JOB-2025-005",
        "master_bill": "CMAU654321987",
        "container_no": "CMAU6543219",
        "vessel_name": "CMA CGM ANTOINE DE SAINT EXUPERY",
        "voyage_number": "056W",
        "status_code": "IN_TRANSIT",
        "status_description": "Container transiting through Mediterranean Sea",
        "etd": datetime(2025, 12, 12, 7, 30),
        "eta": datetime(2025, 12, 28, 15, 0),
        "current_location": "Mediterranean Sea",
        "current_lat": "36.8968",
        "current_lng": "14.4424",
        "risk_flag": False,
        "agent_notes": None
    },
    {
        "id": "JOB-2025-006",
        "master_bill": "EGLV111222333",
        "container_no": "EGLV1112223",
        "vessel_name": "EVER GIVEN",
        "voyage_number": "019E",
        "status_code": "DELAYED",
        "status_description": "Port congestion at Singapore, vessel waiting for berth allocation",
        "etd": datetime(2025, 12, 8, 12, 0),
        "eta": datetime(2025, 12, 20, 10, 0),
        "current_location": "Port of Singapore",
        "current_lat": "1.2644",
        "current_lng": "103.8223",
        "risk_flag": True,
        "agent_notes": "High priority shipment. Customer is getting anxious about delays."
    },
    {
        "id": "JOB-2025-007",
        "master_bill": "YMLU888777666",
        "container_no": "YMLU8887776",
        "vessel_name": "YANG MING WISDOM",
        "voyage_number": "042N",
        "status_code": "AT_PORT",
        "status_description": "Container discharged at Port of Los Angeles, in transit to warehouse",
        "etd": datetime(2025, 11, 25, 9, 0),
        "eta": datetime(2025, 12, 16, 8, 30),
        "current_location": "Port of Los Angeles",
        "current_lat": "33.7361",
        "current_lng": "-118.2644",
        "risk_flag": False,
        "agent_notes": "Awaiting truck pickup for final mile delivery."
    },
    {
        "id": "JOB-2025-008",
        "master_bill": "ONEY555444333",
        "container_no": "ONEY5554443",
        "vessel_name": "ONE APUS",
        "voyage_number": "028W",
        "status_code": "IN_TRANSIT",
        "status_description": "Container en route across Pacific Ocean",
        "etd": datetime(2025, 12, 11, 5, 0),
        "eta": datetime(2025, 12, 26, 20, 0),
        "current_location": "Pacific Ocean",
        "current_lat": "35.6762",
        "current_lng": "-140.1234",
        "risk_flag": False,
        "agent_notes": None
    },
    {
        "id": "JOB-2025-009",
        "master_bill": "ZIMU999888777",
        "container_no": "ZIMU9998887",
        "vessel_name": "ZIM SAMMY OFER",
        "voyage_number": "064S",
        "status_code": "CUSTOMS_HOLD",
        "status_description": "Container held at customs for inspection - documentation discrepancy",
        "etd": datetime(2025, 11, 30, 11, 0),
        "eta": datetime(2025, 12, 17, 13, 0),
        "current_location": "Port of Jebel Ali",
        "current_lat": "25.0095",
        "current_lng": "55.1136",
        "risk_flag": True,
        "agent_notes": "URGENT: Missing commercial invoice. Coordinating with shipper to resolve."
    },
    {
        "id": "JOB-2025-010",
        "master_bill": "MSMU777666555",
        "container_no": "MSMU7776665",
        "vessel_name": "MSC MAYA",
        "voyage_number": "015E",
        "status_code": "IN_TRANSIT",
        "status_description": "Container on vessel, smooth sailing expected",
        "etd": datetime(2025, 12, 13, 6, 30),
        "eta": datetime(2025, 12, 30, 17, 0),
        "current_location": "Indian Ocean",
        "current_lat": "-10.4475",
        "current_lng": "70.3321",
        "risk_flag": False,
        "agent_notes": "Standard shipment, no issues reported."
    }
]

# Sample audit logs for some shipments
SAMPLE_AUDIT_LOGS = [
    {
        "shipment_id": "JOB-2025-002",
        "action": "UPDATE_ETA",
        "reason": "Weather delay in Suez Canal reported by vessel operator",
        "field_name": "eta",
        "old_value": "2025-12-20T16:00:00",
        "new_value": "2025-12-22T16:00:00",
        "agent_id": "ai-agent-001"
    },
    {
        "shipment_id": "JOB-2025-002",
        "action": "SET_RISK_FLAG",
        "reason": "Client is high-priority and delay exceeds acceptable threshold",
        "field_name": "risk_flag",
        "old_value": "false",
        "new_value": "true",
        "agent_id": "ai-agent-001"
    },
    {
        "shipment_id": "JOB-2025-006",
        "action": "ADD_NOTE",
        "reason": "Customer inquiry received about shipment status",
        "field_name": "agent_notes",
        "old_value": None,
        "new_value": "High priority shipment. Customer is getting anxious about delays.",
        "agent_id": "ai-agent-002"
    },
    {
        "shipment_id": "JOB-2025-009",
        "action": "SET_RISK_FLAG",
        "reason": "Customs hold detected - requires immediate attention",
        "field_name": "risk_flag",
        "old_value": "false",
        "new_value": "true",
        "agent_id": "ai-agent-003"
    }
]


async def seed_database():
    """Seed the database with sample data"""
    try:
        logger.info("Initializing database...")
        await init_db()
        
        async with get_db_context() as db:
            # Check if data already exists
            existing_shipments = await ShipmentCRUD.get_all(db, limit=1)
            if existing_shipments:
                logger.warning("Database already contains data. Skipping seed.")
                return
            
            logger.info(f"Seeding {len(SAMPLE_SHIPMENTS)} shipments...")
            for shipment_data in SAMPLE_SHIPMENTS:
                await ShipmentCRUD.create(db, shipment_data)
            
            logger.info(f"Seeding {len(SAMPLE_AUDIT_LOGS)} audit log entries...")
            for log_data in SAMPLE_AUDIT_LOGS:
                await AuditLogCRUD.create(db, **log_data)
            
            await db.commit()
            logger.info("✅ Database seeded successfully!")
            
            # Verify
            shipments = await ShipmentCRUD.get_all(db, limit=100)
            logger.info(f"Total shipments in database: {len(shipments)}")
            
            risk_shipments = await ShipmentCRUD.search(db, risk_flag=True)
            logger.info(f"Shipments flagged as risk: {len(risk_shipments)}")
            
    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())
