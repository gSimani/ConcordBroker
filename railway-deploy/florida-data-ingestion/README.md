# Florida Property Data Orchestrator

Fully automated daily ingestion system for all 67 Florida counties.

## Features

- ✅ **Daily Automated Sync** - Runs at 3:00 AM ET via Railway cron
- ✅ **Delta Detection** - SHA256 hash tracking, only downloads changed files
- ✅ **Multi-Source Ingestion** - DOR Portal + County PAs + FGIO Parcels
- ✅ **AI Validation** - OpenAI + Gemma 3 270M quality scoring
- ✅ **Complete Audit Trail** - Track every ingestion run
- ✅ **Self-Healing** - Automatic error recovery with Sentry monitoring

## Architecture

```
Daily Cron (3 AM ET)
    ↓
DOR Portal Check → Delta Detection → Download if Changed
    ↓
County PA Scrapers (67 counties) → Normalize Data
    ↓
FGIO Geometry Update → PostGIS Load
    ↓
AI Validation (Quality Score 0-100)
    ↓
Staging Tables → Core Tables (Upsert)
    ↓
Audit Logs + Metrics
```

## Quick Start

### 1. Deploy to Railway

```bash
cd railway-deploy/florida-data-ingestion
railway init
railway up
```

### 2. Set Environment Variables

```bash
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_key
railway variables set OPENAI_API_KEY=your_key
railway variables set SENTRY_DSN=your_dsn
```

### 3. Test

```bash
# Get your Railway URL
RAILWAY_URL=$(railway domain)

# Health check
curl $RAILWAY_URL/health

# Trigger manual sync
curl -X POST $RAILWAY_URL/ingest/run

# Check status
curl $RAILWAY_URL/ingest/status
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/ingest/run` | POST | Trigger manual ingestion |
| `/ingest/status` | GET | Last 10 ingestion runs |
| `/coverage/counties` | GET | County coverage statistics |
| `/files/registry` | GET | File change history |

## Database Schema

### Staging Tables
- `nal_staging` - Name/Address/Legal data
- `sdf_staging` - Sales Data File
- `nap_staging` - Property Characteristics

### Audit Tables
- `ingestion_runs` - Run tracking with AI scores
- `file_registry` - SHA256 delta detection
- `validation_errors` - AI-detected issues

### Core Tables
- `florida_parcels` (enhanced with quality columns)
- `property_sales_history` (enhanced with quality columns)

## Data Flow

1. **Discovery**: Fetch DOR directory pages
2. **Delta Check**: Compare SHA256 with file_registry
3. **Download**: Only if file changed or new
4. **Parse**: CSV/ZIP → Staging tables
5. **Validate**: AI quality scoring (0-100)
6. **Upsert**: Staging → Core (on conflict update)
7. **Audit**: Log run + metrics

## Monitoring

### Supabase SQL Queries

```sql
-- Recent ingestion runs
SELECT * FROM recent_ingestion_activity LIMIT 10;

-- County coverage
SELECT * FROM get_county_coverage();

-- Data quality dashboard
SELECT * FROM data_quality_dashboard;

-- Failed ingestions
SELECT * FROM ingestion_runs WHERE status = 'FAILED' ORDER BY run_timestamp DESC;
```

### Railway Logs

```bash
railway logs -f
```

## Configuration

### Cron Schedule

Edit `railway.toml`:
```toml
[[crons]]
schedule = "0 8 * * *"  # Daily at 8 AM UTC (3 AM ET)
command = "python florida_data_orchestrator.py sync"
```

### Batch Sizes

Edit `florida_data_orchestrator.py`:
```python
batch_size = 1000  # Records per batch
```

## Troubleshooting

### No data ingested
- Check Supabase service role key
- Verify Storage bucket exists: `florida-property-data`
- Check Railway logs for errors

### Timeout errors
- Increase batch size
- Check Supabase statement_timeout settings

### Delta detection not working
- Verify file_registry table populated
- Check SHA256 hashing logic

## Development

### Local Testing

```bash
# Set environment variables
export SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your_key
export OPENAI_API_KEY=your_key

# Run locally
python florida_data_orchestrator.py sync

# Or start API server
uvicorn florida_data_orchestrator:app --reload
```

### Run Tests

```bash
pytest tests/
```

## Performance

**Expected Metrics:**
- Single county NAL file: 2-5 minutes
- Full 67 counties: 1.5-3 hours
- AI validation: ~100 records/second
- Memory usage: 2-4 GB
- Quality score target: 85%+

## Cost

**Monthly Estimates:**
- Railway Hobby: $20
- Supabase Pro: $25
- OpenAI API: ~$50
- Sentry: Free tier
- **Total**: ~$95/month

## Support

- **Documentation**: See `RAILWAY_DEPLOYMENT_GUIDE.md`
- **Issues**: Check Railway logs and Sentry
- **Supabase**: https://supabase.com/dashboard

## License

Proprietary - ConcordBroker Internal Use Only
