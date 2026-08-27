"""
Singleton pipeline manager.

Keeps the analysis pipeline lazily loaded and provides safe runtime controls for:
- anonymization enable/disable (demo/admin only)
- blur intensity adjustments

This preserves backward compatibility by not changing existing FastAPI routes, while
allowing new endpoints to control privacy settings for demos.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Optional, Dict

from app.core.config import settings
from app.ml.pipeline import AnalysisPipeline, create_demo_pipeline


@dataclass
class PrivacyState:
    anonymization_enabled: bool
    blur_intensity: int

    @property
    def blur_level(self) -> str:
        """Human-friendly blur level label."""
        low = int(settings.FACE_BLUR_INTENSITY_LOW)
        med = int(settings.FACE_BLUR_INTENSITY_MEDIUM)
        high = int(settings.FACE_BLUR_INTENSITY_HIGH)
        v = int(self.blur_intensity)

        # Nearest level by absolute distance
        distances = {
            "LOW": abs(v - low),
            "MEDIUM": abs(v - med),
            "HIGH": abs(v - high),
        }
        return min(distances, key=distances.get)


_lock = Lock()
_pipeline: Optional[AnalysisPipeline] = None
_analyze_lock = Lock()


def get_pipeline() -> Optional[AnalysisPipeline]:
    """Get or create the shared analysis pipeline (lazy loading)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline


def analyze_frame(frame, camera_id: str, is_sensitive_area: bool = False, timestamp=None):
    """
    Thread-safe wrapper around pipeline.analyze_frame.

    OpenCV + Ultralytics can be sensitive to concurrent access in multi-client streaming.
    This lock keeps inference stable under load on CPU-only deployments.
    """
    p = get_pipeline()
    if p is None:
        return None
    with _analyze_lock:
        return p.analyze_frame(frame, camera_id, is_sensitive_area=is_sensitive_area, timestamp=timestamp)

    with _lock:
        if _pipeline is not None:
            return _pipeline
        try:
            _pipeline = create_demo_pipeline()
        except Exception as e:
            print(f"Warning: Could not create pipeline: {e}")
            _pipeline = None
        return _pipeline


def get_privacy_state() -> PrivacyState:
    """
    Get the current runtime privacy state.
    Falls back to config defaults if pipeline isn't loaded yet.
    """
    p = get_pipeline()
    if p is None:
        return PrivacyState(
            anonymization_enabled=bool(settings.ANONYMIZATION_ENABLED),
            blur_intensity=int(settings.FACE_BLUR_INTENSITY),
        )
    return PrivacyState(anonymization_enabled=bool(p.anonymize), blur_intensity=int(p.get_blur_intensity()))


def set_anonymization_enabled(enabled: bool) -> PrivacyState:
    """
    Enable/disable anonymization at runtime.

    Disabling (OFF) is guarded for demo/admin mode only.
    """
    enabled_bool = bool(enabled)
    if not enabled_bool and not bool(settings.ALLOW_DEMO_PRIVACY_OVERRIDE):
        # Privacy-first: do not allow disabling unless explicitly enabled via config.
        raise PermissionError("Anonymization disable requires ALLOW_DEMO_PRIVACY_OVERRIDE=true")

    p = get_pipeline()
    if p is not None:
        p.set_anonymization_enabled(enabled_bool)
    return get_privacy_state()


def increase_blur(step: int = 10) -> PrivacyState:
    p = get_pipeline()
    if p is not None:
        p.anonymizer.increase_blur(step=step)
    return get_privacy_state()


def decrease_blur(step: int = 10) -> PrivacyState:
    p = get_pipeline()
    if p is not None:
        p.anonymizer.decrease_blur(step=step)
    return get_privacy_state()


def get_runtime_status() -> Dict:
    """Get a structured status payload suitable for API responses."""
    p = get_pipeline()
    privacy = get_privacy_state()
    metrics = p.get_performance_stats() if p is not None else {"fps": 0, "avg_time_ms": 0, "frames_processed": 0}

    return {
        "deployment_mode": settings.DEPLOYMENT_MODE,
        "pipeline_loaded": p is not None,
        "anonymization_enabled": privacy.anonymization_enabled,
        "blur_intensity": privacy.blur_intensity,
        "blur_level": privacy.blur_level,
        "allow_demo_privacy_override": bool(settings.ALLOW_DEMO_PRIVACY_OVERRIDE),
        "metrics": metrics,
    }

