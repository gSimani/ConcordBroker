# 🚀 ConcordBroker Localhost Setup Guide

This guide will help you set up and populate your database for local development.

---

## Prerequisites

- ✅ Python 3.12+ installed
- ✅ Node.js 18+ installed
- ✅ Supabase account with project created
- ✅ Environment variables configured (.env file)

---

## Step 1: Configure Environment Variables

### 1.1 Create .env file
```bash
# If you have .env.new with updated credentials
mv .env.new .env

# Or copy from example
cp .env.example .env
```

### 1.2 Required Variables
Your `.env` must have these values from Supabase:
```env
SUPABASE_URL=https://[your-project].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...your-service-key
DATABASE_URL=postgres://postgres.[project]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Get these from:
1. Supabase Dashboard → Settings → API
2. Copy the URL and service_role key
3. Settings → Database → Connection string

---

## Step 2: Install Dependencies

### 2.1 Backend (Python)
```bash
cd apps/api
pip install -r requirements.txt
pip install supabase pandas python-dotenv

# If you get the proxy error, the fix is already in supabase_client.py
```

### 2.2 Frontend (Node.js)
```bash
cd apps/web
npm install
```

---

## Step 3: Create Database Tables

### Option A: Using Supabase Dashboard (Recommended)
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to SQL Editor
4. Copy contents of `apps/api/supabase_schema.sql`
5. Paste and click "Run"

### Option B: Using Setup Script
```bash
python setup_database.py
# Choose option 1: Create database tables
```

---

## Step 4: Load Data into Database

### 4.1 Prepare Data Files
Make sure you have these CSV files in the root directory:
- `NAP16P202501.csv` - Parcel attributes (19MB)
- `SDF16P202501.csv` - Sales data (13MB)

### 4.2 Run Data Loading Script
```bash
python setup_database.py
```

Choose options:
1. **Option 2**: Load Florida parcel data (loads first 1000 records)
2. **Option 3**: Load sales data
3. **Option 4**: Verify data was loaded

For full data load, edit `setup_database.py` and remove `nrows=1000` limit.

### 4.3 Alternative: Load via Supabase Dashboard
1. Go to Table Editor in Supabase
2. Select `florida_parcels` table
3. Click "Import data from CSV"
4. Upload your CSV files

---

## Step 5: Start Local Development

### Quick Start (All Services)
```powershell
# Run the startup script
.\start-localhost.ps1
```

This will:
- Check ports
- Start API server (port 8000)
- Start web server (port 5173)
- Optionally set up database

### Manual Start

#### Terminal 1: API Server
```bash
cd apps/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Web Server
```bash
cd apps/web
npm run dev
```

---

## Step 6: Verify Everything Works

### 6.1 Check API
- Open: http://localhost:8000/docs
- You should see the FastAPI documentation
- Try the `/health` endpoint

### 6.2 Check Database Connection
```bash
cd apps/api
python supabase_client.py
```

Should output:
```
Connection successful!
Florida parcels table count: [number]
```

### 6.3 Check Web App
- Open: http://localhost:5173
- Should load the React app
- Check browser console for errors

### 6.4 Test Data Query
```bash
python -c "
from apps.api.supabase_client import get_supabase_client
client = get_supabase_client()
result = client.table('florida_parcels').select('*').limit(5).execute()
print(f'Found {len(result.data)} parcels')
for p in result.data:
    print(f'  - {p.get(\"parcel_id\")}: {p.get(\"owner_name\")}')
"
```

---

## Troubleshooting

### Issue: "relation public.florida_parcels does not exist"
**Solution**: Tables not created. Run the schema SQL in Supabase dashboard.

### Issue: Supabase connection "proxy" error
**Solution**: Already fixed in `apps/api/supabase_client.py`. Make sure you're using this file.

### Issue: Port already in use
**Solution**: 
```powershell
# Find process on port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual number)
taskkill /PID [PID] /F
```

### Issue: No data showing in app
**Solution**:
1. Check if data exists: `python setup_database.py` → Option 4
2. Check API logs for errors
3. Verify CORS settings in `apps/api/config.py`

### Issue: CORS errors
**Solution**: Update `apps/api/config.py`:
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default
]
```

---

## Data Structure

### Florida Parcels Table
Main fields populated from CSV:
- `parcel_id` - Unique parcel identifier
- `owner_name` - Property owner
- `phy_addr1` - Physical address
- `just_value` - Just/market value
- `assessed_value` - Assessed value
- `taxable_value` - Taxable value
- `year_built` - Year built
- `total_living_area` - Square footage
- `sale_date` - Last sale date
- `sale_price` - Last sale price

---

## API Endpoints

Once running, these endpoints are available:

### Properties
- `GET /api/properties` - List all properties
- `GET /api/properties/{id}` - Get specific property
- `GET /api/properties/search` - Search properties

### Health Check
- `GET /health` - API health status
- `GET /docs` - Interactive API documentation

---

## Next Steps

1. **Full Data Load**: Remove the `nrows=1000` limit in `setup_database.py` to load all data
2. **Add Indexes**: Run index creation SQL for better performance
3. **Enable Caching**: Set up Redis for caching (optional)
4. **Add Authentication**: Implement user authentication

---

## Quick Commands Reference

```bash
# Start everything
.\start-localhost.ps1

# Load database
python setup_database.py

# Test connection
python apps/api/supabase_client.py

# Start API only
cd apps/api && uvicorn main:app --reload

# Start web only
cd apps/web && npm run dev

# Check logs
vercel logs  # For production
```

---

## Support

If you encounter issues:
1. Check the logs in each terminal
2. Verify your .env file has correct values
3. Ensure Supabase project is active
4. Check network connectivity

---

**Last Updated**: September 5, 2025  
**Status**: Ready for local development