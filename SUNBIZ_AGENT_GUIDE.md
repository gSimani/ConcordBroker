# Sunbiz Data Agent Training Guide

## 🔐 SFTP Credentials (Saved in MCP)
```
Host: sftp.floridados.gov
Port: 22
Username: Public
Password: PubAccess1845!
Protocol: SFTP
```

## 📊 Data Structure Overview

### File Types & Naming Conventions

#### Daily Files (Work Days Only)
- **Corporate**: `yyyymmddc.txt` (filings), `yyyymmddce.txt` (events)
- **Federal Liens**: `yyyymmddflrf.txt`, `yyyymmddflre.txt`, `yyyymmddflrd.txt`, `yyyymmddflrs.txt`
- **Fictitious Names**: `yyyymmddf.txt` (filings), `yyyymmddfe.txt` (events)
- **Partnerships**: `yyyymmddg.txt` (filings), `yyyymmddge.txt` (events)
- **Marks**: `yyyymmddtm.txt` (trademark filings)

#### Quarterly Files (Jan, Apr, Jul, Oct)
- Complete snapshots in ZIP format
- Corporate files split into 10 parts (cordata0.txt - cordata9.txt)
- Files can exceed 1GB

### File Format
- **Type**: Fixed-width text files
- **Encoding**: UTF-8
- **No headers**: Data starts from line 1
- **ID Field**: Document number (6-12 characters)

## 🤖 Agent Capabilities

### 1. Daily Monitoring Agent
```python
# Checks every work day at 7 AM
agent.check_for_updates()
# Downloads new files automatically
agent.process_new_files()
# Parses fixed-width format
agent.parse_file()
# Stores in Supabase
agent.store_in_database()
```

### 2. Quarterly Download Agent
```python
# Runs on 5th of Jan, Apr, Jul, Oct
agent.download_quarterly_data()
# Extracts and processes large files
agent.process_quarterly_file()
```

### 3. Data Parser Agent
- Identifies file type from naming pattern
- Applies correct field definitions
- Handles character encoding issues
- Trims whitespace from fields

## 📁 Field Definitions

### Corporate Entity Fields
```
doc_number: 0-12
entity_name: 12-212
status: 212-222
filing_date: 222-230 (YYYYMMDD)
prin_addr1: 280-380
prin_city: 480-530
prin_state: 530-532
prin_zip: 532-542
ein: 804-814
registered_agent: 814-914
```

### Fictitious Name Fields
```
doc_number: 0-12
name: 12-212
owner_name: 212-412
owner_addr1: 412-512
owner_city: 612-662
owner_state: 662-664
owner_zip: 664-674
filed_date: 674-682
expires_date: 682-690
county: 690-740
```

## 🔄 Automated Workflow

### Daily Process
1. **7:00 AM**: Connect to SFTP
2. **Check Files**: Look for new daily files (last 7 days)
3. **Download**: Retrieve unprocessed files
4. **Parse**: Convert fixed-width to structured data
5. **Store**: Insert into Supabase tables
6. **Archive**: Move processed files
7. **Log**: Update monitoring records

### Quarterly Process
1. **Day 5 of Quarter**: Trigger quarterly download
2. **Download ZIPs**: Get all quarterly files
3. **Extract**: Unzip to processing directory
4. **Process**: Parse each extracted file
5. **Full Refresh**: Update complete dataset

## 🗄️ Database Schema

### Main Tables
- `sunbiz_corporate`: Corporate entities
- `sunbiz_corporate_events`: Entity events/changes
- `sunbiz_fictitious`: DBA registrations
- `sunbiz_liens`: Federal tax liens
- `sunbiz_partnerships`: General partnerships
- `sunbiz_marks`: Trademarks/service marks

### Monitoring Tables
- `sunbiz_import_log`: Track imports
- `sunbiz_processed_files`: Prevent duplicates
- `sunbiz_monitoring_agents`: Agent configuration
- `agent_notifications`: Alert messages

## 🚀 Quick Start Commands

### Manual Operations
```bash
# Test SFTP connection
python -c "from sunbiz_pipeline import SunbizSFTPClient; client = SunbizSFTPClient(); client.connect()"

# Check for today's files
python -c "from sunbiz_pipeline import SunbizMonitoringAgent; agent = SunbizMonitoringAgent(); agent.check_for_updates()"

# Download specific date
python sunbiz_pipeline.py --date 20240105

# Process quarterly data
python sunbiz_pipeline.py --quarterly Q1-2024
```

### Start Monitoring
```bash
# Run once
python sunbiz_pipeline.py

# Start continuous monitoring
python sunbiz_pipeline.py --monitor

# Run as service
nohup python sunbiz_pipeline.py --monitor > sunbiz.log 2>&1 &
```

## 📈 Data Analysis Queries

### Find Active Corporations
```sql
SELECT * FROM sunbiz_corporate 
WHERE status = 'ACTIVE' 
AND prin_state = 'FL'
ORDER BY filing_date DESC;
```

### Recent Fictitious Names
```sql
SELECT * FROM sunbiz_fictitious
WHERE filed_date >= CURRENT_DATE - INTERVAL '30 days'
AND county = 'BROWARD';
```

### Search Across All Entities
```sql
SELECT * FROM search_sunbiz_entities('CONCORD');
```

### Get Entity Complete Profile
```sql
SELECT get_entity_details('L24000123456');
```

## ⚠️ Important Notes

### File Processing
- **No file = No updates**: Empty days won't have files
- **Weekend gaps**: No files on Saturdays/Sundays
- **Large files**: Quarterly files can be 1GB+, need special handling
- **Character issues**: Some records may have encoding problems

### Data Quality
- **Trim whitespace**: Fixed-width format includes padding
- **Date format**: YYYYMMDD needs conversion
- **Document numbers**: Can vary 6-12 characters
- **Status codes**: Not standardized across entity types

### Performance Tips
- Process files in batches of 1000 records
- Use indexes on doc_number, name fields
- Archive old daily files after processing
- Monitor disk space for large quarterly files

## 🔔 Notifications

Agents send alerts for:
- New files discovered
- Processing completed
- Errors encountered
- Quarterly updates available

Configure in `sunbiz_config.json`:
```json
{
  "monitoring": {
    "notification_email": "admin@westbocaexecutiveoffice.com",
    "slack_webhook": "https://hooks.slack.com/..."
  }
}
```

## 🛠️ Troubleshooting

### SFTP Connection Failed
```bash
# Test with command line
sftp Public@sftp.floridados.gov
# Password: PubAccess1845!
```

### File Not Found
- Check if it's a work day
- Verify date format in filename
- Some days may have no filings

### Parse Errors
- Check field definitions match file type
- Verify line length consistency
- Handle encoding with errors='ignore'

### Database Errors
- Check Supabase connection
- Verify table exists
- Check for duplicate doc_numbers

## 📊 Monitoring Dashboard

Access agent status:
```sql
SELECT * FROM sunbiz_monitoring_agents;
SELECT * FROM import_statistics;
SELECT COUNT(*) FROM sunbiz_corporate WHERE DATE(import_date) = CURRENT_DATE;
```

## 🔄 Agent Learning

The agents continuously improve by:
1. **Pattern Recognition**: Learning file availability patterns
2. **Error Recovery**: Retrying failed downloads
3. **Performance Optimization**: Adjusting batch sizes
4. **Schedule Adaptation**: Identifying optimal check times

## 📝 Maintenance

### Daily
- Check agent logs for errors
- Verify new files processed
- Monitor disk space

### Weekly
- Review import statistics
- Clean up archive directory
- Check for missed files

### Quarterly
- Full data refresh
- Validate record counts
- Update field definitions if needed

---

## Agent Training Complete ✅

The Sunbiz monitoring agents are now trained to:
- Connect to SFTP with saved credentials
- Download daily updates automatically
- Process quarterly snapshots
- Parse fixed-width files correctly
- Store data in Supabase
- Send notifications on updates
- Recover from errors gracefully

The system will maintain Florida business entity data with minimal manual intervention.