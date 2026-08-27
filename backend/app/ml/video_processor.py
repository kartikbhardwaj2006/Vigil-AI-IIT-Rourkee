"""
Video processor for frame extraction and analysis.
"""

import cv2
import numpy as np
from typing import Generator, Tuple, Optional
from datetime import datetime


class VideoProcessor:
    """Handles video stream processing and frame extraction."""
    
    def __init__(self, source: str | int = 0):
        """
        Initialize video processor.
        
        Args:
            source: Video file path, RTSP URL, or camera index
        """
        self.source = source
        self.cap = None
        self.fps = 30
        self.frame_count = 0
        
    def open(self) -> bool:
        """Open video source."""
        self.cap = cv2.VideoCapture(self.source)
        if self.cap.isOpened():
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            return True
        return False
    
    def close(self):
        """Release video capture."""
        if self.cap:
            self.cap.release()
    
    def get_frames(self, skip: int = 1) -> Generator[Tuple[np.ndarray, int, datetime], None, None]:
        """
        Generate frames from video source.
        
        Args:
            skip: Process every Nth frame (for performance)
            
        Yields:
            Tuple of (frame, frame_number, timestamp)
        """
        if not self.cap or not self.cap.isOpened():
            if not self.open():
                return
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Skip frames for performance
            if self.frame_count % skip != 0:
                continue
            
            timestamp = datetime.utcnow()
            yield frame, self.frame_count, timestamp
    
    def get_single_frame(self) -> Optional[Tuple[np.ndarray, datetime]]:
        """Get a single frame from the source."""
        if not self.cap or not self.cap.isOpened():
            if not self.open():
                return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame, datetime.utcnow()
        return None
    
    @staticmethod
    def resize_frame(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
        """Resize frame maintaining aspect ratio."""
        height, width = frame.shape[:2]
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            return cv2.resize(frame, (max_width, new_height))
        return frame
    
    @staticmethod
    def frame_to_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
        """Convert frame to JPEG bytes."""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        return buffer.tobytes()


class VideoClipSaver:
    """Save video clips for alert evidence."""
    
    def __init__(self, output_dir: str = "./clips"):
        self.output_dir = output_dir
        self.writer = None
        self.frames = []
        
    def start_recording(self, fps: float = 30, buffer_frames: int = 90):
        """Start recording with a frame buffer."""
        self.fps = fps
        self.buffer_size = buffer_frames
        self.frames = []
        
    def add_frame(self, frame: np.ndarray):
        """Add frame to buffer."""
        self.frames.append(frame.copy())
        # Keep only recent frames
        if len(self.frames) > self.buffer_size * 2:
            self.frames = self.frames[-self.buffer_size:]
    
    def save_clip(self, filename: str, duration_seconds: int = 5) -> str:
        """
        Save buffered frames as video clip.
        
        Returns path to saved clip.
        """
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        output_path = os.path.join(self.output_dir, filename)
        
        if not self.frames:
            return None
        
        # Get frame dimensions
        height, width = self.frames[0].shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
        
        # Calculate frames needed
        frames_needed = int(duration_seconds * self.fps)
        frames_to_save = self.frames[-frames_needed:]
        
        for frame in frames_to_save:
            writer.write(frame)
        
        writer.release()
        
        return output_path
    
    def save_thumbnail(self, frame: np.ndarray, filename: str) -> str:
        """Save a thumbnail image."""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        output_path = os.path.join(self.output_dir, filename)
        
        # Resize to thumbnail
        thumbnail = VideoProcessor.resize_frame(frame, max_width=320)
        cv2.imwrite(output_path, thumbnail)
        
        return output_path
