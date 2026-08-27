"""
WebSocket endpoints for real-time camera statistics.
Streams detection counts and risk levels to frontend.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
import cv2
import os
from pathlib import Path

router = APIRouter()

# Import video mapping
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEMO_VIDEOS_PATH = PROJECT_ROOT / "demo-videos"

CAMERA_VIDEO_MAP = {
    "video1": str(DEMO_VIDEOS_PATH / "video1.mp4"),
    "video2": str(DEMO_VIDEOS_PATH / "video2.mp4"),
    "video3": str(DEMO_VIDEOS_PATH / "video3.mp4"),
    "video4": str(DEMO_VIDEOS_PATH / "video4.mp4"),
    "video5": str(DEMO_VIDEOS_PATH / "video5.mp4"),
}


class StatsConnectionManager:
    """Manages WebSocket connections for camera stats."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, camera_id: str):
        await websocket.accept()
        self.active_connections[camera_id] = websocket
    
    def disconnect(self, camera_id: str):
        if camera_id in self.active_connections:
            del self.active_connections[camera_id]
    
    async def send_stats(self, camera_id: str, stats: dict):
        if camera_id in self.active_connections:
            try:
                await self.active_connections[camera_id].send_json(stats)
            except:
                self.disconnect(camera_id)


stats_manager = StatsConnectionManager()


@router.websocket("/camera/{camera_id}/stats")
async def websocket_camera_stats(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint for real-time camera statistics.
    
    Streams detection data every frame:
    - person_count: Number of people detected
    - bag_count: Number of bags/backpacks detected
    - risk_level: "low" | "medium" | "high"
    """
    await stats_manager.connect(websocket, camera_id)
    
    # Get pipeline and video source
    from app.ml.pipeline_manager import get_pipeline as get_shared_pipeline
    from app.ml.pipeline_manager import analyze_frame as analyze_frame_safe
    from app.ml.pipeline_manager import get_privacy_state

    pipeline = get_shared_pipeline()
    
    # Get video source
    video_source = CAMERA_VIDEO_MAP.get(camera_id)
    if not video_source or not os.path.exists(video_source):
        await websocket.send_json({"error": f"Video not found for camera {camera_id}"})
        return
    
    cap = cv2.VideoCapture(video_source)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "camera_id": camera_id,
            "message": f"Streaming stats for {camera_id}"
        })
        
        frame_count = 0
        fps_target = 2  # Send stats 2 times per second
        frame_delay = 1.0 / fps_target
        
        while True:
            # Non-blocking capture: run OpenCV read in a worker thread.
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_count += 1
            
            # Analyze frame with pipeline
            stats = {
                "person_count": 0,
                "bag_count": 0,
                "risk_level": "low",
                "frame_number": frame_count,
                "metrics": {},
                "privacy": {},
            }
            
            if frame is not None:
                try:
                    if pipeline is None:
                        pipeline = get_shared_pipeline()
                    result = await asyncio.to_thread(analyze_frame_safe, frame, camera_id, False, None)
                    if result is None:
                        raise RuntimeError("Pipeline unavailable")
                    privacy_state = get_privacy_state()
                    stats = {
                        "person_count": result.person_count,
                        "bag_count": result.bag_count,
                        "risk_level": result.risk_assessment.level.value,
                        "crowd_density": result.crowd_density,
                        "frame_number": frame_count,
                        "metrics": result.runtime_metrics or {},
                        "privacy": {
                            "anonymization_enabled": bool(privacy_state.anonymization_enabled),
                            "blur_intensity": int(privacy_state.blur_intensity),
                            "blur_level": privacy_state.blur_level,
                        },
                    }
                except Exception as e:
                    print(f"Pipeline error: {e}")
            
            # Send stats
            await stats_manager.send_stats(camera_id, stats)
            
            # Control rate
            await asyncio.sleep(frame_delay)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from {camera_id} stats")
    except Exception as e:
        print(f"Error in stats stream: {e}")
    finally:
        if cap:
            cap.release()
        stats_manager.disconnect(camera_id)
