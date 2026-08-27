"""
Pose estimation using MediaPipe.
Analyzes body posture for behavior understanding.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from enum import Enum

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: mediapipe not installed. Pose estimation will use mock data.")


class PostureType(str, Enum):
    """Classification of detected postures."""
    STANDING = "standing"
    WALKING = "walking"
    SITTING = "sitting"
    LYING = "lying"
    AGGRESSIVE = "aggressive"
    UNKNOWN = "unknown"


class PoseEstimator:
    """
    MediaPipe-based pose estimation for behavior analysis.
    
    Detects and classifies body postures to aid in risk assessment.
    
    NOTE: Posture classification is approximate and should not be used
    as sole basis for any enforcement action.
    """
    
    # MediaPipe landmark indices
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    
    def __init__(self, min_detection_confidence: float = 0.5):
        """
        Initialize pose estimator.
        
        Args:
            min_detection_confidence: Minimum confidence for detection
        """
        self.pose = None
        
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # Fastest model
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=0.5
            )
    
    def estimate(self, frame: np.ndarray) -> List[Dict]:
        """
        Estimate poses in a frame.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of pose dictionaries with landmarks and classification
        """
        if self.pose is None:
            return self._mock_poses(frame)
        
        import cv2
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.pose.process(rgb_frame)
        
        poses = []
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Extract key points
            keypoints = {}
            for idx, landmark in enumerate(landmarks):
                keypoints[idx] = {
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility
                }
            
            # Classify posture
            posture = self._classify_posture(keypoints, frame.shape)
            
            poses.append({
                "keypoints": keypoints,
                "posture": posture,
                "confidence": self._calculate_pose_confidence(keypoints)
            })
        
        return poses
    
    def _mock_poses(self, frame: np.ndarray) -> List[Dict]:
        """Generate mock pose data for demo."""
        import random
        
        postures = [PostureType.STANDING, PostureType.WALKING]
        
        return [{
            "keypoints": {},
            "posture": random.choice(postures).value,
            "confidence": random.uniform(0.6, 0.9)
        }]
    
    def _classify_posture(self, keypoints: Dict, frame_shape: Tuple) -> str:
        """
        Classify posture based on keypoint positions.
        
        This is a simplified rule-based classification.
        Real-world systems would use more sophisticated methods.
        """
        height, width = frame_shape[:2]
        
        try:
            # Get key landmarks
            nose = keypoints.get(self.NOSE)
            left_shoulder = keypoints.get(self.LEFT_SHOULDER)
            right_shoulder = keypoints.get(self.RIGHT_SHOULDER)
            left_hip = keypoints.get(self.LEFT_HIP)
            right_hip = keypoints.get(self.RIGHT_HIP)
            left_wrist = keypoints.get(self.LEFT_WRIST)
            right_wrist = keypoints.get(self.RIGHT_WRIST)
            
            if not all([nose, left_shoulder, right_shoulder, left_hip, right_hip]):
                return PostureType.UNKNOWN.value
            
            # Calculate body orientation
            shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
            hip_y = (left_hip["y"] + right_hip["y"]) / 2
            
            torso_height = abs(hip_y - shoulder_y)
            
            # Check for aggressive posture (arms raised or extended forward)
            if left_wrist and right_wrist:
                wrist_y = (left_wrist["y"] + right_wrist["y"]) / 2
                # Arms above shoulders
                if wrist_y < shoulder_y - 0.1:
                    return PostureType.AGGRESSIVE.value
            
            # Check for lying down (torso nearly horizontal)
            if torso_height < 0.1:
                return PostureType.LYING.value
            
            # Check for sitting (hips much lower than expected for standing)
            if hip_y > 0.7:
                return PostureType.SITTING.value
            
            return PostureType.STANDING.value
            
        except (KeyError, TypeError):
            return PostureType.UNKNOWN.value
    
    def _calculate_pose_confidence(self, keypoints: Dict) -> float:
        """Calculate overall confidence of pose detection."""
        if not keypoints:
            return 0.0
        
        visibilities = [kp["visibility"] for kp in keypoints.values()]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0
    
    def detect_aggressive_interaction(
        self, 
        poses: List[Dict],
        person_bboxes: List[List[float]],
        proximity_threshold: float = 0.15
    ) -> Optional[Dict]:
        """
        Detect potential aggressive interaction between two people.
        
        Args:
            poses: List of pose detections
            person_bboxes: Bounding boxes of detected persons
            proximity_threshold: Normalized distance threshold (0-1)
            
        Returns:
            Detection dict if aggressive interaction found, None otherwise
        
        DISCLAIMER: This is a heuristic-based detection with significant
        limitations. False positives are expected and should be verified.
        """
        if len(poses) < 2 or len(person_bboxes) < 2:
            return None
        
        # Check for aggressive postures
        aggressive_poses = [p for p in poses if p["posture"] == PostureType.AGGRESSIVE.value]
        
        if not aggressive_poses:
            return None
        
        # Check if two people are in close proximity
        for i, bbox1 in enumerate(person_bboxes):
            for j, bbox2 in enumerate(person_bboxes):
                if i >= j:
                    continue
                
                # Calculate center distance
                c1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
                c2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)
                
                distance = np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                
                if distance < proximity_threshold:
                    return {
                        "type": "potential_aggressive_interaction",
                        "persons": [i, j],
                        "distance": distance,
                        "confidence": min(p["confidence"] for p in aggressive_poses),
                        "disclaimer": "Approximate detection. May be normal interaction."
                    }
        
        return None
    
    def close(self):
        """Release resources."""
        if self.pose:
            self.pose.close()
