# VIGIL - Quick Start Guide

> Get VIGIL running in under 10 minutes

---

## 🚀 Prerequisites

Before starting, ensure you have:

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **MySQL 8.0** (or use SQLite for demo)
- **Webcam or video file** (for testing)

---

## 📦 Installation

### Step 1: Install Backend Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
copy .env.example .env

# Edit .env with your settings
# For SQLite demo: DATABASE_URL=sqlite+aiosqlite:///./vigil.db
# For MySQL: DATABASE_URL=mysql+pymysql://root:password@localhost:3306/vigil_db
```

### Step 3: Setup Database

**Option A: SQLite (Fastest - No Setup)**
- Database will auto-create on first run
- No additional setup needed

**Option B: MySQL (Production)**
```bash
mysql -u root -p
CREATE DATABASE vigil_db CHARACTER SET utf8mb4;
exit;
```

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## ▶️ Running VIGIL

### Quick Start (Windows)

**Terminal 1 - Backend:**
```bash
# Double-click or run:
start_backend.bat
```

**Terminal 2 - Frontend:**
```bash
# Double-click or run:
start_frontend.bat
```

### Manual Start

**Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## 🎯 Access Points

Once running, access:

- **Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## 🎥 Testing the System

### 1. Add a Camera

**Via UI:**
1. Open Dashboard → Settings → Cameras
2. Click "Add Camera"
3. Enter:
   - **Camera ID**: `webcam-1`
   - **Name**: `Test Webcam`
   - **Source**: `0` (default webcam index)
   - Check "Enable"
4. Click Save

**Via API (curl):**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\":\"webcam-1\",\"name\":\"Test Webcam\",\"stream_url\":\"0\",\"is_active\":true}"
```

### 2. View Live Stream

1. Navigate to **Live View** page
2. Your webcam feed should appear (with face blur applied)
3. Verify: **Faces should be blurred in real-time**

### 3. Test Crowd Detection

**Simulated (No Camera):**
```bash
curl -X POST http://localhost:8000/api/demo/simulate-crowd
```

**Manual (With Camera):**
- Gather 15+ people in camera view
- Alert should appear on Dashboard within seconds

### 4. Test Zone Intrusion

1. Go to **Live View** → Click camera
2. Click "Define Zone"
3. Draw polygon around restricted area
4. Save zone
5. Walk into zone → Alert should trigger

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Database connection shows "connected" in logs
- [ ] YOLOv8 model downloaded (auto-downloads on first run)
- [ ] Webcam stream visible in Live View
- [ ] Faces are blurred in stream
- [ ] Alerts appear in Alerts page
- [ ] WebSocket shows "Connected" in browser console

---

## 🐛 Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
- **Fix:** Activate venv and run `pip install -r requirements.txt`

**Error:** `MySQL connection refused`
- **Fix:** Check MySQL is running, or switch to SQLite in `.env`

### Frontend won't start

**Error:** `node: command not found`
- **Fix:** Install Node.js from https://nodejs.org

**Error:** `Cannot find module`
- **Fix:** Run `npm install` in frontend directory

### Webcam not detected

**Error:** Stream shows black screen
- **Fix:** Try different source values (0, 1, 2) in camera config
- **Fix:** Check webcam permissions in Windows Settings

### YOLOv8 download fails

**Manual download:**
```bash
mkdir -p %USERPROFILE%\.cache\ultralytics
cd %USERPROFILE%\.cache\ultralytics
# Download from: https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

---

## 🧪 Running Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test suites
pytest tests/test_anonymizer.py -v
pytest tests/test_alerts.py -v
```

---

## 📊 Demo Mode (No Cameras)

For presentations without live cameras:

```bash
# Add demo camera with video file
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\":\"demo-1\",\"name\":\"Demo Feed\",\"stream_url\":\"./demo-video.mp4\"}"

# Or simulate events
curl -X POST http://localhost:8000/api/demo/simulate-crowd
curl -X POST http://localhost:8000/api/demo/simulate-intrusion
```

---

## ⚙️ Configuration

Edit `backend/app/core/config.py` or `.env` to customize:

```python
# Detection thresholds
CROWD_THRESHOLD = 15              # Persons to trigger crowd alert
LOITER_THRESHOLD_MINUTES = 5      # Minutes for loitering
CONFIDENCE_THRESHOLD = 0.5        # YOLO confidence

# Privacy settings
DEFAULT_ANONYMIZATION = True      # Always anonymize
FACE_BLUR_INTENSITY = 51         # Blur strength (odd number)
```

---

## 🔒 Privacy Verification

**Critical Privacy Test:**

1. Start webcam feed
2. Stand in front of camera
3. **VERIFY:** Your face is blurred immediately
4. **FAIL IF:** Any frame shows unblurred faces

To manually test blur:
```python
python backend/app/ml/anonymizer.py
```

---

## 📝 Next Steps

After successful setup:

1. ✅ Read `implementation_plan.md` for full architecture details
2. ✅ Review `/about` page for ethical guidelines
3. ✅ Test all detection types (crowd, intrusion, loitering)
4. ✅ Configure zones for your use case
5. ✅ Review audit logs to verify accountability

---

## 🆘 Getting Help

- **Issue:** System not working? Check error logs in terminal
- **Documentation:** See `implementation_plan.md`
- **API Docs:** http://localhost:8000/docs (interactive testing)

---

**Ready to run VIGIL? Start with `start_backend.bat` and `start_frontend.bat`!**
