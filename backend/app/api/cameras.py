"""
Camera management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.database_models import Camera
from app.models.schemas import CameraCreate, CameraUpdate, CameraResponse
from app.core.security import get_current_user

router = APIRouter()


@router.get("/", response_model=List[CameraResponse])
async def list_cameras(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all cameras."""
    query = select(Camera)
    if active_only:
        query = query.where(Camera.is_active == True)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    cameras = result.scalars().all()
    
    return cameras


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific camera by ID."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return camera


@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new camera."""
    # Check if camera_id already exists
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_data.camera_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Camera ID already exists")
    
    camera = Camera(**camera_data.model_dump())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    
    return camera


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    update_data = camera_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    await db.commit()
    await db.refresh(camera)
    
    return camera


@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a camera (soft delete)."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    camera.is_active = False
    await db.commit()
    
    return {"message": "Camera deactivated", "camera_id": camera_id}
