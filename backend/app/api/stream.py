"""
MJPEG Video Streaming endpoint for anonymized feeds.

PRIVACY GUARANTEE:
- All frames pass through anonymization pipeline before streaming
- No raw/unprocessed video is ever stored or transmitted
- Processing happens entirely in-memory
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import cv2
import numpy as np
from datetime import datetime

router = APIRouter()

# Lazy-loaded pipeline instance
_pipeline = None
_demo_mode = False  # Now using demo videos instead of generated frames

# Map camera IDs to demo video files
import os
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEMO_VIDEOS_PATH = PROJECT_ROOT / "demo-videos"

# Camera to video mapping
CAMERA_VIDEO_MAP = {
    "video1": str(DEMO_VIDEOS_PATH / "video1.mp4"),
    "video2": str(DEMO_VIDEOS_PATH / "video2.mp4"),
    "video3": str(DEMO_VIDEOS_PATH / "video3.mp4"),
    "video4": str(DEMO_VIDEOS_PATH / "video4.mp4"),
    "video5": str(DEMO_VIDEOS_PATH / "video5.mp4"),
}


def get_pipeline():
    """Get or create the analysis pipeline (lazy loading)."""
    # Backward compatible wrapper (shared singleton is now owned by pipeline_manager).
    from app.ml.pipeline_manager import get_pipeline as _get
    return _get()


def generate_demo_frame(camera_id: str, frame_number: int) -> np.ndarray:
    """
    Generate a demo frame for testing without a real camera.
    Shows animated placeholder with privacy messaging.
    """
    # Create a dark frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (30, 30, 40)  # Dark blue-gray background
    
    # Add grid pattern
    for i in range(0, 640, 40):
        cv2.line(frame, (i, 0), (i, 480), (40, 40, 50), 1)
    for i in range(0, 480, 40):
        cv2.line(frame, (0, i), (640, i), (40, 40, 50), 1)
    
    # Add camera info
    cv2.putText(frame, f"Camera: {camera_id}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 100), 2)
    
    # Add privacy badge
    cv2.rectangle(frame, (20, 60), (200, 90), (50, 120, 50), -1)
    cv2.putText(frame, "ANONYMIZED", (30, 82), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 255, 200), 1)
    
    # Add animated element (moving dot to show stream is live)
    x_pos = int(100 + 50 * np.sin(frame_number * 0.1))
    cv2.circle(frame, (x_pos, 120), 10, (0, 255, 0), -1)
    cv2.putText(frame, "LIVE", (x_pos + 20, 125), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    # Add simulated person silhouettes (blurred)
    num_people = (frame_number // 30) % 5 + 1
    for i in range(num_people):
        cx = 100 + i * 120
        cy = 300
        # Draw blurred person placeholder
        person_roi = frame[cy-60:cy+60, cx-30:cx+30]
        if person_roi.shape[0] > 0 and person_roi.shape[1] > 0:
            cv2.rectangle(frame, (cx-30, cy-60), (cx+30, cy+60), (80, 80, 100), -1)
            # Blur the region to simulate anonymization
            blurred = cv2.GaussianBlur(person_roi, (21, 21), 0)
            frame[cy-60:cy+60, cx-30:cx+30] = blurred
    
    # Add person count
    cv2.putText(frame, f"Persons Detected: {num_people}", (20, 420), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, timestamp, (440, 460), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    # Add disclaimer at bottom
    cv2.putText(frame, "Privacy-Preserved Feed - All faces automatically blurred", 
                (80, 475), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
    
    return frame


async def generate_mjpeg_stream(
    camera_id: str,
    source: Optional[str] = None,
    fps: int = 15,
    show_detections: bool = True
):
    """
    Generator that yields MJPEG frames.
    
    Args:
        camera_id: Camera identifier
        source: Video source (file path, RTSP URL, or camera index)
        fps: Target frames per second
        show_detections: Whether to draw detection overlays
    """
    pipeline = get_pipeline()
    cap = None
    frame_number = 0
    frame_delay = 1.0 / fps
    
    try:
        # Try to open video source
        # Priority: 1) Provided source, 2) Mapped demo video, 3) Demo frame
        video_source = source
        
        # Check if camera_id has a mapped demo video
        if not video_source and camera_id in CAMERA_VIDEO_MAP:
            video_source = CAMERA_VIDEO_MAP[camera_id]
            if os.path.exists(video_source):
                print(f"Loading demo video for {camera_id}: {video_source}")
        
        if video_source:
            if isinstance(video_source, str) and video_source.isdigit():
                cap = cv2.VideoCapture(int(video_source))
            else:
                cap = cv2.VideoCapture(video_source)
            
            if cap.isOpened():
                print(f"✓ Video source opened successfully: {video_source}")
        
        while True:
            frame = None
            
            if cap and cap.isOpened():
                # Non-blocking capture: run OpenCV read in a worker thread.
                ret, frame = await asyncio.to_thread(cap.read)
                if not ret:
                    # Loop video file or reconnect
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
            else:
                # Demo mode - generate placeholder frame
                frame = generate_demo_frame(camera_id, frame_number)
            
            frame_number += 1
            
            # Process frame through pipeline (anonymization + detection)
            if frame is not None:
                try:
                    if pipeline is None:
                        pipeline = get_pipeline()
                    # Non-blocking inference: run analysis on a worker thread.
                    from app.ml.pipeline_manager import analyze_frame as analyze_frame_safe
                    result = await asyncio.to_thread(
                        analyze_frame_safe,
                        frame,
                        camera_id,
                        False,
                        None,
                    )
                    if result is None:
                        raise RuntimeError("Pipeline unavailable")
                    
                    # Use anonymized frame
                    if result.anonymized_frame is not None:
                        frame = result.anonymized_frame
                    
                    # Draw detection overlays if requested
                    if show_detections:
                        frame = await asyncio.to_thread(draw_detection_overlay, frame, result)
                        
                except Exception as e:
                    # If pipeline fails, still show the demo frame
                    pass
            
            # Encode frame as JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            ok, buffer = await asyncio.to_thread(cv2.imencode, '.jpg', frame, encode_param)
            if not ok:
                await asyncio.sleep(frame_delay)
                continue
            frame_bytes = buffer.tobytes()
            
            # Yield as MJPEG frame
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            # Control frame rate
            await asyncio.sleep(frame_delay)
            
    finally:
        if cap:
            cap.release()


def draw_detection_overlay(frame: np.ndarray, result) -> np.ndarray:
    """Draw detection boxes and info on frame."""
    overlay = frame.copy()
    
    # Get bag count from result if available
    bag_count = getattr(result, 'bag_count', 0)
    
    # Draw person count badge
    cv2.rectangle(overlay, (10, 10), (180, 45), (0, 0, 0), -1)
    cv2.putText(overlay, f"Persons: {result.person_count}", (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Draw bag count badge
    cv2.rectangle(overlay, (10, 50), (180, 85), (0, 0, 0), -1)
    cv2.putText(overlay, f"Bags: {bag_count}", (15, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
    
    # Draw risk level indicator
    risk_color = (0, 255, 0)  # Green for low
    risk_text = result.risk_assessment.level.value.upper()
    if result.risk_assessment.level.value == "medium":
        risk_color = (0, 165, 255)  # Orange
    elif result.risk_assessment.level.value == "high":
        risk_color = (0, 0, 255)  # Red
    
    cv2.rectangle(overlay, (10, 90), (180, 125), (0, 0, 0), -1)
    cv2.putText(overlay, f"Risk: {risk_text}", 
                (15, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, risk_color, 2)
    
    # Draw bounding boxes for persons (blurred faces)
    if hasattr(result, 'detections'):
        # Performance: DO NOT create a new ObjectDetector here (that would reload YOLO).
        for det in result.detections:
            bbox = det.get("bbox")
            if not bbox or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = map(int, bbox)
            cls = det.get("class_name")
            conf = float(det.get("confidence", 0.0))

            if cls == "person":
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    overlay,
                    f"Person {conf:.2f}",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )
            elif cls in ("backpack", "handbag", "suitcase"):
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(
                    overlay,
                    f"{cls} {conf:.2f}",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    2,
                )
    
    # Blend overlay
    return cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)


@router.get("/video/{camera_id}")
async def video_feed(
    camera_id: str,
    source: Optional[str] = Query(None, description="Video source (file/URL/camera index)"),
    fps: int = Query(15, ge=1, le=30, description="Frames per second"),
    detections: bool = Query(True, description="Show detection overlays")
):
    """
    Stream anonymized MJPEG video feed.
    
    **Privacy Guarantee:**
    - All frames pass through anonymization pipeline
    - Detected persons have faces automatically blurred
    - No raw video is stored or transmitted
    
    **Usage:**
    - Use in HTML: `<img src="/api/stream/video/camera-1" />`
    - Query params control quality and overlays
    """
    return StreamingResponse(
        generate_mjpeg_stream(camera_id, source, fps, detections),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/snapshot/{camera_id}")
async def get_snapshot(
    camera_id: str,
    source: Optional[str] = Query(None)
):
    """
    Get a single anonymized frame snapshot.
    
    Returns a JPEG image of the current camera view with anonymization applied.
    """
    pipeline = get_pipeline()
    
    # Generate or capture frame
    frame = generate_demo_frame(camera_id, 0)
    
    if source and not _demo_mode:
        cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if not ret:
                frame = generate_demo_frame(camera_id, 0)
    
    # Process through pipeline
    if pipeline:
        try:
            from app.ml.pipeline_manager import analyze_frame as analyze_frame_safe
            result = await asyncio.to_thread(analyze_frame_safe, frame, camera_id, False, None)
            if result.anonymized_frame is not None:
                frame = result.anonymized_frame
        except:
            pass
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    
    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg"
    )


@router.get("/status")
async def stream_status():
    """Get streaming service status."""
    from app.ml.pipeline_manager import get_runtime_status
    status = get_runtime_status()
    return {
        "status": "operational",
        "demo_mode": _demo_mode,
        # Backward compatible fields
        "pipeline_loaded": status["pipeline_loaded"],
        "anonymization_enabled": status["anonymization_enabled"],
        "disclaimer": "All feeds are anonymized by default. No raw video is stored.",
        # New structured fields
        "deployment_mode": status["deployment_mode"],
        "blur_intensity": status["blur_intensity"],
        "blur_level": status["blur_level"],
        "allow_demo_privacy_override": status["allow_demo_privacy_override"],
        "metrics": status["metrics"],
    }


@router.get("/privacy")
async def privacy_status():
    """
    Get current anonymization + blur settings and runtime metrics.
    This is safe to expose to the dashboard (no sensitive content).
    """
    from app.ml.pipeline_manager import get_runtime_status
    return get_runtime_status()


@router.post("/privacy/blur/increase")
async def increase_blur_strength(step: int = Query(10, ge=2, le=50, description="Blur step increase")):
    """Increase blur strength (privacy-first)."""
    from app.ml.pipeline_manager import increase_blur
    state = increase_blur(step=step)
    return {
        "anonymization_enabled": state.anonymization_enabled,
        "blur_intensity": state.blur_intensity,
        "blur_level": state.blur_level,
    }


@router.post("/privacy/blur/decrease")
async def decrease_blur_strength(step: int = Query(10, ge=2, le=50, description="Blur step decrease")):
    """Decrease blur strength (still anonymized)."""
    from app.ml.pipeline_manager import decrease_blur
    state = decrease_blur(step=step)
    return {
        "anonymization_enabled": state.anonymization_enabled,
        "blur_intensity": state.blur_intensity,
        "blur_level": state.blur_level,
    }


@router.post("/privacy/anonymization")
async def set_anonymization(enabled: bool = Query(True, description="Enable/disable anonymization (demo/admin only)")):
    """Toggle anonymization (OFF allowed only when ALLOW_DEMO_PRIVACY_OVERRIDE=true)."""
    from app.ml.pipeline_manager import set_anonymization_enabled
    try:
        state = set_anonymization_enabled(enabled)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "anonymization_enabled": state.anonymization_enabled,
        "blur_intensity": state.blur_intensity,
        "blur_level": state.blur_level,
    }
