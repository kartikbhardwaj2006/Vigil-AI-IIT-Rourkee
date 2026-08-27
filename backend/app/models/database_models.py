"""
SQLAlchemy models for VIGIL database.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration."""
    VIEWER = "viewer"
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"


class AlertLevel(str, enum.Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")
    alert_actions = relationship("AlertAction", back_populates="user")


class Camera(Base):
    """Camera/video source model."""
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    stream_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_sensitive_area = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    alerts = relationship("Alert", back_populates="camera")


class Alert(Base):
    """Alert model for risk detections."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    
    # Risk assessment
    risk_level = Column(Enum(AlertLevel), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Detection details
    detection_type = Column(String(50), nullable=False)  # crowd, loitering, aggressive, etc.
    explanation = Column(Text, nullable=False)  # Human-readable explanation
    
    # Status tracking
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    
    # Video reference
    clip_path = Column(String(500))  # Path to anonymized video clip
    thumbnail_path = Column(String(500))
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    camera = relationship("Camera", back_populates="alerts")
    actions = relationship("AlertAction", back_populates="alert")


class AlertAction(Base):
    """Actions taken on alerts (audit trail)."""
    __tablename__ = "alert_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action_type = Column(String(50), nullable=False)  # acknowledge, false_positive, escalate, etc.
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    alert = relationship("Alert", back_populates="actions")
    user = relationship("User", back_populates="alert_actions")


class AuditLog(Base):
    """Audit log for all sensitive actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))  # camera, alert, user, etc.
    resource_id = Column(Integer)
    
    # For de-anonymization requests
    justification = Column(Text)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    access_granted_until = Column(DateTime(timezone=True), nullable=True)
    
    # Request details
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])


class DetectionConfig(Base):
    """Configuration for detection rules."""
    __tablename__ = "detection_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # Thresholds
    crowd_threshold = Column(Integer, default=15)
    loiter_threshold_minutes = Column(Integer, default=5)
    motion_sensitivity = Column(Float, default=2.0)
    
    # Weights for risk calculation
    crowd_weight = Column(Float, default=0.3)
    aggressive_weight = Column(Float, default=0.4)
    loiter_weight = Column(Float, default=0.2)
    motion_weight = Column(Float, default=0.1)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Zone(Base):
    """Zone model for restricted areas and tripwires."""
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50), nullable=False)  # restricted, tripwire, counting
    polygon_points = Column(JSON)  # List of {x, y} points
    color = Column(String(20), default="#ff0000")
    is_active = Column(Boolean, default=True)
    alert_on_enter = Column(Boolean, default=True)
    alert_on_exit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    camera = relationship("Camera", backref="zones")

