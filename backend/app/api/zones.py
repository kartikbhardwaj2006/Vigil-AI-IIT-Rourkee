"""
Zone management API endpoints.
Allows configuration of restricted zones and tripwires for intrusion detection.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.database_models import Zone, Camera
from app.core.security import get_current_user

router = APIRouter()


# Pydantic schemas for zones
class ZonePoint(BaseModel):
    """A point in a zone polygon."""
    x: float
    y: float


class ZoneCreate(BaseModel):
    """Schema for creating a zone."""
    camera_id: int
    name: str
    zone_type: str  # "restricted" | "tripwire" | "counting"
    polygon_points: List[ZonePoint]
    color: Optional[str] = "#ff0000"
    alert_on_enter: bool = True
    alert_on_exit: bool = False


class ZoneUpdate(BaseModel):
    """Schema for updating a zone."""
    name: Optional[str] = None
    polygon_points: Optional[List[ZonePoint]] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    alert_on_enter: Optional[bool] = None
    alert_on_exit: Optional[bool] = None


class ZoneResponse(BaseModel):
    """Schema for zone response."""
    id: int
    camera_id: int
    name: str
    zone_type: str
    polygon_points: List[dict]
    color: str
    is_active: bool
    alert_on_enter: bool
    alert_on_exit: bool
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ZoneResponse])
async def list_zones(
    camera_id: Optional[int] = None,
    zone_type: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all configured zones.
    
    Zones define areas for:
    - **restricted**: Alert when person enters
    - **tripwire**: Alert when person crosses line
    - **counting**: Count persons in area
    """
    query = select(Zone)
    
    if camera_id:
        query = query.where(Zone.camera_id == camera_id)
    if zone_type:
        query = query.where(Zone.zone_type == zone_type)
    if active_only:
        query = query.where(Zone.is_active == True)
    
    result = await db.execute(query)
    zones = result.scalars().all()
    
    return zones


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific zone by ID."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    return zone


@router.post("/", response_model=ZoneResponse)
async def create_zone(
    zone_data: ZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new zone.
    
    **Zone Types:**
    - `restricted`: Triggers alert when any person enters the polygon
    - `tripwire`: Triggers alert when person crosses the defined line
    - `counting`: Counts persons within the polygon (no alerts)
    
    **Polygon Format:**
    Points should be in normalized coordinates (0-1) relative to frame size,
    or in pixel coordinates for the target resolution.
    """
    # Verify camera exists
    camera_result = await db.execute(
        select(Camera).where(Camera.id == zone_data.camera_id)
    )
    if not camera_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Validate zone type
    valid_types = ["restricted", "tripwire", "counting"]
    if zone_data.zone_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid zone_type. Must be one of: {valid_types}"
        )
    
    # Convert points to list of dicts for JSON storage
    polygon_points = [{"x": p.x, "y": p.y} for p in zone_data.polygon_points]
    
    zone = Zone(
        camera_id=zone_data.camera_id,
        name=zone_data.name,
        zone_type=zone_data.zone_type,
        polygon_points=polygon_points,
        color=zone_data.color,
        alert_on_enter=zone_data.alert_on_enter,
        alert_on_exit=zone_data.alert_on_exit
    )
    
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    
    return zone


@router.patch("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: int,
    zone_data: ZoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a zone's configuration."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    update_data = zone_data.model_dump(exclude_unset=True)
    
    # Convert polygon points if provided
    if "polygon_points" in update_data and update_data["polygon_points"]:
        update_data["polygon_points"] = [
            {"x": p.x, "y": p.y} for p in zone_data.polygon_points
        ]
    
    for field, value in update_data.items():
        setattr(zone, field, value)
    
    await db.commit()
    await db.refresh(zone)
    
    return zone


@router.delete("/{zone_id}")
async def delete_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a zone (soft delete - sets inactive).
    
    To permanently remove, use force=true query parameter.
    """
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    # Soft delete
    zone.is_active = False
    await db.commit()
    
    return {"message": "Zone deactivated", "zone_id": zone_id}


@router.get("/camera/{camera_id}/active")
async def get_active_zones_for_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all active zones for a specific camera.
    Returns zones formatted for the video processing pipeline.
    """
    result = await db.execute(
        select(Zone)
        .where(Zone.camera_id == camera_id)
        .where(Zone.is_active == True)
    )
    zones = result.scalars().all()
    
    # Format for pipeline consumption
    formatted_zones = []
    for zone in zones:
        points = zone.polygon_points
        polygon = [(p["x"], p["y"]) for p in points] if points else []
        
        formatted_zones.append({
            "id": zone.id,
            "name": zone.name,
            "type": zone.zone_type,
            "polygon": polygon,
            "color": zone.color,
            "alert_on_enter": zone.alert_on_enter,
            "alert_on_exit": zone.alert_on_exit
        })
    
    return {
        "camera_id": camera_id,
        "zones": formatted_zones,
        "total": len(formatted_zones)
    }
