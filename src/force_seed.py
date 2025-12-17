"""
Force seed database - always overwrites existing data
Run this to reseed the database on Render
"""
import asyncio
import logging
from seed_database import SAMPLE_SHIPMENTS, SAMPLE_AUDIT_LOGS
from database.database import init_db, get_db_context
from database.crud import ShipmentCRUD, AuditLogCRUD
from database.models import Shipment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def force_seed():
    """Force seed the database, deleting any existing data"""
    try:
        logger.info("🔄 Force seeding database...")
        await init_db()
        
        async with get_db_context() as db:
            # Delete all existing data
            logger.info("🗑️ Deleting existing shipments...")
            from sqlalchemy import delete
            await db.execute(delete(Shipment))
            await db.commit()
            
            # Seed new data
            logger.info(f"📦 Inserting {len(SAMPLE_SHIPMENTS)} shipments...")
            for shipment_data in SAMPLE_SHIPMENTS:
                await ShipmentCRUD.create(db, shipment_data)
            
            logger.info(f"📝 Inserting {len(SAMPLE_AUDIT_LOGS)} audit logs...")
            for log_data in SAMPLE_AUDIT_LOGS:
                await AuditLogCRUD.create(db, **log_data)
            
            await db.commit()
            
            # Verify
            shipments = await ShipmentCRUD.get_all(db, limit=100)
            logger.info(f"✅ Database seeded! Total shipments: {len(shipments)}")
            
            if shipments:
                logger.info(f"✅ First shipment: {shipments[0].job_id} - {shipments[0].container_no}")
            
    except Exception as e:
        logger.error(f"❌ Error force seeding database: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(force_seed())
