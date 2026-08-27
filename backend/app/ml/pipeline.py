"""
Main analysis pipeline that combines all ML components.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

from app.ml.detector import ObjectDetector, SimpleTracker
from app.ml.pose_estimator import PoseEstimator
from app.ml.anonymizer import Anonymizer
from app.ml.risk_scorer import RiskScorer, RiskAssessment, TemporalRiskSmoother
from app.core.config import settings


@dataclass
class AnalysisResult:
    """Result of analyzing a single frame."""
    timestamp: datetime
    camera_id: str
    
    # Detection results
    person_count: int
    bag_count: int
    detections: List[Dict]
    poses: List[Dict]
    
    # Computed metrics
    crowd_density: float
    loitering_detections: List[Dict]
    aggressive_interactions: List[Dict]
    
    # Risk assessment
    risk_assessment: RiskAssessment
    
    # Processed frame (anonymized)
    anonymized_frame: Optional[np.ndarray] = None

    # Runtime metrics (added for real-time dashboards / streaming observability)
    # Exposed via FastAPI responses and WebSocket stats.
    runtime_metrics: Dict = field(default_factory=dict)


class AnalysisPipeline:
    """
    Complete analysis pipeline for video surveillance.
    
    Combines object detection, pose estimation, tracking,
    anonymization, and risk scoring into a single pipeline.
    """
    
    def __init__(
        self,
        yolo_model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        anonymize: bool = True,
        blur_intensity: int = 51
    ):
        """
        Initialize the analysis pipeline.
        
        Args:
            yolo_model_path: Path to YOLOv8 model weights
            confidence_threshold: Detection confidence threshold
            anonymize: Whether to anonymize output frames
            blur_intensity: Gaussian blur intensity for anonymization
        """
        # Initialize components
        self.detector = ObjectDetector(
            yolo_model_path,
            confidence_threshold,
            imgsz=settings.YOLO_IMGSZ,
            device=settings.YOLO_DEVICE,
            use_fuse=settings.YOLO_USE_FUSE,
        )
        self.pose_estimator = PoseEstimator()
        self.anonymizer = Anonymizer(blur_intensity)
        self.risk_scorer = RiskScorer(
            thresholds={
                **RiskScorer.DEFAULT_THRESHOLDS,
                "crowd_count": settings.CROWD_THRESHOLD,
                "loiter_minutes": settings.LOITER_THRESHOLD_MINUTES,
                "risk_score_medium": settings.RISK_SCORE_MEDIUM,
                "risk_score_high": settings.RISK_SCORE_HIGH,
            }
        )
        
        # Per-camera trackers
        self.trackers: Dict[str, SimpleTracker] = {}

        # Per-camera risk smoothing (stable output for real-time dashboards)
        self._risk_smoothers: Dict[str, TemporalRiskSmoother] = {}
        
        # Configuration
        self.anonymize = anonymize
        
        # Performance tracking
        self.frame_times: List[float] = []
        window = int(getattr(settings, "PIPELINE_METRICS_WINDOW", 60) or 60)
        self._metrics_window = max(10, window)
        self._ts = deque(maxlen=self._metrics_window + 1)  # perf_counter timestamps
        self._infer_ms = deque(maxlen=self._metrics_window)
        self._anon_ms = deque(maxlen=self._metrics_window)
        self._total_ms = deque(maxlen=self._metrics_window)
    
    def get_tracker(self, camera_id: str) -> SimpleTracker:
        """Get or create tracker for a camera."""
        if camera_id not in self.trackers:
            self.trackers[camera_id] = SimpleTracker()
        return self.trackers[camera_id]

    def _get_risk_smoother(self, camera_id: str) -> TemporalRiskSmoother:
        """Get or create a temporal smoother for a camera."""
        if camera_id not in self._risk_smoothers:
            self._risk_smoothers[camera_id] = TemporalRiskSmoother(
                window_size=settings.RISK_SMOOTHING_WINDOW,
                debounce_frames=settings.RISK_LEVEL_DEBOUNCE_FRAMES,
            )
        return self._risk_smoothers[camera_id]

    def set_anonymization_enabled(self, enabled: bool):
        """Enable/disable anonymization at runtime (privacy-first default is enabled)."""
        self.anonymize = bool(enabled)

    def set_blur_intensity(self, blur_intensity: int) -> int:
        """Set blur intensity at runtime. Returns normalized blur intensity."""
        return self.anonymizer.set_blur_intensity(blur_intensity)

    def get_blur_intensity(self) -> int:
        """Get current blur intensity."""
        return self.anonymizer.get_blur_intensity()
    
    def analyze_frame(
        self,
        frame: np.ndarray,
        camera_id: str,
        is_sensitive_area: bool = False,
        timestamp: Optional[datetime] = None
    ) -> AnalysisResult:
        """
        Analyze a single frame through the complete pipeline.
        
        Args:
            frame: Input frame (BGR format)
            camera_id: Unique camera identifier
            is_sensitive_area: Whether this camera is in a sensitive zone
            timestamp: Frame timestamp (default: current time)
            
        Returns:
            Complete analysis result with risk assessment
        """
        import time
        # Runtime metrics start (perf_counter is monotonic and efficient)
        start_t = time.perf_counter()
        
        timestamp = timestamp or datetime.utcnow()
        
        # Step 1: Object Detection
        det_t0 = time.perf_counter()  # metrics: inference start
        detections = self.detector.detect(frame)
        det_t1 = time.perf_counter()  # metrics: inference end
        person_detections = self.detector.get_person_detections(detections)
        person_count = len(person_detections)
        bag_count = self.detector.count_bags(detections)
        
        # Step 2: Tracking for loitering detection
        tracker = self.get_tracker(camera_id)
        tracker.update(person_detections, timestamp)
        loiterers = tracker.get_loiterers(threshold_seconds=300)  # 5 minutes
        
        # Step 3: Crowd density calculation
        density_info = self.detector.calculate_crowd_density(
            detections, frame.shape
        )
        
        # Step 4: Pose estimation (on person detections)
        poses = []
        aggressive_poses = 0
        if person_count > 0:
            poses = self.pose_estimator.estimate(frame)
            aggressive_poses = sum(
                1 for p in poses if p.get("posture") == "aggressive"
            )
        
        # Step 5: Check for aggressive interactions
        aggressive_interactions = []
        if aggressive_poses > 0 and person_count >= 2:
            person_bboxes = [d["bbox"] for d in person_detections]
            interaction = self.pose_estimator.detect_aggressive_interaction(
                poses, person_bboxes
            )
            if interaction:
                aggressive_interactions.append(interaction)
        
        # Step 6: Calculate risk score
        max_loiter_duration = max(
            (l["duration_seconds"] for l in loiterers), 
            default=0
        )
        
        risk_assessment = self.risk_scorer.calculate_risk(
            person_count=person_count,
            density_ratio=density_info["density_ratio"],
            aggressive_poses=aggressive_poses,
            persons_in_proximity=len(aggressive_interactions),
            loitering_detections=len(loiterers),
            loiter_duration_seconds=max_loiter_duration,
            is_sensitive_area=is_sensitive_area
        )

        # Temporal smoothing for stable dashboard output (moving average + debounce)
        smoother = self._get_risk_smoother(camera_id)
        smoothed_score = smoother.update_score(risk_assessment.score)
        proposed_level = self.risk_scorer._score_to_level(smoothed_score)
        stable_level = smoother.update_level(proposed_level)
        if smoothed_score != risk_assessment.score or stable_level != risk_assessment.level:
            risk_assessment = RiskAssessment(
                score=smoothed_score,
                level=stable_level,
                factors=risk_assessment.factors,
                explanation=(risk_assessment.explanation + "\n\n(Temporally smoothed for dashboard stability.)"),
                confidence=risk_assessment.confidence,
                timestamp=risk_assessment.timestamp,
                disclaimer=risk_assessment.disclaimer,
                limitations=risk_assessment.limitations,
            )
        
        # Step 7: Anonymization
        anonymized_frame = None
        anon_t0 = time.perf_counter()  # metrics: anonymization start
        if self.anonymize and self.anonymizer:
            anonymized_frame = self.anonymizer.anonymize_detections(
                frame, person_detections
            )
        anon_t1 = time.perf_counter()  # metrics: anonymization end
        
        # Track performance
        end_t = time.perf_counter()

        # Runtime metrics calculation (efficient rolling window)
        inference_ms = (det_t1 - det_t0) * 1000.0
        anonymization_ms = (anon_t1 - anon_t0) * 1000.0
        total_ms = (end_t - start_t) * 1000.0

        self._ts.append(end_t)
        self._infer_ms.append(inference_ms)
        self._anon_ms.append(anonymization_ms)
        self._total_ms.append(total_ms)

        elapsed = (end_t - start_t)
        self.frame_times.append(elapsed)
        if len(self.frame_times) > 100:
            self.frame_times = self.frame_times[-100:]

        fps = 0.0
        if len(self._ts) >= 2:
            duration = self._ts[-1] - self._ts[0]
            if duration > 0:
                fps = (len(self._ts) - 1) / duration
        
        return AnalysisResult(
            timestamp=timestamp,
            camera_id=camera_id,
            person_count=person_count,
            bag_count=bag_count,
            detections=detections,
            poses=poses,
            crowd_density=density_info["density_ratio"],
            loitering_detections=loiterers,
            aggressive_interactions=aggressive_interactions,
            risk_assessment=risk_assessment,
            anonymized_frame=anonymized_frame,
            runtime_metrics={
                "fps": fps,
                "inference_ms": inference_ms,
                "anonymization_ms": anonymization_ms,
                "total_ms": total_ms,
            }
        )
    
    def should_generate_alert(self, result: AnalysisResult) -> bool:
        """Determine if analysis result should trigger an alert."""
        # Only alert for medium and high risk
        from app.ml.risk_scorer import RiskLevel
        
        return result.risk_assessment.level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
    
    def get_performance_stats(self) -> Dict:
        """Get pipeline performance statistics."""
        if not self.frame_times:
            return {"fps": 0, "avg_time_ms": 0, "frames_processed": 0}
        
        avg_time = sum(self.frame_times) / len(self.frame_times)
        
        stats = {
            # Backward-compatible keys
            "fps": 1.0 / avg_time if avg_time > 0 else 0,
            "avg_time_ms": avg_time * 1000,
            "frames_processed": len(self.frame_times),
        }

        # Additional structured metrics (rolling averages)
        if self._total_ms:
            stats["avg_total_ms"] = float(sum(self._total_ms) / len(self._total_ms))
        if self._infer_ms:
            stats["avg_inference_ms"] = float(sum(self._infer_ms) / len(self._infer_ms))
        if self._anon_ms:
            stats["avg_anonymization_ms"] = float(sum(self._anon_ms) / len(self._anon_ms))
        if len(self._ts) >= 2:
            duration = self._ts[-1] - self._ts[0]
            stats["rolling_fps"] = float((len(self._ts) - 1) / duration) if duration > 0 else 0.0

        return stats
    
    def close(self):
        """Release resources."""
        if self.pose_estimator:
            self.pose_estimator.close()


def create_demo_pipeline() -> AnalysisPipeline:
    """Create a pipeline configured for demo purposes."""
    return AnalysisPipeline(
        yolo_model_path=settings.YOLO_MODEL_PATH or "yolov8n.pt",
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        anonymize=settings.ANONYMIZATION_ENABLED if hasattr(settings, "ANONYMIZATION_ENABLED") else settings.DEFAULT_ANONYMIZATION,
        blur_intensity=settings.FACE_BLUR_INTENSITY
    )
