"""
Analytics and dashboard statistics API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.db.database import get_db
from app.models.database_models import Alert, Camera, User, AlertLevel, AlertStatus
from app.models.schemas import DashboardStats, AlertSummary, CameraSummary
from app.core.security import get_current_user

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard overview statistics."""
    # Alert stats (last 24 hours)
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    # Count alerts by level
    result = await db.execute(
        select(Alert.risk_level, func.count(Alert.id))
        .where(Alert.detected_at >= cutoff)
        .group_by(Alert.risk_level)
    )
    level_counts = {row[0].value if row[0] else "unknown": row[1] for row in result.all()}
    
    # Count alerts by status
    result = await db.execute(
        select(Alert.status, func.count(Alert.id))
        .where(Alert.detected_at >= cutoff)
        .group_by(Alert.status)
    )
    status_counts = {row[0].value if row[0] else "unknown": row[1] for row in result.all()}
    
    # Camera stats
    result = await db.execute(select(func.count(Camera.id)))
    total_cameras = result.scalar() or 0
    
    result = await db.execute(select(func.count(Camera.id)).where(Camera.is_active == True))
    active_cameras = result.scalar() or 0
    
    return DashboardStats(
        alerts=AlertSummary(
            total=sum(level_counts.values()),
            high=level_counts.get("high", 0),
            medium=level_counts.get("medium", 0),
            low=level_counts.get("low", 0),
            active=status_counts.get("active", 0),
            acknowledged=status_counts.get("acknowledged", 0),
            false_positives=status_counts.get("false_positive", 0)
        ),
        cameras=CameraSummary(
            total=total_cameras,
            active=active_cameras,
            inactive=total_cameras - active_cameras
        ),
        system_health="operational"
    )


@router.get("/timeline")
async def get_alert_timeline(
    hours: int = Query(default=24, le=168),
    interval: str = Query(default="hour", pattern="^(hour|day)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert counts over time for charting."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all alerts in timeframe
    result = await db.execute(
        select(Alert.detected_at, Alert.risk_level)
        .where(Alert.detected_at >= cutoff)
        .order_by(Alert.detected_at)
    )
    alerts = result.all()
    
    # Group by interval
    timeline = {}
    for detected_at, level in alerts:
        if interval == "hour":
            key = detected_at.strftime("%Y-%m-%d %H:00")
        else:
            key = detected_at.strftime("%Y-%m-%d")
        
        if key not in timeline:
            timeline[key] = {"high": 0, "medium": 0, "low": 0, "total": 0}
        
        timeline[key][level.value] += 1
        timeline[key]["total"] += 1
    
    return {
        "interval": interval,
        "hours_covered": hours,
        "data": timeline
    }


@router.get("/camera-stats")
async def get_camera_stats(
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert counts by camera."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(Camera.id, Camera.name, Camera.location, func.count(Alert.id).label("alert_count"))
        .outerjoin(Alert, (Alert.camera_id == Camera.id) & (Alert.detected_at >= cutoff))
        .where(Camera.is_active == True)
        .group_by(Camera.id, Camera.name, Camera.location)
        .order_by(func.count(Alert.id).desc())
    )
    
    cameras = []
    for row in result.all():
        cameras.append({
            "id": row.id,
            "name": row.name,
            "location": row.location,
            "alert_count": row.alert_count
        })
    
    return {
        "hours_covered": hours,
        "cameras": cameras
    }


@router.get("/detection-types")
async def get_detection_type_stats(
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert counts by detection type."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(Alert.detection_type, func.count(Alert.id))
        .where(Alert.detected_at >= cutoff)
        .group_by(Alert.detection_type)
        .order_by(func.count(Alert.id).desc())
    )
    
    types = {row[0]: row[1] for row in result.all()}
    
    return {
        "hours_covered": hours,
        "detection_types": types
    }
