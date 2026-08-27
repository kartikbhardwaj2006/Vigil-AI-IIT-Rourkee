# 🚀 VIGIL Backend - Complete Startup Guide (Windows + VS Code)

## ✅ Prerequisites
- Python 3.10 installed
- Node.js installed (for frontend)
- Git Bash or PowerShell

---

## 📦 STEP 1: Setup Python Virtual Environment

Open **PowerShell** or **Git Bash** in VS Code terminal, then navigate to backend folder:

```powershell
cd d:\project14feb\backend
```

### Create Virtual Environment
```powershell
python -m venv venv
```

### Activate Virtual Environment

**For PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**For Git Bash:**
```bash
source venv/Scripts/activate
```

**Note:** If you get execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📥 STEP 2: Install Python Dependencies

With venv activated:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI
- SQLAlchemy with aiosqlite (async SQLite)
- Pydantic v2 + pydantic-settings
- YOLOv8 + MediaPipe
- All other dependencies

---

## 🗃️ STEP 3: Verify Environment Configuration

Your `.env` file is already configured with:
- ✅ SQLite async database (`sqlite+aiosqlite:///./vigil.db`)
- ✅ CORS origins for React frontend
- ✅ ML model paths

**No changes needed!** The file is production-ready.

---

## 🎯 STEP 4: Run the Backend Server

**Make sure you're in the backend folder with venv activated**, then run:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Expected Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Test Backend:
Open browser: **http://127.0.0.1:8000/docs**

You should see the FastAPI Swagger UI! 🎉

---

## ⚛️ STEP 5: Run the Frontend (React + Vite)

Open a **NEW terminal** in VS Code, then:

```powershell
cd d:\project14feb\frontend
npm install
npm run dev
```

### Expected Output:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Test Frontend:
Open browser: **http://localhost:5173**

---

## ✅ VERIFICATION CHECKLIST

- [ ] Backend running on `http://127.0.0.1:8000`
- [ ] Frontend running on `http://localhost:5173`
- [ ] No CORS errors in browser console
- [ ] No JSONDecodeError in backend logs
- [ ] No async database driver errors
- [ ] Swagger UI accessible at `http://127.0.0.1:8000/docs`

---

## 🐛 TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'aiosqlite'"
**Solution:**
```powershell
pip install aiosqlite
```

### Issue: "CORS policy error in browser"
**Solution:** Verify backend is running on `127.0.0.1:8000` and check `.env` has:
```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Issue: "Cannot activate venv in PowerShell"
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "Database locked" error
**Solution:** Stop all backend instances and delete `vigil.db` file, then restart.

---

## 🎬 QUICK START COMMANDS (Copy-Paste Ready)

### Terminal 1 (Backend):
```powershell
cd d:\project14feb\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 (Frontend):
```powershell
cd d:\project14feb\frontend
npm run dev
```

---

## 📝 NOTES

1. **Always activate venv** before running backend
2. **Backend must run on 127.0.0.1** (not 0.0.0.0) for CORS to work
3. **SQLite database** will be created automatically on first run
4. **ML models** will be downloaded automatically by YOLOv8 on first use

---

## 🔒 PRODUCTION DEPLOYMENT

When deploying to production:
1. Change `SECRET_KEY` in `.env` to a secure random string
2. Set `LOG_LEVEL=WARNING` or `ERROR`
3. Remove `--reload` flag from uvicorn command
4. Use proper WSGI server (gunicorn + uvicorn workers)
5. Configure SSL/TLS certificates
6. Use PostgreSQL or MySQL instead of SQLite

---

**System is now ready!** 🎉
