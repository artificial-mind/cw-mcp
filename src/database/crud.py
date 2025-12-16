"""
CRUD operations for database entities
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
from datetime import datetime
import logging

from .models import Shipment, AuditLog

logger = logging.getLogger(__name__)


class ShipmentCRUD:
    """CRUD operations for Shipment model"""
    
    @staticmethod
    async def create(db: AsyncSession, shipment_data: dict) -> Shipment:
        """Create a new shipment"""
        shipment = Shipment(**shipment_data)
        db.add(shipment)
        await db.flush()
        await db.refresh(shipment)
        return shipment
    
    @staticmethod
    async def get_by_id(db: AsyncSession, shipment_id: str) -> Optional[Shipment]:
        """Get shipment by ID"""
        result = await db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_container(db: AsyncSession, container_no: str) -> Optional[Shipment]:
        """Get shipment by container number"""
        result = await db.execute(
            select(Shipment).where(Shipment.container_no == container_no)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_master_bill(db: AsyncSession, master_bill: str) -> Optional[Shipment]:
        """Get shipment by master bill"""
        result = await db.execute(
            select(Shipment).where(Shipment.master_bill == master_bill)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search(
        db: AsyncSession,
        container_no: Optional[str] = None,
        master_bill: Optional[str] = None,
        status_code: Optional[str] = None,
        risk_flag: Optional[bool] = None,
        limit: int = 50
    ) -> List[Shipment]:
        """Search shipments with multiple filters"""
        query = select(Shipment)
        conditions = []
        
        if container_no:
            conditions.append(Shipment.container_no.ilike(f"%{container_no}%"))
        if master_bill:
            conditions.append(Shipment.master_bill.ilike(f"%{master_bill}%"))
        if status_code:
            conditions.append(Shipment.status_code == status_code)
        if risk_flag is not None:
            conditions.append(Shipment.risk_flag == risk_flag)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update(
        db: AsyncSession,
        shipment_id: str,
        update_data: dict
    ) -> Optional[Shipment]:
        """Update shipment fields"""
        shipment = await ShipmentCRUD.get_by_id(db, shipment_id)
        if not shipment:
            return None
        
        for key, value in update_data.items():
            if hasattr(shipment, key):
                setattr(shipment, key, value)
        
        shipment.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(shipment)
        return shipment
    
    @staticmethod
    async def delete(db: AsyncSession, shipment_id: str) -> bool:
        """Delete a shipment"""
        shipment = await ShipmentCRUD.get_by_id(db, shipment_id)
        if not shipment:
            return False
        
        await db.delete(shipment)
        return True
    
    @staticmethod
    async def get_all(db: AsyncSession, limit: int = 100) -> List[Shipment]:
        """Get all shipments"""
        result = await db.execute(select(Shipment).limit(limit))
        return result.scalars().all()


class AuditLogCRUD:
    """CRUD operations for AuditLog model"""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        shipment_id: str,
        action: str,
        reason: Optional[str] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        log = AuditLog(
            shipment_id=shipment_id,
            action=action,
            reason=reason,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            agent_id=agent_id
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log
    
    @staticmethod
    async def get_by_shipment(
        db: AsyncSession,
        shipment_id: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get all audit logs for a shipment"""
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.shipment_id == shipment_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_recent(db: AsyncSession, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs across all shipments"""
        result = await db.execute(
            select(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
