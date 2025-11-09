# 🚀 Running ConcordBroker on Localhost

## Quick Start (Windows)

### 1️⃣ **Install Prerequisites**
```powershell
# Install Python (3.9+)
# Download from https://www.python.org/downloads/

# Install Node.js (18+)
# Download from https://nodejs.org/

# Verify installations
python --version
node --version
npm --version
```

### 2️⃣ **Setup Environment**
1. Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

2. Edit `.env` with your Supabase credentials:
```
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
DATABASE_URL=your_database_url_here
```

### 3️⃣ **Install Dependencies**

#### API Dependencies:
```powershell
cd apps/api
pip install fastapi uvicorn python-dotenv supabase asyncpg pandas
cd ../..
```

#### Web Dependencies:
```powershell
cd apps/web
npm install
cd ../..
```

### 4️⃣ **Run the Application**

#### Option A: Use the Startup Script (Recommended)
```powershell
# From project root
.\start-dev.ps1
```

This will:
- ✅ Check for .env file
- ✅ Start API server on http://localhost:8000
- ✅ Start Web server on http://localhost:5173
- ✅ Open browser automatically

#### Option B: Run Manually

**Terminal 1 - API Server:**
```powershell
cd apps/api
python -m uvicorn main_dev:app --reload --port 8000
```

**Terminal 2 - Web Server:**
```powershell
cd apps/web
npm run dev
```

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Web App** | http://localhost:5173 | Main application |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **API Root** | http://localhost:8000 | API status and endpoints |

## 📱 Available Pages

### Main Application Pages:
- **Dashboard**: http://localhost:5173/dashboard
- **Property Search**: http://localhost:5173/properties
- **Analytics**: http://localhost:5173/analytics

### Property Routes (Address-Based):
- Search: `/properties`
- Property by ID: `/properties/123`
- Property by Address: `/properties/fort-lauderdale/123-main-st`
- Property by Parcel: `/properties/parcel/1234567890123`

## 🔍 Testing the Application

### 1. Check API Health:
```bash
curl http://localhost:8000/health
```

### 2. Test Property Search:
```bash
curl "http://localhost:8000/api/properties/search?city=Fort Lauderdale&limit=10"
```

### 3. View API Documentation:
Open http://localhost:8000/docs in your browser

## 🛠️ Troubleshooting

### Port Already in Use:
```powershell
# Kill process on port 8000 (API)
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F

# Kill process on port 5173 (Web)
netstat -ano | findstr :5173
taskkill /PID [PID_NUMBER] /F
```

### Missing Dependencies:
```powershell
# API
pip install -r apps/api/requirements.txt

# Web
cd apps/web && npm install
```

### CORS Issues:
Ensure the API is running and accessible at http://localhost:8000

### Database Connection:
1. Check `.env` file has correct Supabase credentials
2. Verify Supabase project is running
3. Check network connectivity

## 📊 Loading Sample Data

If you need to load NAL property data:

```powershell
# Setup import
python scripts/setup_import.py

# Run import (if you have NAL data file)
python scripts/import_nal_data.py TEMP/NAL16P202501.csv
```

## 🔐 Default Configuration

The development setup uses:
- **No authentication** for easier testing
- **CORS enabled** for localhost origins
- **Debug mode** enabled
- **Auto-reload** on file changes

## 📝 Development Tips

1. **API Changes**: The API auto-reloads when you save changes
2. **React Changes**: The web app hot-reloads automatically
3. **View Logs**: Check the terminal windows for debugging info
4. **API Testing**: Use the `/docs` endpoint for interactive API testing

## 🎯 Next Steps

1. **Explore Dashboard**: View property statistics and analytics
2. **Search Properties**: Test address-based search functionality
3. **View Property Details**: Click on any property to see full details
4. **Test API**: Use the Swagger UI at `/docs` to test endpoints

---

**Need Help?** 
- Check console logs in browser (F12)
- View API logs in the API terminal
- Ensure all dependencies are installed
- Verify Supabase credentials in `.env`