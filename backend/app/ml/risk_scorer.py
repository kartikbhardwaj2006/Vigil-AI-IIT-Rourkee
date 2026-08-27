"""
Risk scoring engine with explainable, rule-based assessment.

This module implements a transparent, auditable risk scoring system.
All scores are calculated using documented rules, not black-box models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
from collections import deque


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RiskFactor:
    """A single factor contributing to risk score."""
    name: str
    weight: float
    value: float  # 0-1 scale
    description: str
    
    @property
    def contribution(self) -> float:
        """Calculate this factor's contribution to total score."""
        return self.weight * self.value


@dataclass
class RiskAssessment:
    """Complete risk assessment with explanation."""
    score: float  # 0-1 scale
    level: RiskLevel
    factors: List[RiskFactor]
    explanation: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Mandatory disclaimers
    disclaimer: str = "This is an automated indicator. Human verification required."
    limitations: List[str] = field(default_factory=lambda: [
        "Cannot determine intent or context",
        "May be normal behavior misinterpreted",
        "Accuracy varies with environmental conditions",
        "Requires human operator verification before any action"
    ])


class RiskScorer:
    """
    Transparent, rule-based risk scoring engine.
    
    All risk scores are calculated using documented, explainable rules.
    No black-box ML is used for final risk determination.
    """
    
    # Default weights (configurable)
    DEFAULT_WEIGHTS = {
        "crowd_density": 0.25,
        "aggressive_posture": 0.35,
        "loitering": 0.20,
        "unusual_motion": 0.10,
        "abandoned_object": 0.10
    }
    
    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "crowd_count": 15,
        "crowd_density_ratio": 0.3,
        "loiter_minutes": 5,
        "motion_std_devs": 2.0,
        # Risk score cutoffs
        "risk_score_medium": 0.3,
        "risk_score_high": 0.6,
    }
    
    def __init__(
        self, 
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize risk scorer.
        
        Args:
            weights: Custom weights for risk factors
            thresholds: Custom detection thresholds
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
    
    def calculate_risk(
        self,
        person_count: int = 0,
        density_ratio: float = 0.0,
        aggressive_poses: int = 0,
        persons_in_proximity: int = 0,
        loitering_detections: int = 0,
        loiter_duration_seconds: float = 0,
        motion_level: float = 0.0,
        abandoned_objects: int = 0,
        is_sensitive_area: bool = False
    ) -> RiskAssessment:
        """
        Calculate risk score based on detection inputs.
        
        All parameters are optional; only provided ones will be considered.
        
        Args:
            person_count: Number of persons detected
            density_ratio: Ratio of frame occupied by persons
            aggressive_poses: Number of aggressive postures detected
            persons_in_proximity: Number of persons in close proximity
            loitering_detections: Number of loitering detections
            loiter_duration_seconds: Longest loitering duration
            motion_level: Unusual motion level (std deviations from baseline)
            abandoned_objects: Number of stationary objects detected
            is_sensitive_area: Whether camera is in a sensitive area
            
        Returns:
            Complete risk assessment with explanation
        """
        factors = []
        
        # Factor 1: Crowd Density
        crowd_value = self._calculate_crowd_factor(person_count, density_ratio)
        if crowd_value > 0:
            factors.append(RiskFactor(
                name="crowd_density",
                weight=self.weights["crowd_density"],
                value=crowd_value,
                description=f"Elevated crowd density: {person_count} persons detected"
            ))
        
        # Factor 2: Aggressive Posture
        aggression_value = self._calculate_aggression_factor(
            aggressive_poses, persons_in_proximity
        )
        if aggression_value > 0:
            factors.append(RiskFactor(
                name="aggressive_posture",
                weight=self.weights["aggressive_posture"],
                value=aggression_value,
                description=f"Aggressive posture detected with {persons_in_proximity} persons in proximity"
            ))
        
        # Factor 3: Loitering
        loiter_value = self._calculate_loiter_factor(
            loitering_detections, loiter_duration_seconds
        )
        if loiter_value > 0:
            factors.append(RiskFactor(
                name="loitering",
                weight=self.weights["loitering"],
                value=loiter_value,
                description=f"Loitering detected: {loiter_duration_seconds/60:.1f} minutes"
            ))
        
        # Factor 4: Unusual Motion
        motion_value = self._calculate_motion_factor(motion_level)
        if motion_value > 0:
            factors.append(RiskFactor(
                name="unusual_motion",
                weight=self.weights["unusual_motion"],
                value=motion_value,
                description=f"Unusual motion pattern: {motion_level:.1f} std deviations"
            ))
        
        # Factor 5: Abandoned Object
        object_value = self._calculate_object_factor(abandoned_objects)
        if object_value > 0:
            factors.append(RiskFactor(
                name="abandoned_object",
                weight=self.weights["abandoned_object"],
                value=object_value,
                description=f"{abandoned_objects} stationary object(s) detected"
            ))
        
        # Calculate total score
        total_score = sum(f.contribution for f in factors)
        
        # Apply sensitive area multiplier
        if is_sensitive_area:
            total_score *= 1.5
            total_score = min(total_score, 1.0)  # Cap at 1.0
        
        # Normalize and clamp
        total_score = max(0.0, min(1.0, total_score))
        
        # Determine level
        level = self._score_to_level(total_score)
        
        # Generate explanation
        explanation = self._generate_explanation(factors, level, is_sensitive_area)
        
        # Calculate confidence (based on number of factors)
        confidence = self._calculate_confidence(factors)
        
        return RiskAssessment(
            score=total_score,
            level=level,
            factors=factors,
            explanation=explanation,
            confidence=confidence
        )
    
    def _calculate_crowd_factor(self, count: int, density: float) -> float:
        """Calculate crowd density risk factor (0-1)."""
        count_threshold = self.thresholds["crowd_count"]
        density_threshold = self.thresholds["crowd_density_ratio"]
        
        count_factor = min(count / count_threshold, 1.0) if count > 0 else 0.0
        density_factor = min(density / density_threshold, 1.0) if density > 0 else 0.0
        
        return max(count_factor, density_factor)
    
    def _calculate_aggression_factor(self, poses: int, proximity: int) -> float:
        """Calculate aggression risk factor (0-1)."""
        if poses == 0:
            return 0.0
        
        # Base value from aggressive pose detection
        base = min(poses / 2.0, 1.0)
        
        # Increase if multiple persons in proximity
        if proximity >= 2:
            base *= 1.5
        
        return min(base, 1.0)
    
    def _calculate_loiter_factor(self, count: int, duration: float) -> float:
        """Calculate loitering risk factor (0-1)."""
        if count == 0 and duration == 0:
            return 0.0
        
        threshold_seconds = self.thresholds["loiter_minutes"] * 60
        
        duration_factor = min(duration / threshold_seconds, 1.0) if duration > 0 else 0.0
        count_factor = min(count / 3.0, 1.0) if count > 0 else 0.0
        
        return max(duration_factor, count_factor)
    
    def _calculate_motion_factor(self, level: float) -> float:
        """Calculate unusual motion risk factor (0-1)."""
        threshold = self.thresholds["motion_std_devs"]
        
        if level < threshold:
            return 0.0
        
        return min((level - threshold) / threshold, 1.0)
    
    def _calculate_object_factor(self, count: int) -> float:
        """Calculate abandoned object risk factor (0-1)."""
        if count == 0:
            return 0.0
        
        return min(count / 2.0, 1.0)
    
    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        medium = float(self.thresholds.get("risk_score_medium", 0.3))
        high = float(self.thresholds.get("risk_score_high", 0.6))

        # Safety: ensure ordering even if misconfigured.
        if high < medium:
            high, medium = medium, high

        if score >= high:
            return RiskLevel.HIGH
        elif score >= medium:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_explanation(
        self, 
        factors: List[RiskFactor],
        level: RiskLevel,
        is_sensitive: bool
    ) -> str:
        """Generate human-readable explanation of risk assessment."""
        if not factors:
            return "No risk indicators detected. Normal activity observed."
        
        parts = []
        
        # Sort factors by contribution
        sorted_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)
        
        # Add factor explanations
        for factor in sorted_factors:
            parts.append(f"• {factor.description} (weight: {factor.weight:.0%})")
        
        if is_sensitive:
            parts.append("• Location: Sensitive area (multiplier applied)")
        
        explanation = "\n".join(parts)
        
        # Add level context
        level_context = {
            RiskLevel.HIGH: "\n\n⚠️ HIGH PRIORITY: Immediate operator review recommended.",
            RiskLevel.MEDIUM: "\n\n⚡ MEDIUM PRIORITY: Review at earliest convenience.",
            RiskLevel.LOW: "\n\nℹ️ LOW PRIORITY: Routine monitoring."
        }
        
        return explanation + level_context.get(level, "")
    
    def _calculate_confidence(self, factors: List[RiskFactor]) -> float:
        """
        Calculate confidence in the assessment.
        
        Higher confidence when multiple corroborating factors present.
        """
        if not factors:
            return 1.0  # High confidence in "no risk" assessment
        
        # Base confidence decreases with fewer factors
        base_confidence = min(len(factors) / 3.0, 1.0)
        
        # Adjust based on factor values
        avg_factor_value = sum(f.value for f in factors) / len(factors)
        
        return base_confidence * (0.5 + avg_factor_value * 0.5)


def create_alert_from_assessment(
    assessment: RiskAssessment,
    camera_id: int,
    detection_type: str
) -> Dict:
    """
    Create alert data from risk assessment.
    
    Returns dictionary suitable for Alert model creation.
    """
    return {
        "camera_id": camera_id,
        "risk_level": assessment.level.value,
        "risk_score": assessment.score,
        "confidence": assessment.confidence,
        "detection_type": detection_type,
        "explanation": assessment.explanation
    }


class TemporalRiskSmoother:
    """
    Temporal smoothing for stable real-time risk dashboards.

    Keeps a small rolling window (moving average) of risk scores and applies
    a lightweight debounce on level changes to reduce false spikes.
    """

    def __init__(self, window_size: int = 5, debounce_frames: int = 3):
        self.window_size = max(1, int(window_size))
        self.debounce_frames = max(1, int(debounce_frames))
        self._scores = deque(maxlen=self.window_size)

        self._stable_level: RiskLevel = RiskLevel.LOW
        self._pending_level: Optional[RiskLevel] = None
        self._pending_count: int = 0

    def update_score(self, score: float) -> float:
        """Add a raw score and return the smoothed score (moving average)."""
        s = max(0.0, min(1.0, float(score)))
        self._scores.append(s)
        return float(sum(self._scores) / len(self._scores)) if self._scores else s

    def update_level(self, proposed_level: RiskLevel) -> RiskLevel:
        """
        Debounce risk level transitions:
        - escalations and de-escalations require consistency over several frames
        """
        if proposed_level == self._stable_level:
            self._pending_level = None
            self._pending_count = 0
            return self._stable_level

        if self._pending_level != proposed_level:
            self._pending_level = proposed_level
            self._pending_count = 1
            return self._stable_level

        self._pending_count += 1
        if self._pending_count >= self.debounce_frames:
            self._stable_level = proposed_level
            self._pending_level = None
            self._pending_count = 0

        return self._stable_level
