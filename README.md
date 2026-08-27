# VIGIL-AI

### Real-Time AI Surveillance & Movement Detection System

VIGIL-AI is an AI-powered real-time surveillance and video intelligence system designed to detect people, monitor movement, identify important events, and generate automated alerts from live video streams.

The project combines computer vision, object detection, movement analysis, privacy-preserving processing, and real-time alert mechanisms to transform conventional video surveillance into an intelligent monitoring system.

> 🏆 **Hackathon Finalist — IIT Roorkee**

---

## 🚀 Key Features

- 👤 **Real-Time Person Detection**: Detects people from live video streams using AI-based object detection (YOLOv8).
- 🏃 **Movement Detection & Monitoring**: Tracks movement within the monitored environment and identifies unusual events.
- 🎯 **Intelligent Event Detection**: Processes video streams to identify predefined surveillance events.
- 🔒 **Privacy-Preserving Surveillance**: Applies real-time face blurring to protect individual privacy while retaining useful scene information.
- 🚨 **Automated Alerts**: Generates visual and voice alerts when critical events are detected.
- 🖥️ **Monitoring Dashboard**: A centralized web interface for viewing live feeds, analytics, and monitoring detected events.

---

## 🧠 System Overview

```text
                ┌─────────────────────┐
                │   Camera / Video    │
                │       Stream        │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Video Processing  │
                │      OpenCV         │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Object Detection  │
                │    YOLO + OpenCV    │
                └──────────┬──────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Person         Movement       Event
       Detection       Analysis      Detection
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Privacy Protection  │
                │    Face Blurring    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Alert Generation   │
                │ Visual + Voice      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Monitoring Dashboard│
                └─────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.8+** (for the backend)
- **Node.js 16+** (for the frontend dashboard)

### 2. Add Your Videos (Optional)
Copy your video files (`video1.mp4`, `video2.mp4`, etc.) into the `demo-videos` directory to simulate live camera feeds.

### 3. Installation
**Backend Setup:**
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate
pip install -r requirements.txt
```

**Frontend Setup:**
```bash
cd frontend
npm install
```

### 4. Running the Application
Open two separate terminals:

**Terminal 1 (Backend):**
```bash
cd backend
venv\Scripts\activate
python main.py  # or run start_backend.bat on Windows
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev     # or run start_frontend.bat on Windows
```

Access the dashboard at: `http://localhost:5173`

### 5. Adding Cameras / Feeds
You can add cameras by running the `ADD_CAMERAS.bat` script on Windows or using the API directly to register video sources (webcams or video files from `demo-videos/`).

---

## 📚 Documentation & Guides

For more detailed setup and deployment instructions, check out the following guides:
- [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - Detailed deployment guide.
- [HOW_TO_RUN.md](HOW_TO_RUN.md) - Complete run guide.
- [QUICKSTART.md](QUICKSTART.md) - In-depth setup instructions.
- [START_HERE.md](START_HERE.md) - 5-minute quick start steps.

---

## 📄 License
This project is licensed under the terms of the license file included in the repository.