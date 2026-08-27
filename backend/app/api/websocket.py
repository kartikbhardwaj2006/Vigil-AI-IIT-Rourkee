"""
WebSocket endpoints for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "alerts": [],
            "cameras": [],
            "all": []
        }
    
    async def connect(self, websocket: WebSocket, channel: str = "all"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str = "all"):
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Broadcast message to all connections in a channel."""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn, channel)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = ConnectionManager()


@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert updates.
    
    Clients receive:
    - New alert notifications
    - Alert status updates
    - System health updates
    """
    await manager.connect(websocket, "alerts")
    
    try:
        # Send initial welcome message
        await manager.send_personal(websocket, {
            "type": "connected",
            "channel": "alerts",
            "message": "Connected to alert stream",
            "disclaimer": "All alerts require human verification"
        })
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
                
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific camera feeds
                    camera_id = message.get("camera_id")
                    await manager.send_personal(websocket, {
                        "type": "subscribed",
                        "camera_id": camera_id
                    })
                    
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "alerts")


@router.websocket("/camera/{camera_id}")
async def websocket_camera(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint for camera-specific updates.
    
    Provides real-time updates for a specific camera including:
    - Frame analysis results (anonymized)
    - Detection overlays
    - Risk score updates
    """
    channel = f"camera_{camera_id}"
    await manager.connect(websocket, channel)
    
    try:
        await manager.send_personal(websocket, {
            "type": "connected",
            "channel": channel,
            "camera_id": camera_id,
            "message": f"Connected to camera {camera_id} feed"
        })
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


async def broadcast_new_alert(alert_data: dict):
    """
    Broadcast a new alert to all connected clients.
    Called by the ML pipeline when a new alert is generated.
    """
    await manager.broadcast({
        "type": "new_alert",
        "data": alert_data,
        "disclaimer": "Automated detection - requires human verification"
    }, "alerts")


async def broadcast_alert_update(alert_id: int, status: str, updated_by: str):
    """
    Broadcast alert status update.
    """
    await manager.broadcast({
        "type": "alert_update",
        "alert_id": alert_id,
        "status": status,
        "updated_by": updated_by
    }, "alerts")


async def broadcast_camera_analysis(camera_id: str, analysis_data: dict):
    """
    Broadcast camera analysis results.
    """
    channel = f"camera_{camera_id}"
    await manager.broadcast({
        "type": "analysis",
        "camera_id": camera_id,
        "data": analysis_data
    }, channel)
