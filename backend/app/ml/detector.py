"""
Object detection using YOLOv8.
Detects persons, objects, and tracks them across frames.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Detection will use mock data.")


class ObjectDetector:
    """
    YOLOv8-based object detection for surveillance.
    
    Focuses on detecting:
    - Persons (for crowd analysis, pose estimation)
    - Bags/backpacks (abandoned object detection)
    - Vehicles (optional, for parking areas)
    """
    
    # Classes of interest for surveillance
    CLASSES_OF_INTEREST = {
        0: "person",
        24: "backpack",
        26: "handbag",
        28: "suitcase",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = 0.35,  # Lowered from 0.5 for better detection
        imgsz: int = 640,
        device: str = "cpu",
        use_fuse: bool = True,
    ):
        """
        Initialize detector.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence: Minimum confidence threshold
        """
        self.confidence = confidence
        self.model = None
        self.model_path = model_path
        self.imgsz = int(imgsz) if imgsz else 640
        self.device = device or "cpu"
        self.use_fuse = bool(use_fuse)
        
        if YOLO_AVAILABLE:
            try:
                resolved = self._resolve_model_path(model_path)
                self.model = YOLO(str(resolved))
                # Best-effort optimization for Intel CPU inference.
                if self.use_fuse:
                    try:
                        self.model.fuse()
                    except Exception:
                        # fuse() isn't always available depending on backend/model
                        pass

                # Ensure PyTorch is configured for CPU usage (robust to missing torch import).
                try:
                    import torch
                    if self.device == "cpu":
                        torch.set_grad_enabled(False)
                except Exception:
                    pass

                print(f"✅ Loaded YOLO model: {resolved}")
            except Exception as e:
                print(f"Warning: Could not load YOLO model: {e}")
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in a frame.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of detection dictionaries with:
            - bbox: [x1, y1, x2, y2]
            - class_name: str
            - class_id: int
            - confidence: float
        """
        if self.model is None:
            return self._mock_detections(frame)
        
        # Run inference (CPU-optimized).
        # NOTE: Keep conversions minimal: Ultralytics accepts BGR numpy arrays directly.
        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                
                # Only include classes of interest
                if class_id not in self.CLASSES_OF_INTEREST:
                    continue
                
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "class_id": class_id,
                    "class_name": self.CLASSES_OF_INTEREST[class_id],
                    "confidence": float(box.conf[0])
                })
        
        return detections

    @staticmethod
    def _resolve_model_path(model_path: str) -> Path:
        """
        Resolve YOLO weights path robustly.
        Supports:
        - absolute path
        - relative path from current working directory
        - repo-shipped weights at `backend/yolov8n.pt`
        """
        p = Path(model_path)
        if p.is_file():
            return p

        # Try relative to backend root (repo ships `backend/yolov8n.pt`)
        # detector.py -> backend/app/ml/detector.py
        backend_root = Path(__file__).resolve().parents[2]
        candidate = backend_root / p.name
        if candidate.is_file():
            return candidate

        # Fallback: allow Ultralytics to handle downloads if a known model name is passed.
        return p
    
    def _mock_detections(self, frame: np.ndarray) -> List[Dict]:
        """Generate mock detections for demo without YOLO."""
        import random
        
        height, width = frame.shape[:2]
        
        # Generate 2-5 random person detections
        num_persons = random.randint(2, 5)
        detections = []
        
        for i in range(num_persons):
            # Random position
            x1 = random.randint(50, width - 150)
            y1 = random.randint(50, height - 300)
            w = random.randint(80, 150)
            h = random.randint(200, 350)
            
            detections.append({
                "bbox": [x1, y1, x1 + w, y1 + h],
                "class_id": 0,
                "class_name": "person",
                "confidence": random.uniform(0.7, 0.95)
            })
        
        return detections
    
    def count_persons(self, detections: List[Dict]) -> int:
        """Count number of persons in detections."""
        return sum(1 for d in detections if d["class_name"] == "person")
    
    def count_bags(self, detections: List[Dict]) -> int:
        """Count number of bags (backpack, handbag, suitcase) in detections."""
        bag_classes = ["backpack", "handbag", "suitcase"]
        return sum(1 for d in detections if d["class_name"] in bag_classes)
    
    def get_person_detections(self, detections: List[Dict]) -> List[Dict]:
        """Filter to only person detections."""
        return [d for d in detections if d["class_name"] == "person"]
    
    def get_bag_detections(self, detections: List[Dict]) -> List[Dict]:
        """Filter to only bag detections."""
        bag_classes = ["backpack", "handbag", "suitcase"]
        return [d for d in detections if d["class_name"] in bag_classes]
    
    def calculate_crowd_density(
        self, 
        detections: List[Dict], 
        frame_shape: Tuple[int, int],
        zones: Optional[List[List[Tuple[int, int]]]] = None
    ) -> Dict:
        """
        Calculate crowd density metrics.
        
        Args:
            detections: List of detections
            frame_shape: (height, width) of frame
            zones: Optional list of polygon zones to analyze
            
        Returns:
            Dictionary with density metrics
        """
        persons = self.get_person_detections(detections)
        total_count = len(persons)
        
        height, width = frame_shape[:2]
        frame_area = height * width
        
        # Calculate occupied area
        person_area = 0
        for p in persons:
            x1, y1, x2, y2 = p["bbox"]
            person_area += (x2 - x1) * (y2 - y1)
        
        # Density as percentage of frame
        density_ratio = person_area / frame_area if frame_area > 0 else 0
        
        return {
            "person_count": total_count,
            "density_ratio": density_ratio,
            "is_crowded": total_count > 10 or density_ratio > 0.3,
            "crowd_level": self._get_crowd_level(total_count, density_ratio)
        }
    
    def _get_crowd_level(self, count: int, density: float) -> str:
        """Classify crowd level."""
        if count > 20 or density > 0.5:
            return "high"
        elif count > 10 or density > 0.3:
            return "medium"
        else:
            return "low"


class SimpleTracker:
    """
    Simple centroid-based object tracker.
    Tracks objects across frames for loitering detection.
    """
    
    def __init__(self, max_disappeared: int = 30):
        """
        Initialize tracker.
        
        Args:
            max_disappeared: Frames to keep tracking after object disappears
        """
        self.next_id = 0
        self.objects: Dict[int, Dict] = {}  # id -> {centroid, class, first_seen, last_seen, positions}
        self.disappeared: Dict[int, int] = {}  # id -> frames since last seen
        self.max_disappeared = max_disappeared
    
    def update(self, detections: List[Dict], timestamp: datetime) -> Dict[int, Dict]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of detection dicts
            timestamp: Current timestamp
            
        Returns:
            Dictionary of tracked objects with IDs
        """
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
            return self.objects
        
        # Calculate centroids for new detections
        input_centroids = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            input_centroids.append((cx, cy, det))
        
        # If no existing objects, register all
        if len(self.objects) == 0:
            for centroid in input_centroids:
                self._register(centroid[0], centroid[1], centroid[2], timestamp)
        else:
            # Match existing objects to new detections
            self._match_detections(input_centroids, timestamp)
        
        return self.objects
    
    def _register(self, cx: float, cy: float, detection: Dict, timestamp: datetime):
        """Register a new object."""
        self.objects[self.next_id] = {
            "centroid": (cx, cy),
            "class_name": detection["class_name"],
            "first_seen": timestamp,
            "last_seen": timestamp,
            "positions": [(cx, cy, timestamp)],
            "bbox": detection["bbox"]
        }
        self.disappeared[self.next_id] = 0
        self.next_id += 1
    
    def _deregister(self, object_id: int):
        """Remove an object from tracking."""
        del self.objects[object_id]
        del self.disappeared[object_id]
    
    def _match_detections(self, input_centroids: List, timestamp: datetime):
        """Match new detections to existing tracked objects."""
        import numpy as np
        
        object_ids = list(self.objects.keys())
        object_centroids = [self.objects[oid]["centroid"] for oid in object_ids]
        
        # Calculate distance matrix
        D = np.zeros((len(object_centroids), len(input_centroids)))
        for i, obj_c in enumerate(object_centroids):
            for j, inp_c in enumerate(input_centroids):
                D[i, j] = np.sqrt((obj_c[0] - inp_c[0])**2 + (obj_c[1] - inp_c[1])**2)
        
        # Match using greedy approach (simple but effective for demo)
        used_cols = set()
        used_rows = set()
        
        while len(used_rows) < len(object_centroids) and len(used_cols) < len(input_centroids):
            # Find minimum distance
            min_val = float('inf')
            min_row, min_col = -1, -1
            
            for i in range(len(object_centroids)):
                if i in used_rows:
                    continue
                for j in range(len(input_centroids)):
                    if j in used_cols:
                        continue
                    if D[i, j] < min_val:
                        min_val = D[i, j]
                        min_row, min_col = i, j
            
            if min_row == -1 or min_val > 100:  # Max distance threshold
                break
            
            # Update matched object
            object_id = object_ids[min_row]
            cx, cy, det = input_centroids[min_col]
            
            self.objects[object_id]["centroid"] = (cx, cy)
            self.objects[object_id]["last_seen"] = timestamp
            self.objects[object_id]["positions"].append((cx, cy, timestamp))
            self.objects[object_id]["bbox"] = det["bbox"]
            self.disappeared[object_id] = 0
            
            used_rows.add(min_row)
            used_cols.add(min_col)
        
        # Mark unmatched existing objects as disappeared
        for i, object_id in enumerate(object_ids):
            if i not in used_rows:
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
        
        # Register unmatched new detections
        for j, (cx, cy, det) in enumerate(input_centroids):
            if j not in used_cols:
                self._register(cx, cy, det, timestamp)
    
    def get_loiterers(self, threshold_seconds: float = 300) -> List[Dict]:
        """
        Get objects that have been stationary for too long.
        
        Args:
            threshold_seconds: Time threshold for loitering (default 5 minutes)
            
        Returns:
            List of loitering objects with duration
        """
        loiterers = []
        
        for object_id, obj in self.objects.items():
            if obj["class_name"] != "person":
                continue
            
            duration = (obj["last_seen"] - obj["first_seen"]).total_seconds()
            
            if duration >= threshold_seconds:
                # Check if position has changed significantly
                positions = obj["positions"]
                if len(positions) >= 2:
                    first_pos = positions[0][:2]
                    last_pos = positions[-1][:2]
                    
                    distance = np.sqrt(
                        (last_pos[0] - first_pos[0])**2 + 
                        (last_pos[1] - first_pos[1])**2
                    )
                    
                    # If moved less than 50 pixels, consider loitering
                    if distance < 50:
                        loiterers.append({
                            "object_id": object_id,
                            "duration_seconds": duration,
                            "centroid": obj["centroid"],
                            "bbox": obj["bbox"]
                        })
        
        return loiterers
