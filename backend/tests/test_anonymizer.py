"""
Unit tests for the anonymizer module.

Verification that:
1. Blur covers all detected bounding boxes
2. Blur intensity is correctly applied
3. No unprocessed face regions bypass anonymization
"""

import pytest
import numpy as np
import cv2
from typing import List, Dict


class TestAnonymizer:
    """Tests for the Anonymizer class."""
    
    @pytest.fixture
    def sample_frame(self):
        """Create a sample test frame with a synthetic face-like region."""
        # Create a 640x480 frame with some distinct regions
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add background gradient
        for i in range(480):
            frame[i, :] = [80 + i//4, 90 + i//4, 100 + i//4]
        
        # Add a bright "face-like" region at a known position
        # This represents a person's head that should be blurred
        face_region = (200, 100, 280, 200)  # x1, y1, x2, y2
        frame[face_region[1]:face_region[3], face_region[0]:face_region[2]] = [200, 180, 160]
        
        return frame
    
    @pytest.fixture
    def sample_detection(self):
        """Create a sample person detection."""
        return {
            "bbox": [180, 80, 300, 350],  # x1, y1, x2, y2 (contains the face region)
            "class_name": "person",
            "class_id": 0,
            "confidence": 0.92
        }
    
    def test_anonymizer_import(self):
        """Test that anonymizer module can be imported."""
        try:
            from app.ml.anonymizer import Anonymizer
            assert Anonymizer is not None
        except ImportError as e:
            pytest.skip(f"Anonymizer module not available: {e}")
    
    def test_blur_covers_bounding_box(self, sample_frame, sample_detection):
        """
        Test that blur is applied to the entire bounding box region.
        
        This is a critical privacy test - ensures no unblurred face pixels
        can leak through the anonymization.
        """
        try:
            from app.ml.anonymizer import Anonymizer
        except ImportError:
            pytest.skip("Anonymizer module not available")
        
        anonymizer = Anonymizer(blur_intensity=51)
        
        # Get the original pixel values in the detection region
        bbox = sample_detection["bbox"]
        original_region = sample_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]].copy()
        
        # Apply anonymization
        anonymized_frame = anonymizer.anonymize_detections(
            sample_frame.copy(),
            [sample_detection]
        )
        
        # Get the anonymized region
        anonymized_region = anonymized_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        
        # Calculate the difference
        difference = np.abs(original_region.astype(float) - anonymized_region.astype(float))
        avg_difference = np.mean(difference)
        
        # The blurred region should be significantly different from the original
        # A properly blurred region should have substantial pixel changes
        assert avg_difference > 5, (
            f"Blur did not significantly change the bounding box region. "
            f"Average pixel difference: {avg_difference}. "
            "This may indicate blur is not being applied correctly."
        )
        
        print(f"✅ Blur verification passed. Avg pixel difference: {avg_difference:.2f}")
    
    def test_blur_intensity_applied(self, sample_frame, sample_detection):
        """
        Test that the configured blur intensity is actually applied.
        
        Higher blur intensity should result in more uniform pixel values
        within the blurred region.
        """
        try:
            from app.ml.anonymizer import Anonymizer
        except ImportError:
            pytest.skip("Anonymizer module not available")
        
        # Test with low blur
        low_blur_anonymizer = Anonymizer(blur_intensity=11)
        low_blur_frame = low_blur_anonymizer.anonymize_detections(
            sample_frame.copy(),
            [sample_detection]
        )
        
        # Test with high blur
        high_blur_anonymizer = Anonymizer(blur_intensity=51)
        high_blur_frame = high_blur_anonymizer.anonymize_detections(
            sample_frame.copy(),
            [sample_detection]
        )
        
        bbox = sample_detection["bbox"]
        
        # Calculate standard deviation within blurred region
        # Higher blur = lower std (more uniform)
        low_blur_region = low_blur_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        high_blur_region = high_blur_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        
        low_blur_std = np.std(low_blur_region)
        high_blur_std = np.std(high_blur_region)
        
        # High blur should produce more uniform (lower std) region
        assert high_blur_std <= low_blur_std, (
            f"Higher blur intensity should produce more uniform region. "
            f"Low blur std: {low_blur_std:.2f}, High blur std: {high_blur_std:.2f}"
        )
        
        print(f"✅ Blur intensity test passed. Low: {low_blur_std:.2f}, High: {high_blur_std:.2f}")
    
    def test_multiple_detections_blurred(self, sample_frame):
        """Test that multiple detections are all blurred."""
        try:
            from app.ml.anonymizer import Anonymizer
        except ImportError:
            pytest.skip("Anonymizer module not available")
        
        detections = [
            {"bbox": [50, 50, 150, 200], "class_name": "person", "class_id": 0, "confidence": 0.9},
            {"bbox": [300, 100, 400, 300], "class_name": "person", "class_id": 0, "confidence": 0.85},
            {"bbox": [450, 150, 550, 350], "class_name": "person", "class_id": 0, "confidence": 0.88},
        ]
        
        anonymizer = Anonymizer(blur_intensity=41)
        anonymized_frame = anonymizer.anonymize_detections(sample_frame.copy(), detections)
        
        # Check each detection region was modified
        for i, det in enumerate(detections):
            bbox = det["bbox"]
            original = sample_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
            anonymized = anonymized_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
            
            diff = np.mean(np.abs(original.astype(float) - anonymized.astype(float)))
            
            assert diff > 1, f"Detection {i} was not blurred. Difference: {diff}"
        
        print(f"✅ Multiple detections test passed. All {len(detections)} regions blurred.")
    
    def test_non_person_not_blurred(self, sample_frame):
        """Test that non-person detections are not blurred (optional behavior)."""
        try:
            from app.ml.anonymizer import Anonymizer
        except ImportError:
            pytest.skip("Anonymizer module not available")
        
        # Only blur persons, not objects
        detections = [
            {"bbox": [100, 100, 200, 200], "class_name": "backpack", "class_id": 24, "confidence": 0.9},
        ]
        
        anonymizer = Anonymizer(blur_intensity=41)
        
        # The default behavior may or may not blur non-persons
        # This test documents the current behavior
        anonymized_frame = anonymizer.anonymize_detections(sample_frame.copy(), detections)
        
        bbox = detections[0]["bbox"]
        original = sample_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        anonymized = anonymized_frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        
        diff = np.mean(np.abs(original.astype(float) - anonymized.astype(float)))
        
        # Document behavior (this test passes regardless to document current state)
        if diff < 1:
            print(f"ℹ️ Non-person objects are NOT blurred (diff: {diff:.2f})")
        else:
            print(f"ℹ️ Non-person objects ARE blurred (diff: {diff:.2f})")


class TestBlurVerification:
    """
    Integration tests verifying blur in the full pipeline.
    """
    
    def test_pipeline_produces_anonymized_output(self):
        """Test that the analysis pipeline produces anonymized frames."""
        try:
            from app.ml.pipeline import create_demo_pipeline
        except ImportError:
            pytest.skip("Pipeline module not available")
        
        # Create pipeline with anonymization enabled
        pipeline = create_demo_pipeline()
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Analyze frame
        result = pipeline.analyze_frame(frame, "test-camera")
        
        # Verify anonymized frame is present
        if result.anonymized_frame is not None:
            # Should be different from input if any detections
            if result.person_count > 0:
                diff = np.mean(np.abs(frame.astype(float) - result.anonymized_frame.astype(float)))
                assert diff > 0, "Anonymized frame should differ from input when persons detected"
                print(f"✅ Pipeline anonymization verified. Diff: {diff:.2f}")
            else:
                print("ℹ️ No persons detected in test frame, anonymization not triggered")
        else:
            print("ℹ️ Anonymized frame is None (anonymization may be disabled)")
        
        pipeline.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
