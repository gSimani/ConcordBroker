# Florida Daily Updates System

A comprehensive, automated system for daily updates of Florida property data from the Florida Department of Revenue portal. Designed for reliable, scalable data collection and processing with robust error handling and monitoring.

## Overview

This system monitors the Florida Revenue portal for new NAL (Name and Address List), NAP (Name and Address with Property Values), and SDF (Sales Data File) data files, automatically downloads them, processes the data, and updates your Supabase database.

### Key Features

- **Automated Daily Updates**: Scheduled to run at 2 AM EST daily
- **Resume Capability**: Downloads can resume if interrupted
- **Incremental Processing**: Only processes new and updated records
- **Database UPSERT**: Efficiently updates existing records
- **Error Recovery**: Robust error handling with retries
- **Monitoring & Alerts**: Email/Slack notifications on success/failure
- **Multi-County Support**: Start with Broward, easily expand to all counties
- **Docker Support**: Containerized deployment option
- **Production Ready**: Handles edge cases and connection failures gracefully

## Architecture

The system consists of 5 main agents orchestrated together:

1. **Monitor Agent**: Checks Florida portal for new/updated files
2. **Downloader Agent**: Downloads files with resume capability  
3. **Processor Agent**: Validates and processes data
4. **Database Updater Agent**: Performs UPSERT operations to Supabase
5. **Orchestrator Agent**: Coordinates all agents and handles workflows

## Quick Start

### Prerequisites

- Python 3.8+
- Supabase account and database
- 10+ GB available disk space
- Internet connection to floridarevenue.com

### Installation

1. **Clone or copy the system files**:
   ```bash
   # Ensure you have the complete florida_daily_updates directory
   cd florida_daily_updates
   ```

2. **Run the setup script**:
   ```bash
   python scripts/setup.py
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Test the system**:
   ```bash
   python scripts/run_daily_update.py --mode test
   ```

### Docker Deployment (Recommended)

1. **Build and run with Docker Compose**:
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your credentials
   
   # Start the system
   docker-compose up -d
   ```

2. **Check logs**:
   ```bash
   docker-compose logs -f florida-updates
   ```

## Configuration

### Environment Variables

Required variables in `.env`:

```bash
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Optional Notifications
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

### Main Configuration

Edit `config/config.yaml` to customize:

- Counties to process (currently Broward enabled)
- File types to download (NAL, NAP, SDF)
- Processing batch sizes
- Retry settings
- Notification preferences

## Usage

### Manual Execution

```bash
# Full daily update
python scripts/run_daily_update.py --mode full

# Monitor for new files only  
python scripts/run_daily_update.py --mode monitor

# Maintenance tasks
python scripts/run_daily_update.py --mode maintenance

# Test with limited scope
python scripts/run_daily_update.py --mode test

# Specific counties/types
python scripts/run_daily_update.py --mode full --counties broward --file-types NAL,NAP
```

### Scheduled Execution

#### Windows (Task Scheduler)
```batch
# Run as Administrator
scripts\schedule_task.bat
```

#### Linux/Mac (Cron)
```bash
# Install cron jobs
chmod +x scripts/install_cron.sh
./scripts/install_cron.sh
```

#### Docker (Automatic)
```bash
# Starts with cron scheduler automatically
docker-compose up -d
```

## Data Flow

1. **Monitor**: Checks https://floridarevenue.com/property/dataportal daily
2. **Download**: Downloads new/updated county files (NAL, NAP, SDF)  
3. **Process**: Validates data, handles incremental updates
4. **Database**: UPSERTs into Supabase tables:
   - `florida_nal_property_details` (property info)
   - `florida_nap_assessments` (valuations)
   - `florida_sdf_sales` (sales transactions)

## Database Schema

### NAL Table (Property Details)
```sql
CREATE TABLE florida_nal_property_details (
    county_code VARCHAR(2),
    parcel_id VARCHAR(50), 
    parcel_number VARCHAR(50),
    owner_name TEXT,
    property_address TEXT,
    legal_description TEXT,
    property_use_code VARCHAR(10),
    land_value DECIMAL(15,2),
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    PRIMARY KEY (county_code, parcel_id)
);
```

### NAP Table (Assessments)
```sql
CREATE TABLE florida_nap_assessments (
    county_code VARCHAR(2),
    parcel_id VARCHAR(50),
    tax_year INTEGER,
    land_value DECIMAL(15,2),
    just_value DECIMAL(15,2), 
    assessed_value DECIMAL(15,2),
    exempt_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    PRIMARY KEY (county_code, parcel_id, tax_year)
);
```

### SDF Table (Sales)
```sql
CREATE TABLE florida_sdf_sales (
    county_code VARCHAR(2),
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_price DECIMAL(15,2),
    deed_book VARCHAR(20),
    deed_page VARCHAR(20),
    grantor TEXT,
    grantee TEXT,
    deed_type VARCHAR(50),
    PRIMARY KEY (county_code, parcel_id, sale_date, deed_book, deed_page)
);
```

## Monitoring

### Logs

- **Application logs**: `logs/florida_updates_YYYYMMDD.log`
- **Cron logs**: `logs/cron.log` (Docker) or system cron logs
- **Agent-specific logs**: Each agent maintains state databases

### Notifications

Configure email or Slack notifications for:
- Daily update success/failure
- Long-running operations (>4 hours)
- Error conditions requiring attention
- Large data changes (>20% record count change)

### Health Checks

- **Docker**: Built-in health checks every 30 minutes
- **Manual**: `python scripts/run_daily_update.py --mode monitor`
- **Database**: Query tracking tables for update status

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Check internet connectivity to floridarevenue.com
   - Verify Supabase credentials and database access
   - Review firewall/proxy settings

2. **Download Failures**:
   - Files resume automatically on next run
   - Check disk space (need 5-10GB free)
   - Verify portal isn't under maintenance

3. **Processing Errors**:
   - Check data format changes in source files
   - Review validation errors in logs
   - Verify database schema matches expectations

4. **Scheduling Issues**:
   - Windows: Check Task Scheduler for task status
   - Linux: Verify cron service running: `sudo service cron status`
   - Docker: Check container is running: `docker ps`

### Debug Mode

Enable verbose logging:
```bash
python scripts/run_daily_update.py --mode full --log-level DEBUG
```

### Manual Recovery

If updates fail, manually trigger recovery:
```bash
# Re-run just the failed step
python scripts/run_daily_update.py --mode monitor  # Check for new files
python scripts/run_daily_update.py --mode full     # Full pipeline
```

## Performance

### Typical Performance
- **Monitoring**: 30-60 seconds
- **Download**: 5-30 minutes (depending on file sizes)
- **Processing**: 10-60 minutes (depending on record count)  
- **Database Update**: 10-30 minutes (depending on changes)
- **Total Runtime**: 30 minutes - 3 hours

### Optimization
- Adjust `batch_size` in configuration for your database
- Increase `max_concurrent_downloads` for faster downloads
- Use SSD storage for better I/O performance
- Monitor database connection pooling

## Scaling

### Adding Counties

Edit `config/config.yaml`:
```yaml
counties:
  palm_beach:
    code: "50"
    name: "Palm Beach" 
    active: true    # Enable this county
    priority: 3
```

### Adding File Types

The system supports any file types available from the Florida portal. Current types:
- **NAL**: Property owner information
- **NAP**: Assessment values  
- **SDF**: Sales transactions

### Horizontal Scaling

For processing multiple states or larger datasets:
- Run separate instances per state/region
- Use different database schemas/tables
- Share the same codebase with different configurations

## API Integration

The system integrates with your existing ConcordBroker API:
- Data is available through existing property endpoints
- Database tables can be joined with other property data
- Real-time updates appear in search results

## Security

- Environment variables for sensitive data
- Service account keys for database access
- Option to encrypt local data storage
- Rate limiting for portal requests
- Secure HTTPS connections only

## Contributing

### Development Setup

1. **Create development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run tests**:
   ```bash
   pytest tests/
   ```

3. **Code style**:
   ```bash
   black florida_daily_updates/
   flake8 florida_daily_updates/
   ```

### Adding New Features

- Follow the agent pattern for new functionality
- Add configuration options to `config.yaml`
- Include tests and documentation
- Update this README

## Support

### Resources
- Configuration: `config/config.yaml`
- Schedules: `config/schedules.json`  
- County list: `config/counties.json`
- Environment template: `.env.example`

### Getting Help
1. Check logs for specific error messages
2. Verify configuration and environment variables
3. Test individual components in isolation
4. Review the Florida Revenue portal for changes

## License

This system is part of the ConcordBroker project. See the main project license for terms and conditions.

## Changelog

### Version 1.0.0
- Initial release with Broward County support
- Full NAL, NAP, SDF processing pipeline
- Docker deployment support
- Comprehensive monitoring and alerting
- Production-ready error handling

---

For technical support or questions, please refer to the main ConcordBroker documentation or contact the development team.