# Property Data Quality Dashboard - User Guide

## Overview

Real-time monitoring dashboard for tracking property type distribution and data completeness across 9.1M Florida properties.

## Quick Start

### 1. Start the Backend API

```bash
# Navigate to project root
cd C:\Users\gsima\Documents\MyProject\ConcordBroker

# Start the production property API (port 8000)
python production_property_api.py
```

### 2. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5191/property-data-quality-dashboard.html
```

Or if running a local server:
```
file:///C:/Users/gsima/Documents/MyProject/ConcordBroker/apps/web/public/property-data-quality-dashboard.html
```

## Features

### Real-Time Metrics

**Summary Statistics:**
- **Total Properties**: Complete count of all Florida parcels in database
- **NULL Values**: Count of properties with unclassified/missing property types
- **NULL Percentage**: Percentage of unclassified properties (Target: < 5%)
- **Unique Types**: Number of distinct property classifications
- **Quality Score**: Overall data quality rating (0-100)

**Quality Score Breakdown:**
- **Excellent (90-100)**: Outstanding data quality
- **Good (75-90)**: Solid data quality with minor improvements possible
- **Fair (60-75)**: Needs improvement
- **Poor (0-60)**: Significant issues requiring immediate action

### Visualizations

**1. Property Type Distribution (Pie Chart)**
- Shows top 10 property types by count
- Interactive labels with percentages
- Hover for detailed statistics

**2. Top 20 Property Types (Bar Chart)**
- Horizontal bar chart of top 20 types
- Sorted by property count
- Shows exact counts and percentages

### Data Tables

**Missing or Unusual Mappings**
- Lists property types with low counts (< 100 properties)
- Identifies potential unmapped values
- Highlights data quality issues

**Recent Changes Timeline**
- Tracks all data refreshes
- Shows errors and warnings
- Maintains last 10 events

## Usage Instructions

### Manual Refresh

Click the **"Refresh"** button in the top-right corner to manually reload data.

### Auto-Refresh

Dashboard automatically refreshes every **5 minutes** to keep data current.

### Export Data

Click the **"Export CSV"** button to download current property type distribution as a CSV file.

**CSV Format:**
```csv
Property Type,Count,Percentage
"Residential - Single Family",2450000,26.89
"Commercial - Retail",450000,4.94
...
```

## Backend API Endpoint

### GET /api/properties/data-quality

Returns comprehensive data quality statistics.

**Response Schema:**
```json
{
  "summary": {
    "total_properties": 9113150,
    "null_count": 3962000,
    "null_percentage": 43.48,
    "unique_types": 127,
    "quality_score": 68.5
  },
  "property_type_distribution": [
    {
      "type": "Residential - Single Family",
      "count": 2450000,
      "percentage": 26.89
    }
  ],
  "missing_mappings": [
    {
      "type": "Unknown Type",
      "count": 45,
      "issue": "Low count - possible unmapped value"
    }
  ],
  "metadata": {
    "response_time_ms": 1250,
    "timestamp": "2025-01-15T10:30:00.000Z",
    "target_null_percentage": 5.0,
    "quality_thresholds": {
      "excellent": 90,
      "good": 75,
      "fair": 60,
      "poor": 0
    }
  }
}
```

## Quality Score Calculation

The quality score is calculated using three weighted factors:

1. **NULL Score (50% weight)**
   - Penalizes high NULL percentages
   - Formula: `max(0, 100 - (null_percentage * 2))`
   - Example: 20% NULL → 60 points

2. **Distribution Score (30% weight)**
   - Penalizes heavy concentration in single type
   - Formula: `max(0, 100 - max(0, top_type_percentage - 50))`
   - Example: Top type at 60% → 90 points

3. **Completeness Score (20% weight)**
   - Measures type coverage vs expected
   - Formula: `min(100, (unique_types / 100) * 100)`
   - Example: 80 unique types → 80 points

**Final Score:**
```
quality_score = (null_score * 0.5) + (distribution_score * 0.3) + (completeness_score * 0.2)
```

## Monitoring Goals

### Short-Term Targets (30 days)
- [ ] Reduce NULL percentage from 43.5% to < 20%
- [ ] Identify and map all unmapped property types
- [ ] Achieve "Good" quality score (75+)

### Long-Term Targets (90 days)
- [ ] Reduce NULL percentage to < 5%
- [ ] Achieve "Excellent" quality score (90+)
- [ ] Maintain 100+ unique property types
- [ ] Zero missing mappings

## Troubleshooting

### Dashboard Shows "Loading..."

**Problem:** Dashboard cannot connect to API

**Solutions:**
1. Verify API is running: `curl http://localhost:8000/health`
2. Check port 8000 is not in use
3. Review API logs for errors

### Data Quality Score is Low

**Problem:** Quality score < 60

**Actions:**
1. Review NULL percentage - primary factor
2. Check missing mappings table
3. Investigate top property type concentration
4. Run data mapping validation scripts

### Charts Not Displaying

**Problem:** Pie/bar charts are blank

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify Chart.js library loaded successfully
3. Ensure API returns valid data
4. Try clearing browser cache

### Export CSV Fails

**Problem:** CSV download doesn't work

**Solutions:**
1. Ensure data is loaded (check dashboard)
2. Try different browser
3. Check browser download settings
4. Verify popup blocker not interfering

## API Testing

### Test Backend Health
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "total_properties": 9113150,
  "is_production_dataset": true,
  "timestamp": "2025-01-15T10:30:00.000Z"
}
```

### Test Data Quality Endpoint
```bash
curl http://localhost:8000/api/properties/data-quality
```

### Test with Query Parameters
```bash
# Using production API
curl http://localhost:8000/api/properties/search?use=residential&limit=10
```

## Technical Details

### Technology Stack
- **Frontend**: HTML5, TailwindCSS, Chart.js
- **Backend**: FastAPI (Python), Supabase PostgreSQL
- **Data Source**: florida_parcels table (9.1M records)
- **Auto-Refresh**: JavaScript `setInterval` (5 minutes)

### Browser Requirements
- Modern browser with ES6+ support
- JavaScript enabled
- Chart.js 3.0+ compatible
- LocalStorage support (for future features)

### Performance
- **Initial Load**: ~2-3 seconds
- **Refresh Time**: ~1-2 seconds
- **API Response**: ~500-1500ms (depending on data volume)
- **Memory Usage**: ~50-100MB

## File Locations

**Dashboard:**
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\public\property-data-quality-dashboard.html
```

**Backend API:**
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\production_property_api.py
```

**Documentation:**
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\PROPERTY_DATA_QUALITY_DASHBOARD_README.md
```

## Future Enhancements

### Planned Features
- [ ] Historical trend tracking (weekly/monthly)
- [ ] Email alerts for quality score drops
- [ ] Automated data mapping suggestions
- [ ] Property type hierarchy visualization
- [ ] County-level quality breakdown
- [ ] Batch data correction tools
- [ ] Integration with data validation pipeline
- [ ] Mobile-responsive improvements

### Configuration Options
- [ ] Customizable refresh intervals
- [ ] Adjustable quality thresholds
- [ ] Dark mode support
- [ ] User preferences persistence

## Support

For issues or questions:
1. Check this README for troubleshooting steps
2. Review API logs in terminal
3. Verify database connection
4. Check browser console for errors

## Version History

**v1.0.0** (Current)
- Initial release
- Real-time data quality monitoring
- Property type distribution visualizations
- CSV export functionality
- Auto-refresh every 5 minutes
- Quality score calculation
- Missing mappings detection

---

**Last Updated:** January 2025
**Maintained By:** ConcordBroker Development Team
