# Property Data Quality Dashboard - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Verify Prerequisites

Ensure you have:
- ✅ Python 3.8+ installed
- ✅ FastAPI and dependencies installed
- ✅ Access to Supabase production database
- ✅ Modern web browser (Chrome, Firefox, Edge)

### Step 2: Start the API Server

Open a terminal and run:

```bash
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
python production_property_api.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify it's working:**
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "total_properties": 9113150,
  "is_production_dataset": true
}
```

### Step 3: Open the Dashboard

**Option A: Via Local Dev Server (Recommended)**

If you have the web app running:
```
http://localhost:5191/property-data-quality-dashboard.html
```

**Option B: Direct File Access**

Open in your browser:
```
file:///C:/Users/gsima/Documents/MyProject/ConcordBroker/apps/web/public/property-data-quality-dashboard.html
```

**Note:** Direct file access may have CORS restrictions. Use Option A if possible.

---

## 📊 What You Should See

### Dashboard Loads Successfully

1. **Summary Cards** showing:
   - Total Properties: ~9.1M
   - NULL Values: Count of unclassified properties
   - NULL Percentage: Should be < 50%
   - Unique Types: ~100+ property classifications
   - Quality Score: 0-100 rating

2. **Quality Meter** with color-coded score:
   - 🟢 Green (90-100): Excellent
   - 🔵 Blue (75-90): Good
   - 🟡 Yellow (60-75): Fair
   - 🔴 Red (0-60): Poor

3. **Charts**:
   - Pie chart showing top 10 property types
   - Bar chart showing top 20 types with counts

4. **Tables**:
   - Missing/unusual mappings requiring attention
   - Recent changes timeline

### Real-Time Features

- Auto-refreshes every 5 minutes
- Manual refresh button in top-right
- Export to CSV functionality
- Live status indicator (green dot)

---

## 🔧 Troubleshooting

### Problem: "No API server found"

**Solution:**
1. Check if Python API is running: `curl http://localhost:8000/health`
2. If not running, start it: `python production_property_api.py`
3. Click "Retry Connection" on dashboard

### Problem: "Failed to load data quality metrics"

**Cause:** API endpoint missing or error

**Solution:**
1. Verify endpoint exists:
   ```bash
   curl http://localhost:8000/api/properties/data-quality
   ```

2. Check API logs for errors

3. Ensure Supabase connection is working

### Problem: Charts not displaying

**Cause:** Chart.js not loading or data format issue

**Solution:**
1. Check browser console for JavaScript errors (F12)
2. Verify internet connection (Chart.js loads from CDN)
3. Try hard refresh (Ctrl+Shift+R)

### Problem: CORS errors (if using file:// protocol)

**Cause:** Browser security restrictions

**Solution:**
Use local dev server instead:
```bash
cd apps/web
npm run dev
# Then access at http://localhost:5191/property-data-quality-dashboard.html
```

---

## 🧪 Testing the API Directly

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

### Test Data Quality Endpoint
```bash
curl http://localhost:8000/api/properties/data-quality
```

### Test with Python
```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# Data quality
response = requests.get('http://localhost:8000/api/properties/data-quality')
data = response.json()

print(f"Total Properties: {data['summary']['total_properties']:,}")
print(f"NULL Percentage: {data['summary']['null_percentage']:.2f}%")
print(f"Quality Score: {data['summary']['quality_score']:.1f}/100")
```

---

## 📈 Expected Metrics (Current State)

Based on the 9.1M property dataset:

**Baseline Metrics:**
- Total Properties: 9,113,150
- NULL Count: ~3,962,000 (43.5%)
- Unique Types: 100-150
- Quality Score: 60-70 (Fair)

**Top Property Types:**
1. Residential - Single Family (25-30%)
2. Vacant - Residential (10-15%)
3. Commercial - Retail (3-5%)
4. Condominium (5-8%)
5. Multi-Family (2-4%)

**Known Issues:**
- High NULL percentage (43.5% vs target 5%)
- Some unmapped DOR codes
- Inconsistent property type naming

**Improvement Goals:**
- Reduce NULL to < 20% in 30 days
- Reduce NULL to < 5% in 90 days
- Achieve Quality Score > 75 in 60 days
- Achieve Quality Score > 90 in 180 days

---

## 🎯 Key Features to Explore

### 1. Quality Score Analysis

The quality score combines:
- **50%** - NULL value percentage (lower is better)
- **30%** - Distribution balance (avoid heavy concentration)
- **20%** - Type completeness (more unique types is better)

### 2. Property Type Distribution

- **Pie Chart**: Visual breakdown of top 10 types
- **Bar Chart**: Detailed counts for top 20 types
- **Percentages**: Each type shows % of total properties

### 3. Missing Mappings Detection

Automatically identifies:
- Types with very low counts (< 100 properties)
- Unusual type names that may need review
- Potential unmapped DOR codes

### 4. Export Functionality

Click "Export CSV" to download:
- Full property type distribution
- Counts and percentages
- Timestamp of export
- Ready for Excel/Google Sheets

---

## 🔄 Using Auto-Refresh

The dashboard automatically refreshes every 5 minutes:

**What Gets Updated:**
- All summary statistics
- Chart data
- Missing mappings table
- Quality score and meter
- Timeline events

**Manual Refresh:**
Click the "Refresh" button anytime to update immediately.

**Disable Auto-Refresh:**
Refresh will stop if you close the browser tab. Re-opening starts it again.

---

## 💡 Tips for Best Results

1. **Keep API Running**: Dashboard requires API server to be active
2. **Monitor Quality Score**: Track trends over time
3. **Review Missing Mappings**: Weekly review helps catch issues early
4. **Export Regular Snapshots**: Save CSV exports for historical comparison
5. **Check Browser Console**: F12 developer tools show detailed logs

---

## 📝 Next Steps

After initial setup:

1. **Baseline Measurement**
   - Take screenshot of current dashboard
   - Export CSV with current data
   - Document starting quality score

2. **Identify Improvement Areas**
   - Review missing mappings table
   - Analyze NULL percentage by county (future feature)
   - Check distribution of property types

3. **Set Goals**
   - Define target quality score
   - Set NULL percentage reduction goals
   - Plan data mapping improvements

4. **Regular Monitoring**
   - Daily: Check quality score
   - Weekly: Review missing mappings
   - Monthly: Export and analyze trends

---

## 🆘 Getting Help

**Common Questions:**

Q: Why is my NULL percentage so high?
A: Many properties are not yet classified. This is expected and is being addressed through data mapping improvements.

Q: Can I filter by county?
A: Not yet - this is a planned feature for v1.1.

Q: How often is the data updated?
A: Dashboard shows real-time data from Supabase. Database is updated as property records change.

Q: Can I customize the refresh interval?
A: Currently fixed at 5 minutes. Customization planned for future release.

**Support Channels:**
- Check the main README: `PROPERTY_DATA_QUALITY_DASHBOARD_README.md`
- Review API logs for errors
- Browser console (F12) for frontend issues
- Test API endpoints with curl

---

## ✅ Success Checklist

You know everything is working when:

- [ ] API health check returns status: "healthy"
- [ ] Dashboard loads without errors
- [ ] All 5 summary cards show data
- [ ] Quality meter displays a score
- [ ] Both charts render with data
- [ ] Missing mappings table loads
- [ ] Export CSV downloads successfully
- [ ] Auto-refresh updates after 5 minutes
- [ ] Timeline shows recent events
- [ ] No errors in browser console (F12)

---

**Dashboard Version:** 1.0.0
**Last Updated:** January 2025
**Maintained By:** ConcordBroker Development Team
