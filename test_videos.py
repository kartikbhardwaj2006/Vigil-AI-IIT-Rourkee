"""
Quick test script to verify video files can be loaded with OpenCV
"""
import cv2
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent
DEMO_VIDEOS_PATH = PROJECT_ROOT / "demo-videos"

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

print("Testing demo videos...\n")
print("=" * 60)

for video_name in videos:
    video_path = DEMO_VIDEOS_PATH / video_name
    print(f"\n📹 Testing: {video_name}")
    print(f"   Path: {video_path}")
    print(f"   Exists: {video_path.exists()}")
    
    if video_path.exists():
        cap = cv2.VideoCapture(str(video_path))
        
        if cap.isOpened():
            # Read first frame
            ret, frame = cap.read()
            
            if ret:
                height, width = frame.shape[:2]
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                print(f"   ✅ Successfully opened!")
                print(f"   Resolution: {width}x{height}")
                print(f"   FPS: {fps:.1f}")
                print(f"   Frames: {frame_count}")
                print(f"   Duration: {duration:.1f}s")
            else:
                print(f"   ❌ Could not read first frame")
        else:
            print(f"   ❌ Could not open video file")
        
        cap.release()
    else:
        print(f"   ❌ File not found!")

print("\n" + "=" * 60)
print("\nTest complete!")
print("\nIf all videos show ✅, the backend should work correctly.")
print("If video3 shows ❌, there may be a file corruption issue.")