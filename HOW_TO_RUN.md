# 🎥 VIGIL - Complete Setup & Run Guide

> **Quick Setup:** From adding videos to running the system

---

## 📁 STEP 1: Add Your Demo Videos

1. **Place your videos** in the `demo-videos` folder:
   ```
   project14feb/
   └── demo-videos/
       ├── video1.mp4  ← Your first video
       ├── video2.mp4  ← Your second video
       └── video3.mp4  ← Your third video
   ```

2. **Video Requirements:**
   - Format: MP4, AVI, MOV, or MKV
   - Any resolution (720p, 1080p recommended)
   - Any duration (will loop automatically)

---

## ⚙️ STEP 2: Install Dependencies (First Time Only)

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend

# Install packages
npm install
```

### Database Setup (Choose One)

**Option A: SQLite (Easiest - No Setup)**
```bash
# Edit backend/.env
DATABASE_URL=sqlite+aiosqlite:///./vigil.db
```

**Option B: MySQL**
```bash
# Create database in MySQL
mysql -u root -p
CREATE DATABASE vigil_db;
exit;

# Edit backend/.env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/vigil_db
```

---

## ▶️ STEP 3: Start VIGIL

### Terminal 1 - Start Backend
```bash
# Double-click or run:
start_backend.bat

# Wait for: "✅ VIGIL Backend started successfully"
```

### Terminal 2 - Start Frontend
```bash
# Double-click or run:
start_frontend.bat

# Wait for: "Local: http://localhost:5173"
```

### Terminal 3 - Access Dashboard
```bash
# Open in browser:
http://localhost:5173
```

---

## 🎬 STEP 4: Add Cameras (Choose Your Source)

You have **2 options** to add cameras:

### **Option A: Interactive Menu (Easiest)**

```bash
# Run the setup script:
ADD_CAMERAS.bat

# Then choose:
# [1] Live Webcam
# [2] Demo Video 1
# [3] Demo Video 2
# [4] Demo Video 3
# [5] All 3 Demo Videos at once
```

### **Option B: Manual API Calls**

**For Live Webcam:**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\":\"webcam-1\",\"name\":\"Live Webcam\",\"stream_url\":\"0\",\"is_active\":true}"
```

**For Demo Video 1:**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\":\"demo-1\",\"name\":\"Demo Video 1\",\"stream_url\":\"demo-videos/video1.mp4\",\"is_active\":true}"
```

**For Demo Video 2:**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\":\"demo-2\",\"name\":\"Demo Video 2\",\"stream_url\":\"demo-videos/video2.mp4\",\"is_active\":true}"
```

**For Demo Video 3:**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\":\"demo-3\",\"name\":\"Demo Video 3\",\"stream_url\":\"demo-videos/video3.mp4\",\"is_active\":true}"
```

---

## ✅ STEP 5: Verify It's Working

1. **Open Dashboard**: http://localhost:5173

2. **Check Live View**:
   - Go to "Live View" page
   - You should see your camera/video streams
   - **VERIFY**: Faces are blurred in real-time ✅

3. **Check Alerts**:
   - Go to "Alerts" page
   - Should see any detected events

4. **Trigger a Test Alert**:
   ```bash
   # Simulate crowd detection
   curl -X POST http://localhost:8000/api/demo/simulate-crowd
   
   # Check Alerts page - should see new alert
   ```

---

## 🎯 Complete Workflow Summary

```bash
# 1. Add videos to demo-videos/ folder
# (Copy your video1.mp4, video2.mp4, video3.mp4 there)

# 2. Start Backend (Terminal 1)
start_backend.bat

# 3. Start Frontend (Terminal 2)
start_frontend.bat

# 4. Add Cameras (Terminal 3)
ADD_CAMERAS.bat
# Choose option 5 to add all 3 videos

# 5. Open Dashboard
# Browser: http://localhost:5173

# 6. View Live Streams
# Click "Live View" - see all 3 video feeds with privacy blur

# 7. Monitor Alerts
# Click "Alerts" - see real-time detections
```

---

## 🔍 How to Check Each Feature

### Privacy Verification
- **Go to**: Live View page
- **Expected**: All faces should be blurred
- **Fail If**: Any unblurred faces visible

### Crowd Detection
- **Method 1** (Simulated):
  ```bash
  curl -X POST http://localhost:8000/api/demo/simulate-crowd
  ```
- **Method 2** (Real): Have 15+ people in camera view
- **Expected**: Alert appears with "Crowd density" event

### Zone Intrusion
- **Go to**: Live View → Click camera
- **Click**: "Define Zone" button
- **Draw**: Polygon on video
- **Save**: Zone configuration
- **Test**: Walk into zone
- **Expected**: Alert with "Zone intrusion" event

### Analytics
- **Go to**: Analytics page
- **Check**: Charts showing hourly alert counts
- **Check**: Camera activity heatmap

### Audit Log
- **Go to**: Audit Log page
- **Action**: Acknowledge an alert
- **Check**: Action appears in audit log with timestamp

---

## 🛠️ Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Video not found error
```bash
# Make sure videos are in correct location:
# project14feb/demo-videos/video1.mp4

# Check file name matches exactly (case-sensitive)
```

### Webcam not detected
```bash
# Try different camera indexes:
# stream_url: "0"  ← Try this first
# stream_url: "1"  ← If 0 doesn't work
# stream_url: "2"  ← If 1 doesn't work
```

### No faces in video
```bash
# VIGIL works best with videos containing people
# Make sure your videos show people/faces
# The system will only blur detected faces
```

---

## 🎬 Demo Mode Tips

### For Presentations:
1. Use all 3 demo videos (looks impressive)
2. Pre-configure zones on videos
3. Have some alerts already in system
4. Open multiple browser tabs to show different pages

### Best Video Content:
- **Video 1**: Crowded area (mall, station)
- **Video 2**: Restricted area scenario
- **Video 3**: Normal monitoring scene

---

## 📊 What You'll See

### Dashboard
- Active camera count
- Recent alerts feed
- Risk level distribution
- Activity timeline

### Live View
- Multi-camera grid (1-9 cameras)
- Real-time anonymized streams
- Privacy indicator badges
- Camera status overlays

### Alerts Page
- Real-time alert feed
- Filter by camera, risk level, date
- Acknowledge/dismiss controls
- Detailed explanations

### Analytics
- Hourly alert distribution chart
- Camera activity heatmap
- Event type breakdown
- Risk score trends

---

## ✅ Final Checklist

Before demo:

- [ ] Videos placed in `demo-videos/` folder
- [ ] Backend started (no errors)
- [ ] Frontend started (loads successfully)
- [ ] Cameras added via `ADD_CAMERAS.bat`
- [ ] Live View shows video streams
- [ ] Faces are blurred in streams
- [ ] Alerts page working
- [ ] Analytics charts loading

---

## 🚀 You're Ready!

Your system is now configured to run with either:
- ✅ Live webcam for real-time testing
- ✅ Demo videos for presentations

**To switch sources**: Just add the camera type you want using `ADD_CAMERAS.bat`

**To remove cameras**: 
```bash
curl -X DELETE http://localhost:8000/api/cameras/{camera_id}
```

---

**Need help?** Check `QUICKSTART.md` for detailed troubleshooting.
