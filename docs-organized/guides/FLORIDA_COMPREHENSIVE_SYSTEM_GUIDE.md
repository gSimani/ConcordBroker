# Florida Property Data Comprehensive Monitoring & Download System

## Overview

This document provides a complete implementation guide for the comprehensive Florida property data ecosystem monitoring and download system. The system automatically detects, downloads, processes, and monitors all Florida property data sources with intelligent scheduling, error recovery, and real-time alerting.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   MASTER ORCHESTRATOR                      │
│                 (florida_master_orchestrator.py)           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  COMPREHENSIVE  │  │   MONITORING    │  │    ERROR     │ │
│  │    MONITOR      │  │    SYSTEM       │  │   HANDLER    │ │
│  │                 │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   SCHEDULER     │  │  URL RESOLVER   │  │     DATA     │ │
│  │                 │  │                 │  │  PROCESSOR   │ │
│  │                 │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE DATABASE                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   FLORIDA DATA  │  │   MONITORING    │  │    ERROR     │ │
│  │     TABLES      │  │     TABLES      │  │   TRACKING   │ │
│  │                 │  │                 │  │              │ │
│  │  • fl_tpp       │  │  • fl_data_     │  │  • fl_error_ │ │
│  │  • fl_nav       │  │    updates      │  │    records   │ │
│  │  • fl_sdf       │  │  • fl_agent_    │  │  • fl_circuit│ │
│  │  • fl_nal       │  │    status       │  │    breakers  │ │
│  │                 │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Sources Covered

### 1. Florida Revenue Data Portal
- **URL**: https://floridarevenue.com/property/dataportal/
- **Data Types**: NAL, NAP, NAV, SDF, TPP, RER, CDF, JVS
- **Update Frequency**: Monthly (with period indicators P/F)
- **Counties**: Broward (06), Miami-Dade (13), Palm Beach (50)

### 2. Sunbiz SFTP Server
- **Host**: sftp.floridados.gov
- **Credentials**: Public/PubAccess1845!
- **Data Types**: Business entities, officers, reports
- **Update Frequency**: Daily/Weekly

### 3. Broward County Daily Index
- **URL**: https://www.broward.org/RecordsTaxesTreasury/Records/Pages/DailyIndexExtractFiles.aspx
- **Data Types**: Property records, transactions
- **Update Frequency**: Daily

### 4. ArcGIS Statewide Cadastral
- **URL**: https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer
- **Data Types**: Parcel boundaries, geographic data
- **Update Frequency**: Quarterly

### 5. Florida Geospatial Open Data
- **URL**: https://geodata.floridagio.gov/
- **Data Types**: GIS data, boundaries, flood zones
- **Update Frequency**: Variable

## Installation & Setup

### Prerequisites

1. **Python 3.9+** with asyncio support
2. **PostgreSQL** (via Supabase)
3. **Required Python packages**:

```bash
pip install -r requirements-florida-comprehensive.txt
```

Create `requirements-florida-comprehensive.txt`:
```
asyncio==3.4.3
aiohttp==3.8.4
asyncpg==0.28.0
asyncssh==2.13.1
pandas==2.0.3
numpy==1.24.3
supabase==1.0.4
psutil==5.9.5
schedule==1.2.0
rich==13.4.2
beautifulsoup4==4.12.2
chardet==5.1.0
python-dateutil==2.8.2
pytz==2023.3
```

### Environment Variables

Create `.env` file in project root:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Notification Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_RECIPIENTS=admin1@company.com,admin2@company.com

# Slack/Discord Webhooks (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK

# System Configuration
TIMEZONE=US/Eastern
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=5
```

### Database Schema Deployment

1. **Apply Supabase migrations**:
```bash
# Navigate to project root
cd /path/to/ConcordBroker

# Apply the Florida data schemas
python -c "
import asyncio
from apps.workers.florida_comprehensive_monitor import FloridaComprehensiveMonitor
async def setup():
    async with FloridaComprehensiveMonitor() as monitor:
        print('Database schemas initialized')
asyncio.run(setup())
"
```

2. **Verify table creation**:
```sql
-- Check that all tables are created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'fl_%';
```

## Usage Guide

### 1. Quick Start - Single Run

Test the system with a single comprehensive operation:

```bash
cd /path/to/ConcordBroker/apps/workers
python florida_master_orchestrator.py --mode single --log-level INFO
```

### 2. Health Check

Check system health and component status:

```bash
python florida_master_orchestrator.py --mode health
```

### 3. Live Dashboard

Start the real-time monitoring dashboard:

```bash
python florida_master_orchestrator.py --mode dashboard
```

### 4. Production Daemon

Start the full orchestrator daemon for continuous operation:

```bash
python florida_master_orchestrator.py --mode daemon --log-level INFO
```

### 5. Individual Component Testing

Test individual components:

```bash
# Test comprehensive monitoring
python florida_comprehensive_monitor.py

# Test URL resolver
python florida_url_resolver.py

# Test data processor
python florida_data_processor.py

# Test error handler
python florida_error_handler.py

# Test scheduler
python florida_scheduler.py
```

## Configuration Options

### System Configuration (`florida_config.json`)

Create a configuration file for custom settings:

```json
{
  "orchestrator": {
    "name": "Florida Property Data Orchestrator",
    "version": "1.0.0",
    "timezone": "US/Eastern",
    "log_level": "INFO"
  },
  "health_checks": {
    "interval_minutes": 5,
    "alert_thresholds": {
      "error_rate": 0.1,
      "response_time_seconds": 30,
      "cpu_usage_percent": 80,
      "memory_usage_percent": 80
    }
  },
  "data_sources": {
    "florida_revenue": {
      "priority": 1,
      "check_interval_hours": 1,
      "enabled": true
    },
    "sunbiz": {
      "priority": 2,
      "check_interval_hours": 24,
      "enabled": true
    },
    "broward_daily": {
      "priority": 3,
      "check_interval_minutes": 30,
      "enabled": true
    },
    "arcgis": {
      "priority": 4,
      "check_interval_hours": 12,
      "enabled": true
    }
  },
  "notifications": {
    "critical_errors": true,
    "email_recipients": ["admin@company.com"],
    "slack": {
      "enabled": true,
      "webhook_url": "SLACK_WEBHOOK_URL",
      "channel": "#florida-data-alerts"
    }
  }
}
```

### Scheduling Configuration

The scheduler supports multiple schedule types:

```python
# Daily schedule
{
  "schedule_type": "daily",
  "schedule_config": {
    "time": "06:00",
    "timezone": "US/Eastern"
  }
}

# Interval schedule
{
  "schedule_type": "interval",
  "schedule_config": {
    "minutes": 30
  }
}

# Weekly schedule
{
  "schedule_type": "weekly",
  "schedule_config": {
    "day": "sunday",
    "time": "02:00"
  }
}

# Adaptive schedule (automatically optimized)
{
  "schedule_type": "adaptive",
  "schedule_config": {
    "min_interval_minutes": 15,
    "max_interval_hours": 24
  }
}
```

## Monitoring & Alerting

### Dashboard Features

The live dashboard provides real-time monitoring of:

- **System Health**: Overall status, uptime, resource usage
- **Component Status**: Status of each system component
- **Data Sources**: Status and last check time for each source
- **Active Alerts**: Current alerts and error rates
- **Performance Metrics**: Execution times, success rates

### Alert Types

The system generates alerts for:

1. **New File Detected**: When new data files are found
2. **File Updated**: When existing files are modified
3. **Download Failed**: When file downloads fail
4. **Processing Failed**: When data processing encounters errors
5. **Source Unavailable**: When data sources become inaccessible
6. **Anomaly Detected**: When unusual patterns are detected
7. **System Overload**: When resource usage exceeds thresholds

### Notification Channels

- **Email**: SMTP-based email notifications
- **Slack**: Webhook-based Slack messages
- **Discord**: Webhook-based Discord messages
- **Database**: All alerts stored in `fl_monitoring_alerts` table

## Error Handling & Recovery

### Circuit Breaker Pattern

The system implements circuit breakers for each data source:

- **CLOSED**: Normal operation
- **OPEN**: Source is failing, skip requests
- **HALF_OPEN**: Testing if source has recovered

### Retry Logic

Configurable retry logic with exponential backoff:

```python
retry_configs = {
    "network_error": {
        "max_attempts": 5,
        "base_delay": 2.0,
        "max_delay": 120.0
    },
    "http_error": {
        "max_attempts": 3,
        "base_delay": 1.0,
        "max_delay": 60.0
    }
}
```

### Recovery Actions

Automatic recovery actions:
- **RETRY**: Retry the operation
- **SKIP**: Skip and continue
- **FALLBACK**: Use alternative data source
- **ABORT**: Stop related operations
- **MANUAL_INTERVENTION**: Notify administrators

## Performance Optimization

### Adaptive Scheduling

The system automatically optimizes schedules based on:
- Historical data patterns
- System load
- Resource availability
- Error rates

### Resource Management

- **CPU Usage Monitoring**: Throttle operations when CPU > 80%
- **Memory Management**: Monitor and limit memory usage
- **Concurrent Task Limits**: Maximum simultaneous operations
- **Rate Limiting**: Respect source rate limits

### Batch Processing

- Configurable batch sizes for data processing
- Bulk database operations
- Parallel processing where possible

## Data Quality & Validation

### Schema Validation

All data is validated against predefined schemas:

```python
# Example TPP schema validation
tpp_schema = {
    "county_number": {"type": "text", "required": True},
    "account_number": {"type": "text", "required": True},
    "assessment_year": {"type": "integer", "required": True},
    "tangible_value": {"type": "decimal", "transform": "clean_currency"}
}
```

### Data Cleaning

Automatic data cleaning:
- Currency value parsing
- Date format standardization
- Text field trimming
- NULL value handling

### Quality Metrics

Monitor data quality with:
- Record count validation
- Null percentage checks
- Outlier detection
- Schema compliance

## Deployment Options

### 1. Local Development

```bash
# Clone repository
git clone https://github.com/your-org/concord-broker
cd concord-broker

# Install dependencies
pip install -r requirements-florida-comprehensive.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run single test
python apps/workers/florida_master_orchestrator.py --mode single
```

### 2. Production Server

```bash
# Install as systemd service
sudo cp deployment/florida-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable florida-orchestrator
sudo systemctl start florida-orchestrator
```

### 3. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements-florida-comprehensive.txt .
RUN pip install -r requirements-florida-comprehensive.txt

COPY apps/ ./apps/
COPY .env .

CMD ["python", "apps/workers/florida_master_orchestrator.py", "--mode", "daemon"]
```

### 4. Cloud Deployment (AWS/GCP/Azure)

Use the provided cloud deployment scripts:
- `deployment/aws-ecs-deploy.yml`
- `deployment/gcp-cloud-run-deploy.yml`
- `deployment/azure-container-deploy.yml`

## Maintenance & Operations

### Daily Operations

1. **Check Dashboard**: Monitor system health
2. **Review Alerts**: Address any active alerts
3. **Validate Data**: Ensure data quality
4. **Check Logs**: Review error logs for issues

### Weekly Operations

1. **Performance Review**: Analyze execution times
2. **Schedule Optimization**: Review and adjust schedules
3. **Error Analysis**: Investigate recurring errors
4. **Capacity Planning**: Monitor resource usage trends

### Monthly Operations

1. **Data Audit**: Comprehensive data quality audit
2. **Performance Tuning**: Optimize based on patterns
3. **Configuration Review**: Update configurations
4. **Backup Verification**: Ensure backup systems work

### Troubleshooting

#### Common Issues

1. **High Error Rates**
   - Check network connectivity
   - Verify credentials
   - Review source availability

2. **Slow Performance**
   - Check resource usage
   - Optimize batch sizes
   - Review concurrent task limits

3. **Missing Data**
   - Check source URLs
   - Verify file patterns
   - Review processing logs

#### Log Analysis

Key log files:
- `florida_master_orchestrator.log`: Main system log
- `florida_comprehensive_monitor.log`: Monitoring activities
- `florida_error_handler.log`: Error tracking

#### Database Queries

Useful monitoring queries:

```sql
-- Check recent errors
SELECT * FROM fl_error_records 
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Monitor data updates
SELECT agent_name, last_checked, status, records_processed
FROM fl_data_updates
ORDER BY last_checked DESC;

-- Circuit breaker status
SELECT source, state, failure_count, last_failure
FROM fl_circuit_breaker_states
WHERE state != 'CLOSED';
```

## API Integration

### REST API Endpoints

The system provides REST endpoints for integration:

```python
# Health check
GET /api/v1/health

# System status
GET /api/v1/status

# Data sources
GET /api/v1/sources
GET /api/v1/sources/{source_id}/status

# Alerts
GET /api/v1/alerts
POST /api/v1/alerts/{alert_id}/resolve

# Manual operations
POST /api/v1/operations/run
POST /api/v1/operations/schedule
```

### Webhooks

Configure webhooks for external integration:

```json
{
  "webhooks": {
    "data_updated": "https://your-app.com/webhooks/data-updated",
    "error_occurred": "https://your-app.com/webhooks/error-occurred",
    "system_health": "https://your-app.com/webhooks/health-check"
  }
}
```

## Security Considerations

### Access Control

- **Environment Variables**: Store sensitive data in environment variables
- **Database Security**: Use least-privilege database access
- **API Authentication**: Implement API key authentication
- **Network Security**: Use HTTPS for all external communications

### Data Protection

- **Encryption**: Encrypt sensitive data in transit and at rest
- **Audit Logs**: Maintain comprehensive audit trails
- **Backup Security**: Secure backup storage
- **Access Monitoring**: Monitor and log all system access

## Support & Maintenance

### Getting Help

1. **Documentation**: Refer to this comprehensive guide
2. **Logs**: Check system logs for error details
3. **Dashboard**: Use the live dashboard for real-time status
4. **Database**: Query monitoring tables for historical data

### Contributing

To contribute to the system:
1. Follow the existing code patterns
2. Add comprehensive error handling
3. Include logging for debugging
4. Write tests for new functionality
5. Update documentation

### Version History

- **v1.0.0**: Initial comprehensive system implementation
  - Complete monitoring and download system
  - Advanced scheduling and error handling
  - Real-time dashboard and alerting
  - Comprehensive data processing pipeline

---

This comprehensive system provides a robust, scalable, and intelligent solution for monitoring and downloading Florida property data. The modular architecture allows for easy extension and customization while maintaining reliability and performance.