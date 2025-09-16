# Supabase Data Pipeline Setup Guide

## Complete setup instructions for ConcordBroker's Florida data pipeline with Supabase

### 🚀 Quick Start

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL and keys

2. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.supabase .env
   
   # Edit with your Supabase credentials
   nano .env
   ```

3. **Run Database Migration**
   ```bash
   # In Supabase SQL Editor, run:
   supabase/migrations/001_florida_data_schemas.sql
   ```

4. **Test Pipeline**
   ```bash
   python TEST_SUPABASE_PIPELINE.py
   ```

5. **Start Orchestrator**
   ```bash
   python apps/workers/supabase_orchestrator.py
   ```

---

## 📊 Data Sources & Agents

### Active Data Agents

| Agent | Data Source | Update Frequency | Records | Priority |
|-------|-------------|------------------|---------|----------|
| **TPP** | Florida Revenue TPP | Weekly | ~90,000 | High |
| **NAV** | Non Ad Valorem Assessments | Weekly | ~200,000 | High |
| **SDF** | Sales Data File | Daily | ~95,000 | Critical |
| **Sunbiz** | Florida Business Registry | Daily | Variable | Medium |
| **BCPA** | Broward Property Appraiser | Daily | ~600,000 | High |
| **Official Records** | County Records | Continuous | Millions | High |
| **DOR** | Department of Revenue | Monthly | ~1M | Medium |

### Key Features

- **Continuous Monitoring**: Checks for updates every hour
- **Auto-sync**: Automatically downloads when updates detected
- **Optimized Storage**: Indexed tables with materialized views
- **Alert System**: Real-time notifications for important updates
- **Distressed Property Tracking**: Identifies foreclosures and REO properties
- **Major Owner Detection**: Tracks institutional investors
- **Flip Opportunity Analysis**: Identifies rapid resale patterns

---

## 🔧 Detailed Setup

### 1. Supabase Project Configuration

1. **Create Tables**
   - Run migration script in SQL Editor
   - Verify tables created:
     - `fl_tpp_accounts`
     - `fl_nav_parcel_summary`
     - `fl_nav_assessment_detail`
     - `fl_sdf_sales`
     - `fl_data_updates`
     - `fl_agent_status`

2. **Enable Row Level Security**
   ```sql
   -- Already included in migration
   ALTER TABLE fl_tpp_accounts ENABLE ROW LEVEL SECURITY;
   ```

3. **Create API Keys**
   - Settings → API → Copy keys
   - Service Role key (for backend)
   - Anon key (for frontend)

### 2. Environment Variables

```bash
# Required Variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Optional Notification Settings
NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
NOTIFICATION_EMAIL=admin@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `supabase`
- `asyncpg`
- `aiohttp`
- `rich`
- `python-dotenv`
- `schedule`

### 4. Database Optimization

The migration includes:
- **Optimized Indexes**: For fast queries
- **Materialized Views**: Pre-computed analytics
- **Partitioning Ready**: For large datasets
- **Text Search**: Using PostgreSQL extensions

---

## 🎯 Key Discoveries from Data

### Critical Market Intelligence

1. **Bank Dominance**: 48.7% of Broward sales are financial institution resales
2. **Distressed Pipeline**: ~51% of all sales involve distressed properties
3. **Major Investors**: Invitation Homes owns 2,376+ properties
4. **CDD Properties**: Thousands of properties with special assessments
5. **Flip Opportunities**: Properties with 100%+ ROI in under 2 years

### Business Value

- **Early Warning System**: Detect market shifts before competitors
- **Investment Opportunities**: First access to distressed properties
- **Market Timing**: Track velocity and momentum indicators
- **Competitive Intelligence**: Monitor institutional activity

---

## 📈 Monitoring & Analytics

### Dashboard Queries

```sql
-- Market Summary
SELECT * FROM mv_market_summary_monthly 
WHERE county_number = '16' 
ORDER BY month DESC;

-- Top Property Owners
SELECT * FROM mv_top_property_owners 
LIMIT 20;

-- Recent Distressed Sales
SELECT * FROM mv_distressed_pipeline 
ORDER BY sale_date DESC 
LIMIT 50;

-- Agent Status
SELECT * FROM fl_agent_status 
ORDER BY last_run DESC;
```

### Alert Configuration

Alerts trigger for:
- New distressed properties (>10 in batch)
- Major owner activity (>100 properties)
- Bank sale surge (>60% of sales)
- Flip opportunities (>50% ROI)
- Agent failures

---

## 🚦 Running the Pipeline

### Manual Agent Runs

```python
# Run specific agent
python apps/workers/tpp/main.py --year 2025

# Run with analytics
python apps/workers/sdf_sales/main.py --analytics

# Force update check
python apps/workers/orchestrator.py --force-update
```

### Scheduled Operations

The orchestrator automatically runs agents based on schedules:
- **Daily**: SDF (6am), Sunbiz (2am), BCPA (3am), Official Records (4am)
- **Weekly**: TPP (Monday 5am), NAV (Tuesday 5am)
- **Monthly**: DOR (1st of month, 1am)

### Monitoring

```bash
# View real-time status
python apps/workers/supabase_orchestrator.py

# Check logs
tail -f logs/pipeline.log

# Database status
psql $SUPABASE_DB_URL -c "SELECT * FROM fl_agent_status;"
```

---

## 🔒 Security Best Practices

1. **Use Service Role Key** only on backend
2. **Enable RLS** on all tables
3. **Rotate keys** regularly
4. **Monitor access** via Supabase dashboard
5. **Backup data** regularly

---

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check Supabase URL and credentials
   - Verify network connectivity
   - Check firewall settings

2. **Missing Tables**
   - Run migration script
   - Check SQL syntax errors
   - Verify permissions

3. **No Updates Detected**
   - Check agent schedules
   - Verify source URLs
   - Review update tracking table

4. **Alerts Not Sending**
   - Verify webhook URL
   - Check SMTP credentials
   - Review alert logs

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
python TEST_SUPABASE_PIPELINE.py
```

---

## 📞 Support

- **Documentation**: `/supabase/migrations/`
- **Test Suite**: `TEST_SUPABASE_PIPELINE.py`
- **Logs**: Check `fl_data_updates` table
- **Monitoring**: Use Supabase dashboard

---

## ✅ Checklist

- [ ] Supabase project created
- [ ] Environment variables configured
- [ ] Database migration completed
- [ ] Dependencies installed
- [ ] Test suite passing
- [ ] Orchestrator running
- [ ] Alerts configured
- [ ] First data sync completed

---

## 🎉 Success Indicators

When everything is working:
1. ✅ All tests pass in `TEST_SUPABASE_PIPELINE.py`
2. ✅ Data appears in Supabase tables
3. ✅ Agent status shows "Active" 
4. ✅ Materialized views populated
5. ✅ Alerts triggering for updates

The pipeline is now actively monitoring Florida Revenue data sources and syncing to Supabase!