# 🚀 VIGIL - 5-Minute Quick Start

## Step-by-Step: Get VIGIL Running NOW

### 1️⃣ Add Your Videos (30 seconds)
```
📁 Open folder: demo-videos
📋 Copy your files:
   - video1.mp4
   - video2.mp4
   - video3.mp4
```

### 2️⃣ Install (First Time Only - 5 minutes)
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3️⃣ Start VIGIL (30 seconds)
```bash
# Terminal 1
start_backend.bat

# Terminal 2
start_frontend.bat
```

### 4️⃣ Add Cameras (30 seconds)
```bash
# Terminal 3
ADD_CAMERAS.bat
# Choose option 5 (all 3 videos)
```

### 5️⃣ Open Dashboard
```
🌐 Browser: http://localhost:5173
```

---

## ✅ What You'll See

1. **Dashboard** → Overview with stats
2. **Live View** → 3 video streams (faces blurred)
3. **Alerts** → Real-time event notifications
4. **Analytics** → Charts and graphs

---

## 🎯 Quick Test

After starting, verify:

```bash
# Trigger test alert
curl -X POST http://localhost:8000/api/demo/simulate-crowd

# Check: Alert should appear on Dashboard within 1 second
```

---

## 🎥 Camera Options

| Option | Source | Use Case |
|--------|--------|----------|
| **Webcam** | `0` | Live testing |
| **Video 1** | `demo-videos/video1.mp4` | Crowd scenes |
| **Video 2** | `demo-videos/video2.mp4` | Zone intrusion |
| **Video 3** | `demo-videos/video3.mp4` | Normal monitoring |

---

## 🐛 Problems?

**Backend error?**
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend error?**
```bash
cd frontend
npm install
```

**Video not found?**
- Check files are in `demo-videos/` folder
- Check exact names: `video1.mp4`, `video2.mp4`, `video3.mp4`

---

## 📚 Full Documentation

- **Complete Guide**: `HOW_TO_RUN.md`
- **Setup Details**: `QUICKSTART.md`
- **System Overview**: `README.md`
- **Implementation**: `implementation_plan.md`

---

**That's it! Your privacy-preserving video intelligence system is running! 🎉**
