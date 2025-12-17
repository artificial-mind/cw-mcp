"""
SQLAlchemy models for local cache database
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Shipment(Base):
    """
    Shipment model - stores core shipment data with custom fields
    that don't exist in external systems (risk flags, agent notes)
    """
    __tablename__ = "shipments"
    
    # Primary identifier
    id = Column(String, primary_key=True, index=True)  # e.g., "JOB-2025-001"
    
    # Core shipment data
    master_bill = Column(String, index=True)  # MBL / AWB number
    container_no = Column(String, index=True)
    vessel_name = Column(String, nullable=True)
    voyage_number = Column(String, nullable=True)
    
    # Ports
    origin_port = Column(String, nullable=True)
    destination_port = Column(String, nullable=True)
    
    # Status information
    status_code = Column(String, index=True)  # Standardized: IN_TRANSIT, DELAYED, DELIVERED, etc.
    status_description = Column(Text, nullable=True)
    
    # Schedule
    etd = Column(DateTime, nullable=True)  # Estimated Time of Departure
    eta = Column(DateTime, nullable=True)  # Estimated Time of Arrival
    
    # Location tracking
    current_location = Column(String, nullable=True)
    current_lat = Column(String, nullable=True)
    current_lng = Column(String, nullable=True)
    
    # Custom fields for AI agents
    risk_flag = Column(Boolean, default=False, index=True)
    agent_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="shipment", cascade="all, delete-orphan")
    
    def to_standard_format(self) -> dict:
        """Convert to the standard JSON format for agents"""
        return {
            "id": self.id,
            "tracking": {
                "container": self.container_no,
                "vessel": self.vessel_name,
                "voyage": self.voyage_number,
                "location": {
                    "lat": float(self.current_lat) if self.current_lat else None,
                    "lng": float(self.current_lng) if self.current_lng else None,
                    "name": self.current_location
                }
            },
            "schedule": {
                "etd": self.etd.isoformat() if self.etd else None,
                "eta": self.eta.isoformat() if self.eta else None
            },
            "status": {
                "code": self.status_code,
                "description": self.status_description
            },
            "flags": {
                "is_risk": self.risk_flag,
                "agent_notes": self.agent_notes
            },
            "metadata": {
                "master_bill": self.master_bill,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
        }


class AuditLog(Base):
    """
    Audit log for tracking all changes made by agents
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String, ForeignKey("shipments.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String, nullable=False)  # e.g., "UPDATE_ETA", "SET_RISK_FLAG"
    reason = Column(Text, nullable=True)  # AI's reasoning for the change
    
    # What changed
    field_name = Column(String, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent_id = Column(String, nullable=True)  # Optional: which agent made the change
    
    # Relationship
    shipment = relationship("Shipment", back_populates="audit_logs")
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "action": self.action,
            "reason": self.reason,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "agent_id": self.agent_id
        }
