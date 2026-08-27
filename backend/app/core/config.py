"""
Application configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vigil.db"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - Stored as string, accessed as list via property
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # ML Models
    # NOTE: The repo already ships with `backend/yolov8n.pt`. Keep this default CPU-friendly and robust.
    YOLO_MODEL_PATH: str = "./yolov8n.pt"
    YOLO_DEVICE: str = "cpu"
    YOLO_IMGSZ: int = 640
    YOLO_USE_FUSE: bool = True
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # Privacy Settings
    # Privacy-first defaults: anonymization ON by default.
    DEFAULT_ANONYMIZATION: bool = True
    ANONYMIZATION_ENABLED: bool = True
    FACE_BLUR_INTENSITY: int = 51  # Must be odd number for Gaussian blur (MEDIUM default)
    FACE_BLUR_INTENSITY_LOW: int = 21
    FACE_BLUR_INTENSITY_MEDIUM: int = 51
    FACE_BLUR_INTENSITY_HIGH: int = 91

    # Demo/admin-only control: allow disabling anonymization (OFF) for demos.
    # Keep OFF by default to preserve privacy guarantees.
    ALLOW_DEMO_PRIVACY_OVERRIDE: bool = False
    
    # Risk Thresholds
    CROWD_THRESHOLD: int = 15
    LOITER_THRESHOLD_MINUTES: int = 5
    # Risk score cutoffs (used for LOW/MEDIUM/HIGH classification).
    RISK_SCORE_MEDIUM: float = 0.3
    RISK_SCORE_HIGH: float = 0.6
    # Temporal smoothing to reduce false spikes in real-time dashboards.
    RISK_SMOOTHING_WINDOW: int = 5
    RISK_LEVEL_DEBOUNCE_FRAMES: int = 3

    # Performance metrics
    PIPELINE_METRICS_WINDOW: int = 60  # rolling window for FPS/latency averages

    # Deployment labeling (does not change core logic)
    DEPLOYMENT_MODE: str = "bank_security"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def get_cors_origins(self) -> List[str]:
        """Get CORS_ORIGINS as a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        return self.CORS_ORIGINS
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
