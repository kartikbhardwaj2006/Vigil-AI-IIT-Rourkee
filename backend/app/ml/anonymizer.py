"""
Anonymization module for privacy preservation.
Implements face blurring and configurable anonymization strategies.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class Anonymizer:
    """
    Privacy-preserving anonymization for video frames.
    
    Implements multiple anonymization strategies:
    - Gaussian blur (default)
    - Pixelation
    - Solid color mask
    """
    
    def __init__(self, blur_intensity: int = 51, method: str = "blur"):
        """
        Initialize anonymizer.
        
        Args:
            blur_intensity: Gaussian blur kernel size (must be odd)
            method: Anonymization method ("blur", "pixelate", "mask")
        """
        # Ensure blur intensity is odd
        self.blur_intensity = self._normalize_blur_intensity(blur_intensity)
        self.method = method
        
        # Load face detector (Haar cascade - fast and reliable)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Profile face detector
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )

    @staticmethod
    def _normalize_blur_intensity(value: int) -> int:
        """
        Normalize Gaussian kernel size for blur:
        - must be odd
        - must be >= 3
        """
        try:
            v = int(value)
        except Exception:
            v = 51
        v = max(3, v)
        return v if v % 2 == 1 else v + 1

    def set_blur_intensity(self, blur_intensity: int) -> int:
        """
        Update blur intensity at runtime.
        Returns the normalized blur intensity actually applied.
        """
        self.blur_intensity = self._normalize_blur_intensity(blur_intensity)
        return self.blur_intensity

    def get_blur_intensity(self) -> int:
        """Get current blur intensity (Gaussian kernel size)."""
        return int(self.blur_intensity)

    def increase_blur(self, step: int = 10, max_value: int = 151) -> int:
        """
        Increase blur intensity efficiently.
        step is applied then normalized to an odd kernel size.
        """
        next_value = min(int(self.blur_intensity) + int(step), int(max_value))
        return self.set_blur_intensity(next_value)

    def decrease_blur(self, step: int = 10, min_value: int = 3) -> int:
        """Decrease blur intensity efficiently."""
        next_value = max(int(self.blur_intensity) - int(step), int(min_value))
        return self.set_blur_intensity(next_value)
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.
        
        Returns:
            List of (x, y, w, h) tuples for detected faces
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect frontal faces
        frontal_faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Detect profile faces
        profile_faces = self.profile_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Combine and deduplicate
        all_faces = list(frontal_faces) + list(profile_faces)
        return self._deduplicate_faces(all_faces)
    
    def _deduplicate_faces(self, faces: List, iou_threshold: float = 0.5) -> List:
        """Remove overlapping face detections."""
        if len(faces) == 0:
            return []
        
        # Convert to numpy array
        faces = np.array(faces)
        
        # Calculate intersection over union and remove duplicates
        unique_faces = []
        for face in faces:
            is_duplicate = False
            for unique in unique_faces:
                iou = self._calculate_iou(face, unique)
                if iou > iou_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_faces.append(face)
        
        return unique_faces
    
    def _calculate_iou(self, box1, box2) -> float:
        """Calculate intersection over union between two boxes."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        union = w1 * h1 + w2 * h2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def anonymize_region(self, frame: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """
        Anonymize a specific region of the frame.
        
        Args:
            frame: Input frame
            x, y, w, h: Region coordinates
            
        Returns:
            Frame with anonymized region
        """
        result = frame.copy()
        
        # Add padding to ensure full face coverage
        padding = int(max(w, h) * 0.2)
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + w + padding)
        y2 = min(frame.shape[0], y + h + padding)
        
        roi = result[y1:y2, x1:x2]
        
        if self.method == "blur":
            # Gaussian blur
            blurred = cv2.GaussianBlur(roi, (self.blur_intensity, self.blur_intensity), 0)
            result[y1:y2, x1:x2] = blurred
            
        elif self.method == "pixelate":
            # Pixelation
            small = cv2.resize(roi, (8, 8), interpolation=cv2.INTER_LINEAR)
            pixelated = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
            result[y1:y2, x1:x2] = pixelated
            
        elif self.method == "mask":
            # Solid color mask
            result[y1:y2, x1:x2] = [50, 50, 50]  # Dark gray
        
        return result
    
    def anonymize_frame(self, frame: np.ndarray, faces: Optional[List] = None) -> Tuple[np.ndarray, int]:
        """
        Anonymize all faces in a frame.
        
        Args:
            frame: Input frame
            faces: Optional pre-detected face locations
            
        Returns:
            Tuple of (anonymized frame, number of faces anonymized)
        """
        if faces is None:
            faces = self.detect_faces(frame)
        
        result = frame.copy()
        
        for face in faces:
            x, y, w, h = face
            result = self.anonymize_region(result, x, y, w, h)
        
        return result, len(faces)
    
    def anonymize_detections(self, frame: np.ndarray, detections: List[dict]) -> np.ndarray:
        """
        Anonymize based on person detections from YOLO.
        Blurs the entire person bounding box for full privacy protection.
        
        Args:
            frame: Input frame
            detections: List of detection dicts with 'bbox' key
            
        Returns:
            Anonymized frame
        """
        result = frame.copy()
        
        for detection in detections:
            if detection.get("class_name") == "person":
                bbox = detection["bbox"]
                x1, y1, x2, y2 = [int(c) for c in bbox]
                
                # Anonymize entire person bounding box
                result = self.anonymize_region(
                    result, 
                    x1, y1, 
                    x2 - x1, y2 - y1
                )
        
        return result


# Convenience function for quick anonymization
def anonymize_image(image_path: str, output_path: str, method: str = "blur") -> int:
    """
    Anonymize faces in an image file.
    
    Args:
        image_path: Path to input image
        output_path: Path to save anonymized image
        method: Anonymization method
        
    Returns:
        Number of faces anonymized
    """
    frame = cv2.imread(image_path)
    if frame is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    anonymizer = Anonymizer(method=method)
    result, face_count = anonymizer.anonymize_frame(frame)
    
    cv2.imwrite(output_path, result)
    
    return face_count
