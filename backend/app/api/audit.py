"""
Audit log API endpoints for accountability and transparency.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.database_models import AuditLog, User, UserRole
from app.models.schemas import AuditLogResponse, DeAnonymizationRequest
from app.core.security import get_current_user

router = APIRouter()


async def log_audit_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    justification: str = None,
    approved_by: int = None,
    access_granted_until: datetime = None,
    request: Request = None
):
    """Helper to create audit log entries."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        justification=justification,
        approved_by=approved_by,
        access_granted_until=access_granted_until,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(log)
    return log


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List audit logs (supervisor and auditor only).
    
    Shows all sensitive actions including de-anonymization requests,
    access grants, and user management.
    """
    # Check permissions
    if current_user["role"] not in ["supervisor", "auditor"]:
        raise HTTPException(
            status_code=403, 
            detail="Audit logs are only accessible to supervisors and auditors"
        )
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = select(AuditLog).options(selectinload(AuditLog.user))
    
    filters = [AuditLog.created_at >= cutoff]
    if action:
        filters.append(AuditLog.action == action)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    
    query = query.where(and_(*filters)).order_by(AuditLog.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    response = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "justification": log.justification,
            "approved_by": log.approved_by,
            "access_granted_until": log.access_granted_until,
            "created_at": log.created_at
        }
        response.append(AuditLogResponse(**log_dict))
    
    return response


@router.post("/de-anonymization-request")
async def request_de_anonymization(
    request_data: DeAnonymizationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Request de-anonymization access.
    
    This requires justification and creates an audit trail.
    Supervisors can auto-approve, operators need supervisor approval.
    """
    # Get user
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Supervisors can auto-approve
    is_auto_approved = current_user["role"] == "supervisor"
    
    access_granted_until = None
    if is_auto_approved:
        access_granted_until = datetime.utcnow() + timedelta(minutes=request_data.duration_minutes)
    
    # Create audit log
    await log_audit_action(
        db=db,
        user_id=user.id,
        action="DE_ANONYMIZATION_REQUEST",
        resource_type="camera",
        resource_id=request_data.camera_id,
        justification=request_data.justification,
        approved_by=user.id if is_auto_approved else None,
        access_granted_until=access_granted_until,
        request=request
    )
    
    await db.commit()
    
    if is_auto_approved:
        return {
            "status": "approved",
            "message": "De-anonymization access granted",
            "access_expires_at": access_granted_until.isoformat(),
            "camera_id": request_data.camera_id,
            "disclaimer": "All de-anonymized access is logged. Use responsibly."
        }
    else:
        return {
            "status": "pending",
            "message": "De-anonymization request submitted for supervisor approval",
            "camera_id": request_data.camera_id,
            "justification_recorded": True
        }


@router.post("/de-anonymization-approve/{log_id}")
async def approve_de_anonymization(
    log_id: int,
    duration_minutes: int = Query(default=5, ge=1, le=30),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Approve a de-anonymization request (supervisor only).
    """
    if current_user["role"] != "supervisor":
        raise HTTPException(status_code=403, detail="Only supervisors can approve requests")
    
    # Get the request log
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if log.approved_by is not None:
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Get approving user
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    approver = user_result.scalar_one_or_none()
    
    # Update the log with approval
    log.approved_by = approver.id
    log.access_granted_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    # Create approval log
    await log_audit_action(
        db=db,
        user_id=approver.id,
        action="DE_ANONYMIZATION_APPROVED",
        resource_type="audit_log",
        resource_id=log_id,
        request=request
    )
    
    await db.commit()
    
    return {
        "status": "approved",
        "message": "De-anonymization request approved",
        "original_requestor_id": log.user_id,
        "access_expires_at": log.access_granted_until.isoformat(),
        "approved_by": current_user["username"]
    }


@router.get("/summary")
async def get_audit_summary(
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get audit log summary statistics."""
    if current_user["role"] not in ["supervisor", "auditor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .where(AuditLog.created_at >= cutoff)
        .group_by(AuditLog.action)
    )
    
    from sqlalchemy import func
    
    actions = {row[0]: row[1] for row in result.all()}
    
    return {
        "days_covered": days,
        "action_counts": actions,
        "total_actions": sum(actions.values())
    }
