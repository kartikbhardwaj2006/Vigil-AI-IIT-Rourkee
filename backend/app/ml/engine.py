"""
Video Intelligence Engine - Central orchestrator for video processing.

This module coordinates:
- Multiple camera stream management
- Frame processing through ML pipeline
- Alert generation and persistence
- WebSocket broadcasting of real-time updates

PRIVACY GUARANTEE:
- All processing happens in-memory
- No raw frames are ever stored
- Only anonymized data leaves this module
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import cv2
import numpy as np

from app.ml.pipeline import AnalysisPipeline, AnalysisResult, create_demo_pipeline
from app.ml.video_processor import VideoProcessor


@dataclass
class CameraConfig:
    """Configuration for a camera stream."""
    camera_id: str
    name: str
    source: str  # Video file, RTSP URL, or camera index
    is_sensitive_area: bool = False
    restricted_zones: List[List[tuple]] = field(default_factory=list)
    tripwires: List[tuple] = field(default_factory=list)
    enabled: bool = True


@dataclass
class CameraState:
    """Runtime state for a camera."""
    config: CameraConfig
    processor: Optional[VideoProcessor] = None
    last_frame_time: Optional[datetime] = None
    frame_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    is_connected: bool = False
    current_person_count: int = 0
    current_risk_level: str = "low"


class AlertBuffer:
    """
    Buffer to prevent alert flooding.
    Only allows one alert per event type per camera within cooldown period.
    """
    
    def __init__(self, cooldown_seconds: int = 30):
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self.last_alerts: Dict[str, datetime] = {}
    
    def can_alert(self, camera_id: str, event_type: str) -> bool:
        """Check if an alert can be generated."""
        key = f"{camera_id}:{event_type}"
        now = datetime.utcnow()
        
        if key in self.last_alerts:
            if now - self.last_alerts[key] < self.cooldown:
                return False
        
        self.last_alerts[key] = now
        return True
    
    def clear(self, camera_id: str = None):
        """Clear alert history."""
        if camera_id:
            self.last_alerts = {
                k: v for k, v in self.last_alerts.items() 
                if not k.startswith(f"{camera_id}:")
            }
        else:
            self.last_alerts.clear()


class VideoEngine:
    """
    Central video intelligence engine.
    
    Manages multiple camera streams, coordinates processing,
    and handles alert generation.
    """
    
    def __init__(
        self,
        db_session_factory=None,
        broadcast_callback=None,
        alert_cooldown: int = 30
    ):
        """
        Initialize the video engine.
        
        Args:
            db_session_factory: Async function to get database session
            broadcast_callback: Async function to broadcast alerts via WebSocket
            alert_cooldown: Seconds between alerts of same type per camera
        """
        self.cameras: Dict[str, CameraState] = {}
        self.pipeline: Optional[AnalysisPipeline] = None
        self.alert_buffer = AlertBuffer(alert_cooldown)
        
        self._db_session_factory = db_session_factory
        self._broadcast_callback = broadcast_callback
        
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        
        # Performance metrics
        self._total_frames_processed = 0
        self._total_alerts_generated = 0
        self._start_time: Optional[datetime] = None
    
    async def initialize(self):
        """Initialize the engine and load ML models."""
        try:
            self.pipeline = create_demo_pipeline()
            self._start_time = datetime.utcnow()
            print("✅ Video Engine initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Video Engine: {e}")
            return False
    
    def add_camera(self, config: CameraConfig):
        """Add a camera to be monitored."""
        state = CameraState(config=config)
        self.cameras[config.camera_id] = state
        print(f"📷 Added camera: {config.camera_id} ({config.name})")
    
    def remove_camera(self, camera_id: str):
        """Remove a camera from monitoring."""
        if camera_id in self.cameras:
            # Stop processing task if running
            if camera_id in self._tasks:
                self._tasks[camera_id].cancel()
                del self._tasks[camera_id]
            
            # Close processor
            state = self.cameras[camera_id]
            if state.processor:
                state.processor.close()
            
            del self.cameras[camera_id]
            print(f"📷 Removed camera: {camera_id}")
    
    async def start(self):
        """Start processing all cameras."""
        if self._running:
            return
        
        self._running = True
        
        for camera_id, state in self.cameras.items():
            if state.config.enabled:
                task = asyncio.create_task(
                    self._process_camera_loop(camera_id)
                )
                self._tasks[camera_id] = task
        
        print(f"🚀 Video Engine started with {len(self._tasks)} cameras")
    
    async def stop(self):
        """Stop processing all cameras."""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        
        self._tasks.clear()
        
        # Close resources
        if self.pipeline:
            self.pipeline.close()
        
        for state in self.cameras.values():
            if state.processor:
                state.processor.close()
        
        print("🛑 Video Engine stopped")
    
    async def _process_camera_loop(self, camera_id: str):
        """Main processing loop for a camera."""
        state = self.cameras.get(camera_id)
        if not state:
            return
        
        config = state.config
        
        # Initialize video processor
        state.processor = VideoProcessor(config.source)
        
        try:
            if not state.processor.open():
                state.is_connected = False
                state.last_error = "Failed to open video source"
                return
            
            state.is_connected = True
            
            while self._running:
                try:
                    # Get frame
                    result = state.processor.get_single_frame()
                    if result is None:
                        await asyncio.sleep(0.1)
                        continue
                    
                    frame, timestamp = result
                    
                    # Process through pipeline
                    if self.pipeline:
                        analysis = self.pipeline.analyze_frame(
                            frame,
                            camera_id,
                            is_sensitive_area=config.is_sensitive_area,
                            timestamp=timestamp
                        )
                        
                        # Update state
                        state.frame_count += 1
                        state.last_frame_time = timestamp
                        state.current_person_count = analysis.person_count
                        state.current_risk_level = analysis.risk_assessment.level.value
                        
                        self._total_frames_processed += 1
                        
                        # Check for alerts
                        if self.pipeline.should_generate_alert(analysis):
                            await self._handle_alert(camera_id, analysis)
                        
                        # Check zone intrusions
                        await self._check_zone_intrusions(camera_id, analysis, config)
                    
                    # Control processing rate (~15 FPS)
                    await asyncio.sleep(0.066)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    state.error_count += 1
                    state.last_error = str(e)
                    await asyncio.sleep(1)  # Back off on error
                    
        finally:
            state.is_connected = False
            if state.processor:
                state.processor.close()
    
    async def _check_zone_intrusions(
        self, 
        camera_id: str, 
        analysis: AnalysisResult,
        config: CameraConfig
    ):
        """Check if any detected persons are in restricted zones."""
        if not config.restricted_zones:
            return
        
        for detection in analysis.detections:
            if detection.get("class_name") != "person":
                continue
            
            bbox = detection.get("bbox", [])
            if len(bbox) < 4:
                continue
            
            # Calculate center point of detection
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            
            # Check each restricted zone
            for zone_idx, zone in enumerate(config.restricted_zones):
                if self._point_in_polygon(cx, cy, zone):
                    if self.alert_buffer.can_alert(camera_id, f"intrusion_zone_{zone_idx}"):
                        await self._create_intrusion_alert(
                            camera_id,
                            zone_idx,
                            analysis.timestamp
                        )
    
    @staticmethod
    def _point_in_polygon(x: float, y: float, polygon: List[tuple]) -> bool:
        """Ray casting algorithm to check point in polygon."""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    async def _handle_alert(self, camera_id: str, analysis: AnalysisResult):
        """Handle potential alert from analysis result."""
        event_type = self._determine_event_type(analysis)
        
        if not self.alert_buffer.can_alert(camera_id, event_type):
            return
        
        await self._create_alert(
            camera_id=camera_id,
            event_type=event_type,
            analysis=analysis
        )
    
    def _determine_event_type(self, analysis: AnalysisResult) -> str:
        """Determine the primary event type from analysis."""
        if analysis.crowd_density > 0.7:
            return "crowd_formation"
        if len(analysis.loitering_detections) > 0:
            return "loitering"
        if len(analysis.aggressive_interactions) > 0:
            return "aggressive_posture"
        return "elevated_risk"
    
    async def _create_alert(
        self,
        camera_id: str,
        event_type: str,
        analysis: AnalysisResult
    ):
        """Create and persist an alert."""
        alert_data = {
            "camera_id": camera_id,
            "event_type": event_type,
            "timestamp": analysis.timestamp.isoformat(),
            "person_count": analysis.person_count,
            "risk_level": analysis.risk_assessment.level.value,
            "risk_score": analysis.risk_assessment.score,
            "explanation": analysis.risk_assessment.explanation,
            "factors": [f.to_dict() for f in analysis.risk_assessment.factors],
            "requires_review": True,
            "disclaimer": "Automated detection - requires human verification"
        }
        
        # Persist to database
        if self._db_session_factory:
            await self._persist_alert(alert_data)
        
        # Broadcast via WebSocket
        if self._broadcast_callback:
            await self._broadcast_callback(alert_data)
        
        self._total_alerts_generated += 1
        print(f"⚠️ Alert generated: {event_type} on {camera_id}")
    
    async def _create_intrusion_alert(
        self,
        camera_id: str,
        zone_index: int,
        timestamp: datetime
    ):
        """Create intrusion-specific alert."""
        alert_data = {
            "camera_id": camera_id,
            "event_type": "zone_intrusion",
            "timestamp": timestamp.isoformat(),
            "zone_index": zone_index,
            "risk_level": "high",
            "explanation": f"Person detected in restricted zone {zone_index}",
            "requires_review": True,
            "disclaimer": "Automated detection - requires human verification"
        }
        
        if self._db_session_factory:
            await self._persist_alert(alert_data)
        
        if self._broadcast_callback:
            await self._broadcast_callback(alert_data)
        
        self._total_alerts_generated += 1
        print(f"🚨 Intrusion alert: Zone {zone_index} on {camera_id}")
    
    async def _persist_alert(self, alert_data: dict):
        """Persist alert to database."""
        try:
            from app.models.database_models import Alert
            
            async with self._db_session_factory() as session:
                alert = Alert(
                    camera_id=alert_data.get("camera_id"),
                    event_type=alert_data.get("event_type"),
                    risk_level=alert_data.get("risk_level", "medium"),
                    risk_score=alert_data.get("risk_score", 0.5),
                    person_count=alert_data.get("person_count", 0),
                    explanation=alert_data.get("explanation", ""),
                    status="pending_review"
                )
                session.add(alert)
                await session.commit()
        except Exception as e:
            print(f"Failed to persist alert: {e}")
    
    def get_camera_status(self, camera_id: str) -> Optional[dict]:
        """Get current status of a camera."""
        state = self.cameras.get(camera_id)
        if not state:
            return None
        
        return {
            "camera_id": camera_id,
            "name": state.config.name,
            "is_connected": state.is_connected,
            "frame_count": state.frame_count,
            "last_frame_time": state.last_frame_time.isoformat() if state.last_frame_time else None,
            "current_person_count": state.current_person_count,
            "current_risk_level": state.current_risk_level,
            "error_count": state.error_count,
            "last_error": state.last_error
        }
    
    def get_all_camera_status(self) -> List[dict]:
        """Get status of all cameras."""
        return [
            self.get_camera_status(camera_id)
            for camera_id in self.cameras
        ]
    
    def get_engine_stats(self) -> dict:
        """Get engine performance statistics."""
        uptime = None
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        pipeline_stats = {}
        if self.pipeline:
            pipeline_stats = self.pipeline.get_performance_stats()
        
        return {
            "running": self._running,
            "uptime_seconds": uptime,
            "total_cameras": len(self.cameras),
            "active_cameras": len(self._tasks),
            "total_frames_processed": self._total_frames_processed,
            "total_alerts_generated": self._total_alerts_generated,
            "pipeline": pipeline_stats
        }


# Global engine instance
_engine: Optional[VideoEngine] = None


def get_engine() -> Optional[VideoEngine]:
    """Get the global engine instance."""
    return _engine


async def initialize_engine(db_session_factory=None, broadcast_callback=None):
    """Initialize the global engine instance."""
    global _engine
    _engine = VideoEngine(db_session_factory, broadcast_callback)
    await _engine.initialize()
    return _engine
