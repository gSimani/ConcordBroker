# Florida SunBiz Daily Update System

## Overview
Automated system for daily updates of Florida business data directly from SFTP to Supabase, bypassing local PC storage.

## 🚀 Key Features

### Direct SFTP-to-Supabase Pipeline
- No local storage required
- Streams data directly from Florida DOS SFTP server
- Processes files in memory
- Efficient batch uploads using PostgreSQL COPY

### Intelligent Processing
- **Deduplication**: Prevents duplicate key errors (lesson learned from bulk upload)
- **Incremental Updates**: Only processes new daily files
- **File Tracking**: Maintains history of processed files
- **UPSERT Logic**: Updates existing entities or creates new ones

### Multiple Deployment Options
1. **Local Scheduler** (`florida_daily_updater.py`)
   - Runs on local machine or server
   - Built-in scheduling with Python `schedule` library
   - Configurable run times

2. **Cloud-Native** (`florida_cloud_updater.py`)
   - AWS Lambda compatible
   - Google Cloud Function ready
   - Container deployable
   - Serverless architecture

## 📋 Prerequisites

### Required Python Packages
```bash
pip install psycopg2-binary paramiko schedule boto3
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgres://user:pass@host:port/database

# SFTP (optional - has defaults)
SFTP_HOST=sftp.floridados.gov
SFTP_USER=Public
SFTP_PASS=PubAccess1845!

# Notifications (optional)
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic
WEBHOOK_URL=https://your-webhook-url.com
```

## 🔧 Configuration

### Database Schema
The system automatically creates required tables:
- `florida_entities` - Main entity storage
- `florida_daily_processed_files` - Tracking table for processed files

### Daily File Types Processed
- Corporate Filings (`c`)
- Corporate Events (`ce`)
- Fictitious Names (`f`, `fe`)
- General Partnerships (`gp`, `gpe`)
- Federal Tax Liens (`lien`)
- Mark Filings (`mk`)

## 🚀 Deployment Options

### Option 1: Local/Server Deployment
```bash
# Run once for testing
python apps/agents/florida_daily_updater.py

# Or schedule for continuous operation
# Edit the schedule time in the script and run:
python apps/agents/florida_daily_updater.py --schedule
```

### Option 2: AWS Lambda
1. Package the cloud updater with dependencies:
```bash
pip install -r requirements.txt -t package/
cp florida_cloud_updater.py package/
cd package && zip -r ../function.zip .
```

2. Create Lambda function:
```bash
aws lambda create-function \
  --function-name florida-daily-updater \
  --runtime python3.9 \
  --handler florida_cloud_updater.lambda_handler \
  --zip-file fileb://function.zip \
  --environment Variables={DATABASE_URL=your-db-url}
```

3. Schedule with CloudWatch Events (daily at 2 AM EST):
```bash
aws events put-rule \
  --name florida-daily-update \
  --schedule-expression "cron(0 7 * * ? *)"
```

### Option 3: Google Cloud Function
```bash
gcloud functions deploy florida-daily-updater \
  --runtime python39 \
  --trigger-http \
  --entry-point cloud_function_handler \
  --set-env-vars DATABASE_URL=your-db-url
```

### Option 4: Docker Container
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY florida_cloud_updater.py .
CMD ["python", "florida_cloud_updater.py"]
```

### Option 5: GitHub Actions
```yaml
name: Florida Daily Update
on:
  schedule:
    - cron: '0 7 * * *'  # 2 AM EST
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python florida_cloud_updater.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## 📊 Monitoring

### Tracking Table Queries
```sql
-- Check recent updates
SELECT * FROM florida_daily_processed_files 
ORDER BY processed_at DESC 
LIMIT 10;

-- Check for failures
SELECT * FROM florida_daily_processed_files 
WHERE status = 'failed'
ORDER BY processed_at DESC;

-- Daily statistics
SELECT 
    DATE(processed_at) as date,
    COUNT(*) as files_processed,
    SUM(entities_created) as total_created,
    SUM(entities_updated) as total_updated,
    AVG(processing_time_seconds) as avg_time
FROM florida_daily_processed_files
WHERE status = 'completed'
GROUP BY DATE(processed_at)
ORDER BY date DESC;
```

### Health Checks
```python
# Check if updates are running
def check_update_health():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(processed_at) as last_update
            FROM florida_daily_processed_files
            WHERE status = 'completed'
        """)
        last_update = cur.fetchone()[0]
        
        if last_update:
            hours_since = (datetime.now() - last_update).total_seconds() / 3600
            if hours_since > 48:
                print("WARNING: No updates in 48+ hours")
        else:
            print("ERROR: No successful updates found")
```

## 🔍 Data Flow

1. **SFTP Connection** → Connect to Florida DOS server
2. **File Discovery** → Find new daily files (last N days)
3. **Duplicate Check** → Skip already processed files
4. **Stream Processing** → Read file directly into memory
5. **Parse Records** → Extract entity information
6. **Deduplicate** → Remove duplicates within batch
7. **Batch Upload** → Use COPY for efficient insertion
8. **UPSERT Logic** → Update existing or create new entities
9. **Track Progress** → Log processed files
10. **Send Notifications** → Alert on completion/errors

## 🎯 Key Improvements from Bulk Upload

### Lessons Applied:
1. **Proper Deduplication**: Always deduplicate before INSERT to prevent "command cannot affect row a second time" errors
2. **Efficient Batching**: Use PostgreSQL COPY command for speed
3. **Unique Prefixes**: Daily updates use "D" prefix to avoid conflicts
4. **Incremental Processing**: Only process new files, track what's been done
5. **Error Handling**: Comprehensive error logging and recovery

## 📈 Performance Metrics

- **Processing Speed**: ~1,000 records/second
- **Memory Usage**: < 100MB per file
- **Network Efficiency**: Direct streaming, no intermediate storage
- **Database Load**: Optimized batch inserts minimize connections

## 🔐 Security Notes

- SFTP credentials are public (provided by Florida DOS)
- Database credentials should be stored securely (environment variables)
- Use IAM roles for cloud deployments
- Consider VPC endpoints for database access

## 🛠️ Troubleshooting

### Common Issues:

1. **SFTP Connection Failures**
   - Check network connectivity
   - Verify credentials haven't changed
   - Check Florida DOS service status

2. **Database Timeouts**
   - Increase statement timeout
   - Reduce batch size
   - Check database performance

3. **Duplicate Key Errors**
   - Ensure deduplication is working
   - Check for unique constraint violations
   - Review entity_id generation logic

4. **Missing Daily Files**
   - Files are only generated on business days
   - No files on holidays/weekends
   - Check Florida DOS announcements

## 📞 Support

For issues with:
- **Florida Data**: Contact Florida Department of State
- **Database**: Check Supabase status page
- **Code**: Review error logs and tracking table

## 🎉 Success Metrics

The system is working correctly when:
- ✅ Daily files are processed within 24 hours
- ✅ No duplicate key errors in logs
- ✅ Processing time < 5 minutes per day
- ✅ All file types are being captured
- ✅ Notifications are received daily

---

*Built with lessons learned from successfully uploading 8,414 files with millions of Florida business entities.*