"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"


class AlertLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# Camera Schemas
class CameraBase(BaseModel):
    camera_id: str
    name: str
    location: Optional[str] = None
    stream_url: Optional[str] = None
    is_sensitive_area: bool = False


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    stream_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_sensitive_area: Optional[bool] = None


class CameraResponse(CameraBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Alert Schemas
class RiskExplanation(BaseModel):
    """Individual risk factor explanation."""
    factor: str
    weight: float
    description: str


class AlertBase(BaseModel):
    detection_type: str
    risk_level: AlertLevel
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    explanation: str


class AlertCreate(AlertBase):
    camera_id: int
    clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


class AlertResponse(AlertBase):
    id: int
    camera_id: int
    status: AlertStatus
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    clip_path: Optional[str]
    thumbnail_path: Optional[str]
    
    # Additional context
    camera_name: Optional[str] = None
    camera_location: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertWithExplanation(AlertResponse):
    """Extended alert with detailed explanations."""
    risk_factors: List[RiskExplanation] = []
    limitations: List[str] = [
        "Cannot determine intent",
        "May be normal behavior",
        "Requires human verification"
    ]
    disclaimer: str = "This is an automated indicator. Human verification required."


class AlertActionRequest(BaseModel):
    action_type: str  # acknowledge, false_positive, escalate
    notes: Optional[str] = None


# Audit Log Schemas
class AuditLogBase(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    justification: Optional[str] = None


class DeAnonymizationRequest(BaseModel):
    camera_id: int
    alert_id: Optional[int] = None
    justification: str = Field(min_length=10, description="Must provide detailed justification")
    duration_minutes: int = Field(default=5, ge=1, le=30)


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int
    username: Optional[str] = None
    approved_by: Optional[int] = None
    access_granted_until: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Analytics Schemas
class AlertSummary(BaseModel):
    total: int
    high: int
    medium: int
    low: int
    active: int
    acknowledged: int
    false_positives: int


class CameraSummary(BaseModel):
    total: int
    active: int
    inactive: int


class DashboardStats(BaseModel):
    alerts: AlertSummary
    cameras: CameraSummary
    system_health: str = "operational"


# Risk Assessment Schemas (for ML pipeline)
class Detection(BaseModel):
    """Single detection from ML model."""
    bbox: List[float]  # [x1, y1, x2, y2]
    class_name: str
    confidence: float
    track_id: Optional[int] = None


class FrameAnalysis(BaseModel):
    """Analysis result for a single frame."""
    timestamp: datetime
    camera_id: str
    person_count: int
    detections: List[Detection]
    poses_detected: int = 0
    motion_level: float = 0.0


class RiskAssessment(BaseModel):
    """Final risk assessment output."""
    level: AlertLevel
    score: float
    confidence: float
    explanations: List[str]
    factors: List[RiskExplanation]
    disclaimer: str = "This is an automated indicator. Human verification required."
