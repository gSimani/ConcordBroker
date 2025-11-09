# ConcordBroker - Localhost Deployment Guide

**Date:** October 1, 2025
**Status:** Deployment In Progress

---

## 🚀 Current Status

### ✅ Frontend (Running)
- **Status:** ✓ Running successfully
- **URL:** http://localhost:5173
- **Technology:** Vite + React + TypeScript
- **Started with:** `npm run dev`
- **Location:** `apps/web/`

### ⚠️ Backend API (Issue Found)
- **Status:** Import error - needs fix
- **Expected URL:** http://localhost:8000
- **Technology:** FastAPI + Python
- **Issue:** Module import path configuration
- **Location:** `apps/api/`

### ✓ Database
- **Status:** Already configured
- **Type:** Supabase (Cloud)
- **Connection:** Active via .env

---

## 📋 Services Overview

### 1. Frontend - React/Vite App
```
Location: apps/web/
Port: 5173
Status: ✓ RUNNING
```

**Start Command:**
```bash
cd apps/web
npm run dev
```

**Available Scripts:**
- `npm run dev` - Development server
- `npm run dev:localhost` - Localhost-specific config
- `npm run build` - Production build
- `npm run preview` - Preview production build

### 2. Backend API - FastAPI
```
Location: apps/api/
Port: 8000
Status: ⚠️ NEEDS FIX
```

**Issue:** Import path configuration
**Error:** `ModuleNotFoundError: No module named 'routers'`

**Fix Required:**
The API imports need to use absolute imports from the `apps.api` package.

**Temporary Workaround:**
Add `PYTHONPATH` to include the project root:

```bash
# Windows
set PYTHONPATH=C:\Users\gsima\Documents\MyProject\ConcordBroker
cd apps/api
python -m uvicorn main:app --reload

# Or from project root
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
python -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Database - Supabase
```
Type: Cloud PostgreSQL
Status: ✓ CONFIGURED
```

Already connected via `.env`:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- DATABASE_URL

---

## 🔧 Quick Start (Fixed Commands)

### Option 1: Run Frontend Only (Working Now)

```bash
# Terminal 1: Frontend
cd C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web
npm run dev
```

**Access:** http://localhost:5173

### Option 2: Run Full Stack (After API Fix)

**Terminal 1: Frontend**
```bash
cd C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web
npm run dev
```

**Terminal 2: Backend (with PYTHONPATH fix)**
```bash
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
set PYTHONPATH=%CD%
cd apps\api
uvicorn main:app --reload --port 8000
```

---

## 🛠️ API Import Fix

The API has relative import issues. Here's how to fix permanently:

### Fix Option 1: Update Imports (Recommended)

Edit `apps/api/main.py` and all router files:

**Change from:**
```python
from routers import parcels, entities, health
from database import Database
```

**Change to:**
```python
from apps.api.routers import parcels, entities, health
from apps.api.database import Database
```

### Fix Option 2: Add __init__.py

Ensure `apps/__init__.py` and `apps/api/__init__.py` exist:

```bash
# Create if missing
echo. > apps\__init__.py
echo. > apps\api\__init__.py
```

### Fix Option 3: Use Poetry (If Available)

```bash
cd apps/api
poetry install
poetry run uvicorn main:app --reload
```

---

## 📁 Project Structure

```
ConcordBroker/
├── apps/
│   ├── web/                 # Frontend (Vite/React) ✓ Running
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── api/                 # Backend (FastAPI) ⚠️ Needs Fix
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── database.py
│   │   └── pyproject.toml
│   │
│   ├── workers/             # Background workers
│   ├── agents/              # AI agents
│   └── validation/          # UI validation system
│
├── .env                     # Environment variables
└── README.md
```

---

## 🌐 Access URLs (After Full Deploy)

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | http://localhost:5173 | ✓ Running |
| **API Docs** | http://localhost:8000/docs | ⏳ Pending Fix |
| **API Health** | http://localhost:8000/health | ⏳ Pending Fix |
| **Supabase** | https://pmispwtdngkcmsrsjwbp.supabase.co | ✓ Connected |

---

## ✅ What's Working

1. ✅ **Frontend Development Server**
   - Vite dev server running on port 5173
   - Hot module replacement (HMR) active
   - React app loading

2. ✅ **Environment Configuration**
   - .env file loaded
   - Supabase credentials configured
   - API keys available

3. ✅ **Database Connection**
   - Supabase cloud database active
   - Connection strings configured
   - Service role key available

---

## ⚠️ Known Issues

### Issue 1: API Import Errors
**Problem:** Relative imports failing
**Impact:** Backend API won't start
**Status:** Identified, fix available (see above)

### Issue 2: Module Path Configuration
**Problem:** Python can't find `routers` module
**Cause:** PYTHONPATH not set for project structure
**Solution:** Set PYTHONPATH or use absolute imports

---

## 🔍 Verification Steps

### 1. Check Frontend
```bash
# Should see Vite dev server
curl http://localhost:5173
```

**Expected:** HTML response with React app

### 2. Check API (After Fix)
```bash
# Should see API docs
curl http://localhost:8000/docs
```

**Expected:** Swagger UI documentation

### 3. Check Database
```bash
# Test Supabase connection
curl -X GET "https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/" \
  -H "apikey: YOUR_ANON_KEY"
```

**Expected:** API metadata response

---

## 📝 Next Steps

### Immediate (Now)

1. **Fix API Imports**
   - Choose one of the 3 fix options above
   - Update import statements
   - Test API start

2. **Restart API**
   ```bash
   cd apps/api
   uvicorn main:app --reload --port 8000
   ```

3. **Verify Both Services**
   - Frontend: http://localhost:5173
   - API: http://localhost:8000/docs

### Short Term (Today)

4. **Test Full Integration**
   - Verify frontend can call backend
   - Check database queries work
   - Test authentication flow

5. **Run Workers (Optional)**
   ```bash
   cd apps/workers
   python -m master_pipeline
   ```

### Long Term (This Week)

6. **Set Up Dev Containers** (Optional)
   - Docker Compose for local stack
   - Consistent dev environment

7. **Add Hot Reload**
   - API auto-reload on file changes
   - Frontend HMR already active

---

## 🐛 Troubleshooting

### Frontend Issues

**Port 5173 already in use:**
```bash
# Kill existing process
npx kill-port 5173
# Or use different port
npm run dev -- --port 5174
```

**Dependencies missing:**
```bash
cd apps/web
npm install
```

### Backend Issues

**Python module not found:**
```bash
# Set PYTHONPATH
set PYTHONPATH=C:\Users\gsima\Documents\MyProject\ConcordBroker

# Or use absolute path
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
python -m apps.api.main
```

**Port 8000 already in use:**
```bash
# Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn main:app --port 8001
```

### Database Issues

**Connection refused:**
- Check internet connection (Supabase is cloud)
- Verify SUPABASE_URL in .env
- Check SERVICE_ROLE_KEY is correct

---

## 🚀 Production Deployment

This project is configured for:
- **Frontend:** Vercel (https://www.concordbroker.com)
- **Backend:** Railway (concordbroker.railway.app)
- **Database:** Supabase (Cloud PostgreSQL)

See deployment configuration in:
- `.github/workflows/` - CI/CD pipelines
- `vercel.json` - Vercel config
- `railway.json` - Railway config

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs (after fix)
- **Frontend Components:** `apps/web/src/components/`
- **API Routes:** `apps/api/routers/`
- **Environment Config:** `.env`
- **Validation System:** `apps/validation/README.md`

---

## ✅ Deployment Checklist

- [x] Frontend dependencies installed
- [x] Frontend dev server started
- [x] Environment variables configured
- [x] Database connection verified
- [ ] API import issues fixed
- [ ] Backend server started
- [ ] Full stack integration tested
- [ ] Optional: Workers started

---

**Current Status: Frontend Running, API Needs Import Fix**

**Next Action:** Apply one of the API import fixes above and restart the backend server.
