"""
Alert management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.database_models import Alert, AlertAction, Camera, User, AlertLevel, AlertStatus
from app.models.schemas import (
    AlertCreate, AlertResponse, AlertWithExplanation, 
    AlertActionRequest, RiskExplanation
)
from app.core.security import get_current_user

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 50,
    status: Optional[AlertStatus] = None,
    level: Optional[AlertLevel] = None,
    camera_id: Optional[int] = None,
    hours: int = Query(default=24, description="Filter alerts from last N hours"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List alerts with optional filters."""
    query = select(Alert).options(selectinload(Alert.camera))
    
    # Apply filters
    filters = []
    if status:
        filters.append(Alert.status == status)
    if level:
        filters.append(Alert.risk_level == level)
    if camera_id:
        filters.append(Alert.camera_id == camera_id)
    
    # Time filter
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    filters.append(Alert.detected_at >= cutoff_time)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Alert.detected_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Convert to response with camera info
    response = []
    for alert in alerts:
        alert_dict = AlertResponse.model_validate(alert).model_dump()
        alert_dict["camera_name"] = alert.camera.name if alert.camera else None
        alert_dict["camera_location"] = alert.camera.location if alert.camera else None
        response.append(AlertResponse(**alert_dict))
    
    return response


@router.get("/summary")
async def get_alert_summary(
    hours: int = Query(default=24, description="Summary for last N hours"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert summary statistics."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Count by level
    result = await db.execute(
        select(Alert.risk_level, func.count(Alert.id))
        .where(Alert.detected_at >= cutoff_time)
        .group_by(Alert.risk_level)
    )
    level_counts = {row[0].value: row[1] for row in result.all()}
    
    # Count by status
    result = await db.execute(
        select(Alert.status, func.count(Alert.id))
        .where(Alert.detected_at >= cutoff_time)
        .group_by(Alert.status)
    )
    status_counts = {row[0].value: row[1] for row in result.all()}
    
    total = sum(level_counts.values())
    
    return {
        "total": total,
        "high": level_counts.get("high", 0),
        "medium": level_counts.get("medium", 0),
        "low": level_counts.get("low", 0),
        "active": status_counts.get("active", 0),
        "acknowledged": status_counts.get("acknowledged", 0),
        "false_positives": status_counts.get("false_positive", 0),
        "hours_covered": hours
    }


@router.get("/{alert_id}", response_model=AlertWithExplanation)
async def get_alert_detail(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed alert with full explanation."""
    result = await db.execute(
        select(Alert).options(selectinload(Alert.camera)).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Build detailed explanation
    # Parse the factors from the explanation (in production, store separately)
    risk_factors = parse_risk_factors(alert.explanation, alert.risk_score)
    
    response = AlertWithExplanation(
        id=alert.id,
        camera_id=alert.camera_id,
        camera_name=alert.camera.name if alert.camera else None,
        camera_location=alert.camera.location if alert.camera else None,
        detection_type=alert.detection_type,
        risk_level=alert.risk_level,
        risk_score=alert.risk_score,
        confidence=alert.confidence,
        explanation=alert.explanation,
        status=alert.status,
        detected_at=alert.detected_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        clip_path=alert.clip_path,
        thumbnail_path=alert.thumbnail_path,
        risk_factors=risk_factors,
        limitations=[
            "Cannot determine intent or context",
            "May be normal behavior misinterpreted",
            "Accuracy varies with lighting and distance",
            "Requires human verification before action"
        ]
    )
    
    return response


def parse_risk_factors(explanation: str, risk_score: float) -> List[RiskExplanation]:
    """Parse risk factors from explanation text."""
    # In production, these would be stored separately in the database
    # For now, generate based on explanation keywords
    factors = []
    
    if "crowd" in explanation.lower():
        factors.append(RiskExplanation(
            factor="crowd_density",
            weight=0.3,
            description="Elevated person count in monitored area"
        ))
    
    if "aggressive" in explanation.lower() or "posture" in explanation.lower():
        factors.append(RiskExplanation(
            factor="body_posture",
            weight=0.4,
            description="Body posture analysis indicates potential confrontation"
        ))
    
    if "loiter" in explanation.lower():
        factors.append(RiskExplanation(
            factor="loitering",
            weight=0.2,
            description="Prolonged stationary presence in area"
        ))
    
    if "motion" in explanation.lower() or "running" in explanation.lower():
        factors.append(RiskExplanation(
            factor="unusual_motion",
            weight=0.1,
            description="Movement pattern differs from baseline"
        ))
    
    return factors


@router.post("/{alert_id}/action")
async def perform_alert_action(
    alert_id: int,
    action: AlertActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Perform an action on an alert (acknowledge, mark false positive, etc.)."""
    # Get alert
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Get user ID
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update alert status based on action
    now = datetime.utcnow()
    
    if action.action_type == "acknowledge":
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = now
    elif action.action_type == "false_positive":
        alert.status = AlertStatus.FALSE_POSITIVE
        alert.resolved_at = now
    elif action.action_type == "escalate":
        alert.status = AlertStatus.ESCALATED
    elif action.action_type == "resolve":
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = now
    
    # Log action
    alert_action = AlertAction(
        alert_id=alert_id,
        user_id=user.id,
        action_type=action.action_type,
        notes=action.notes
    )
    db.add(alert_action)
    
    await db.commit()
    
    return {
        "message": f"Alert {action.action_type}d successfully",
        "alert_id": alert_id,
        "new_status": alert.status.value,
        "action_by": current_user["username"]
    }


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert (called by ML pipeline)."""
    # Verify camera exists
    result = await db.execute(select(Camera).where(Camera.id == alert_data.camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    alert = Alert(**alert_data.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    return AlertResponse.model_validate(alert)
