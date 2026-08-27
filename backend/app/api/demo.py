"""
Demo and simulation endpoints for hackathon demonstration.

These endpoints allow testing without real cameras:
- Simulate alerts
- Generate test data
- Demo mode controls
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
import random

from app.core.security import get_current_user

router = APIRouter()


# Simulated event types for demo
DEMO_EVENTS = [
    {
        "event_type": "crowd_formation",
        "description": "Elevated crowd density detected",
        "risk_level": "medium",
        "person_count": 18
    },
    {
        "event_type": "zone_intrusion",
        "description": "Person detected in restricted area",
        "risk_level": "high",
        "person_count": 1
    },
    {
        "event_type": "loitering",
        "description": "Prolonged stationary presence detected",
        "risk_level": "low",
        "person_count": 2
    },
    {
        "event_type": "aggressive_posture",
        "description": "Potentially aggressive body posture detected",
        "risk_level": "medium",
        "person_count": 2
    }
]


@router.post("/simulate-alert")
async def simulate_alert(
    event_type: Optional[str] = None,
    camera_id: str = "demo-cam-1",
    current_user: dict = Depends(get_current_user)
):
    """
    Simulate an alert for demo purposes.
    
    **Event Types:**
    - `crowd_formation` - Crowd density threshold exceeded
    - `zone_intrusion` - Person in restricted area
    - `loitering` - Prolonged stationary presence
    - `aggressive_posture` - Potentially aggressive posture
    
    Leave event_type empty for a random event.
    """
    # Select event
    if event_type:
        event = next(
            (e for e in DEMO_EVENTS if e["event_type"] == event_type),
            DEMO_EVENTS[0]
        )
    else:
        event = random.choice(DEMO_EVENTS)
    
    alert_data = {
        "id": random.randint(1000, 9999),
        "camera_id": camera_id,
        "event_type": event["event_type"],
        "description": event["description"],
        "risk_level": event["risk_level"],
        "risk_score": round(random.uniform(0.4, 0.9), 2),
        "person_count": event["person_count"],
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending_review",
        "is_demo": True,
        "disclaimer": "DEMO ALERT - This is simulated data for demonstration purposes"
    }
    
    # Broadcast via WebSocket if available
    try:
        from app.api.websocket import broadcast_new_alert
        import asyncio
        asyncio.create_task(broadcast_new_alert(alert_data))
    except Exception:
        pass
    
    return {
        "success": True,
        "message": "Demo alert created",
        "alert": alert_data
    }


@router.post("/simulate-crowd")
async def simulate_crowd(
    person_count: int = 20,
    camera_id: str = "demo-cam-1",
    current_user: dict = Depends(get_current_user)
):
    """
    Simulate a crowd detection event.
    
    Args:
        person_count: Number of persons to simulate (triggers alert if > 15)
        camera_id: Camera to associate with the event
    """
    is_alert = person_count > 15
    risk_level = "high" if person_count > 25 else ("medium" if person_count > 15 else "low")
    
    result = {
        "camera_id": camera_id,
        "person_count": person_count,
        "crowd_threshold": 15,
        "is_crowd": is_alert,
        "risk_level": risk_level,
        "timestamp": datetime.utcnow().isoformat(),
        "is_demo": True
    }
    
    if is_alert:
        await simulate_alert("crowd_formation", camera_id, current_user)
    
    return result


@router.post("/simulate-intrusion")
async def simulate_intrusion(
    zone_name: str = "Restricted Area A",
    camera_id: str = "demo-cam-1",
    current_user: dict = Depends(get_current_user)
):
    """
    Simulate a zone intrusion event.
    """
    alert_data = {
        "id": random.randint(1000, 9999),
        "camera_id": camera_id,
        "event_type": "zone_intrusion",
        "zone_name": zone_name,
        "description": f"Person detected in {zone_name}",
        "risk_level": "high",
        "risk_score": 0.85,
        "person_count": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending_review",
        "is_demo": True,
        "disclaimer": "DEMO ALERT - This is simulated data"
    }
    
    # Broadcast
    try:
        from app.api.websocket import broadcast_new_alert
        import asyncio
        asyncio.create_task(broadcast_new_alert(alert_data))
    except Exception:
        pass
    
    return {
        "success": True,
        "message": "Intrusion alert simulated",
        "alert": alert_data
    }


@router.get("/sample-cameras")
async def get_sample_cameras():
    """
    Get a list of sample cameras for demo.
    These can be used to simulate a multi-camera setup.
    """
    return {
        "cameras": [
            {
                "camera_id": "demo-cam-1",
                "name": "Main Entrance",
                "location": "Building A - Front",
                "status": "active",
                "is_demo": True
            },
            {
                "camera_id": "demo-cam-2",
                "name": "Parking Lot",
                "location": "Lot B - East",
                "status": "active",
                "is_demo": True
            },
            {
                "camera_id": "demo-cam-3",
                "name": "Main Hall",
                "location": "Building A - Center",
                "status": "active",
                "is_demo": True
            },
            {
                "camera_id": "demo-cam-4",
                "name": "Emergency Exit",
                "location": "Building A - Rear",
                "status": "active",
                "is_demo": True
            }
        ],
        "disclaimer": "Demo cameras - No real video feeds"
    }


@router.get("/status")
async def demo_status():
    """Get demo mode status and capabilities."""
    return {
        "demo_mode": True,
        "features": {
            "simulated_alerts": True,
            "sample_cameras": True,
            "mjpeg_stream": True,
            "websocket": True
        },
        "limitations": [
            "No real video processing",
            "Alerts are simulated",
            "No actual anonymization (demo frames shown)"
        ],
        "disclaimer": "This is a demonstration system. Not for production use."
    }
