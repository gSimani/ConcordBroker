# Florida Property Data Agent System

A comprehensive, production-ready agent architecture for automated daily updates of Florida property data from the Florida Revenue portal to Supabase database.

## 🏗️ Architecture Overview

The Florida Agent System consists of six main components working together to provide reliable, automated property data synchronization:

### Core Components

1. **Main Orchestrator Agent** (`florida_agent_orchestrator.py`)
   - Central coordination system managing all activities
   - Handles scheduling, error recovery, and system health
   - Supports multiple operation modes (daemon, single, dashboard, health)

2. **Download Agent** (`florida_download_agent.py`)
   - Automated discovery and download of NAL, NAP, and SDF files
   - Intelligent change detection using checksums and timestamps
   - Rate limiting and retry logic with exponential backoff

3. **Processing Agent** (`florida_processing_agent.py`)
   - Data validation and quality checks
   - CSV parsing with error handling and batch processing
   - Data transformation and normalization for database compatibility

4. **Database Agent** (`florida_database_agent.py`)
   - Batch upsert operations for optimal performance
   - Automatic schema management and table creation
   - Transaction management with rollback capabilities

5. **Monitoring Agent** (`florida_monitoring_agent.py`)
   - Real-time system health monitoring and metrics collection
   - Alert generation and notification system (email/webhook)
   - Performance analytics and trend analysis

6. **Configuration Manager** (`florida_config_manager.py`)
   - Centralized configuration with environment overrides
   - Encrypted secret management and validation
   - Hot reloading and multi-environment support

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ 
- Active Supabase project with database access
- 5GB+ available disk space
- Network access to Florida Revenue portal

### Installation

1. **Deploy the system:**
   ```bash
   cd apps/agents
   python deploy_florida_agents.py --env production
   ```

2. **Configure credentials:**
   ```bash
   cd /opt/florida-agents  # or C:\florida-agents on Windows
   nano config/.env
   ```
   
   Update with your actual Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
   ```

3. **Start the services:**
   ```bash
   ./scripts/start_agents.sh
   ```

4. **Verify operation:**
   ```bash
   ./scripts/health_check.sh
   ```

## 📊 Data Sources

The system monitors and processes three types of Florida property data files:

### NAL Files (Name Address Legal)
- **Content**: Property owner information, addresses, legal descriptions
- **Frequency**: Updated annually, typically in January
- **Format**: Tab-delimited text files, compressed as ZIP
- **Key Fields**: Parcel ID, Owner Name, Property Address, Legal Description

### NAP Files (Name Address Property)  
- **Content**: Property characteristics, assessments, valuations
- **Frequency**: Updated annually with assessment data
- **Format**: Tab-delimited text files, compressed as ZIP  
- **Key Fields**: Parcel ID, Property Use Code, Assessed Value, Just Value

### SDF Files (Sales Data Files)
- **Content**: Property sales transactions and deed information
- **Frequency**: Updated monthly with new sales
- **Format**: Tab-delimited text files, compressed as ZIP
- **Key Fields**: Parcel ID, Sale Date, Sale Price, Qualified Sale indicator

## 🏛️ Database Schema

The system automatically creates and manages three main tables in your Supabase database:

### florida_nal_data
```sql
CREATE TABLE florida_nal_data (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(2) NOT NULL,
    year VARCHAR(6) NOT NULL,
    owner_name TEXT,
    property_address TEXT,
    legal_description TEXT,
    -- Additional columns for complete NAL data
    record_hash VARCHAR(32),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### florida_nap_data
```sql
CREATE TABLE florida_nap_data (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(2) NOT NULL,
    year VARCHAR(6) NOT NULL,
    property_use_code VARCHAR(10),
    assessed_value DECIMAL(15,2),
    just_value DECIMAL(15,2),
    living_area INTEGER,
    year_built INTEGER,
    -- Additional NAP fields
    record_hash VARCHAR(32),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### florida_sdf_data
```sql
CREATE TABLE florida_sdf_data (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(2) NOT NULL,
    year VARCHAR(6) NOT NULL,
    sale_date DATE,
    sale_price DECIMAL(15,2),
    qualified_sale VARCHAR(1),
    grantor_name TEXT,
    grantee_name TEXT,
    -- Additional SDF fields
    record_hash VARCHAR(32),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## ⚙️ Configuration

### Environment Configuration

The system supports three environments with different defaults:

- **Development**: Reduced concurrency, verbose logging, smaller batches
- **Staging**: Moderate settings, subset of counties enabled
- **Production**: Full performance optimization, all counties enabled

### County Configuration

Configure which Florida counties to monitor in `config/florida_agent_config.json`:

```json
{
  "counties": {
    "broward": {
      "code": "12",
      "name": "Broward County", 
      "enabled": true,
      "priority": 1
    },
    "miami_dade": {
      "code": "25",
      "name": "Miami-Dade County",
      "enabled": true,
      "priority": 2
    }
  }
}
```

### Performance Tuning

Key performance settings in configuration:

```json
{
  "download": {
    "max_concurrent": 5,
    "rate_limit_seconds": 1.0
  },
  "processing": {
    "batch_size": 10000,
    "max_workers": 4
  },
  "database": {
    "max_connections": 10,
    "batch_size": 1000
  }
}
```

### Notification Setup

Configure email and webhook alerts:

```json
{
  "monitoring": {
    "notifications": {
      "email": {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "from_address": "alerts@yourdomain.com",
        "to_addresses": ["admin@yourdomain.com"]
      },
      "webhook": {
        "enabled": true,
        "url": "https://your-webhook-endpoint.com/alerts"
      }
    }
  }
}
```

## 🕐 Scheduling

### Daily Operations

The system runs automatically at 2 AM daily by default. The daily operation cycle includes:

1. **Discovery Phase**: Check Florida Revenue portal for new/updated files
2. **Download Phase**: Download any changed files with progress tracking  
3. **Processing Phase**: Validate, transform, and prepare data for database
4. **Database Phase**: Batch upsert data with conflict resolution
5. **Monitoring Phase**: Update metrics, check health, send alerts

### Custom Scheduling

Modify scheduling in configuration:

```json
{
  "scheduling": {
    "daily_hour": 2,
    "enable_hourly_checks": true
  }
}
```

### Manual Operations

Run operations manually:

```bash
# Single operation run
python agents/florida_agent_orchestrator.py --mode single

# Health check only  
python agents/florida_agent_orchestrator.py --mode health

# Interactive dashboard
python agents/florida_agent_orchestrator.py --mode dashboard
```

## 📊 Monitoring & Alerts

### Health Monitoring

The system continuously monitors:

- **System Resources**: CPU, memory, disk usage
- **Application Metrics**: Files processed, success rates, error counts
- **Database Health**: Connection status, query performance
- **Network Connectivity**: Access to Florida Revenue portal

### Alert Types

**Critical Alerts** (immediate notification):
- System failures or crashes
- Database connectivity issues
- High error rates (>25%)

**Warning Alerts** (periodic notification):
- Resource usage above thresholds
- Performance degradation
- Individual component failures

**Info Alerts** (logged only):
- Successful operations
- Configuration changes
- Routine maintenance events

### Metrics Dashboard

Access real-time metrics via the interactive dashboard:

```bash
python agents/florida_agent_orchestrator.py --mode dashboard
```

Dashboard shows:
- System overview and status
- Component health indicators  
- Recent operation results
- Resource usage trends
- Active alerts summary

## 🔧 Operations & Maintenance

### Daily Operations Checklist

1. **Morning Check** (after scheduled run):
   ```bash
   ./scripts/health_check.sh
   tail -50 logs/orchestrator.log
   ```

2. **Review Metrics**: Check dashboard for any warnings or performance issues

3. **Validate Data**: Spot-check database for recent updates

### Weekly Maintenance

1. **Review Logs**: Check for patterns in errors or performance issues
2. **Database Maintenance**: Run cleanup for old data if needed
3. **Configuration Review**: Verify settings are optimal for current load

### Monthly Maintenance

1. **Performance Analysis**: Review metrics trends and optimize settings
2. **Capacity Planning**: Monitor growth and adjust resources if needed
3. **Security Updates**: Update dependencies and review access logs

### Troubleshooting

#### Common Issues

**Services not starting:**
```bash
# Check logs for errors
tail -100 logs/orchestrator.log

# Verify configuration
python agents/florida_agent_orchestrator.py --mode config

# Test database connection
python -c "import asyncpg; print('asyncpg available')"
```

**No data being downloaded:**
```bash
# Test connectivity to Florida portal
curl -I https://floridarevenue.com/property/dataportal/

# Check download agent logs
grep -i "error\|fail" logs/orchestrator.log

# Run discovery manually
python agents/florida_agent_orchestrator.py --mode single
```

**Database connection issues:**
```bash
# Verify environment variables
env | grep SUPABASE

# Test database connectivity
python -c "
import os
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect(os.getenv('SUPABASE_DB_URL'))
    result = await conn.fetchval('SELECT 1')
    await conn.close()
    print(f'Database test: {result}')

asyncio.run(test_db())
"
```

#### Log Locations

- **Application Logs**: `logs/orchestrator.log`, `logs/monitor.log`
- **System Logs**: `/var/log/florida-agent/` (Linux)
- **Error Logs**: Filtered with `grep -i error logs/*.log`

### Performance Optimization

#### For High-Volume Processing

```json
{
  "processing": {
    "batch_size": 50000,
    "max_workers": 8
  },
  "database": {
    "max_connections": 20,
    "batch_size": 5000,
    "enable_parallel": true,
    "max_parallel_ops": 10
  }
}
```

#### For Resource-Constrained Systems

```json
{
  "download": {
    "max_concurrent": 2,
    "rate_limit_seconds": 2.0
  },
  "processing": {
    "batch_size": 1000,
    "max_workers": 2,
    "memory_limit_mb": 1024
  },
  "database": {
    "max_connections": 5,
    "batch_size": 500
  }
}
```

## 🔒 Security Considerations

### Credential Management

- Store credentials in environment variables or encrypted configuration
- Use Supabase service keys with minimal required permissions
- Rotate credentials regularly (quarterly recommended)

### Network Security

- Ensure secure connections (HTTPS/SSL) to all external services
- Consider VPN or private networking for database connections
- Monitor and log all external API calls

### Data Protection

- Implement data retention policies for historical data
- Consider encryption at rest for sensitive property information  
- Regular backups of configuration and processed data

## 🚀 Scaling Considerations

### Horizontal Scaling

- Deploy multiple instances with different county assignments
- Use message queues for coordination between instances
- Implement distributed locking for shared resources

### Vertical Scaling

- Increase processing workers and database connections
- Optimize batch sizes based on available memory
- Consider dedicated database instances for high throughput

### Multi-County Deployment

For processing all 67 Florida counties:

1. **Resource Requirements**:
   - 16GB+ RAM for processing large datasets
   - 100GB+ storage for data files and databases
   - Robust network connection for downloads

2. **Configuration Adjustments**:
   ```json
   {
     "download": {
       "max_concurrent": 10
     },
     "processing": {
       "batch_size": 25000,
       "max_workers": 12
     },
     "database": {
       "max_connections": 25
     }
   }
   ```

## 📈 Advanced Features

### Custom Data Processing

Extend the processing agent with custom validation rules:

```python
# In florida_processing_agent.py
custom_rules = [
    ValidationRule("CUSTOM_FIELD", "required", {}, "error"),
    ValidationRule("PRICE_FIELD", "range", {"min": 1000, "max": 50000000}, "warning")
]
```

### Integration with External Systems

The system can be extended to integrate with:

- **CRM Systems**: Export processed data to customer systems
- **Analytics Platforms**: Stream metrics to business intelligence tools  
- **Notification Systems**: Custom alert channels (Slack, Teams, etc.)

### API Extensions

Build REST APIs on top of the agent system:

```python
# Example Flask API endpoint
@app.route('/api/trigger-sync', methods=['POST'])
def trigger_sync():
    # Trigger immediate synchronization
    orchestrator.run_daily_update_cycle()
    return {"status": "triggered"}
```

## 🤝 Contributing

### Development Setup

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd apps/agents
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Development Configuration**:
   ```bash
   cp florida_agent_config.json config_development.json
   # Edit config_development.json for local settings
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/
   ```

### Code Standards

- **Python Style**: Follow PEP 8 guidelines
- **Documentation**: Comprehensive docstrings for all functions
- **Error Handling**: Explicit exception handling with logging
- **Type Hints**: Use type annotations for better code clarity

### Adding New Data Sources

To add support for additional Florida data sources:

1. **Extend Download Agent**: Add discovery logic for new file patterns
2. **Update Processing Agent**: Add validation rules and field mappings
3. **Modify Database Agent**: Create new table schemas
4. **Update Configuration**: Add data source settings

## 📞 Support

### Documentation

- **Configuration Reference**: See `config/` directory for examples
- **API Documentation**: Auto-generated from code docstrings
- **Troubleshooting Guide**: Common issues and solutions above

### Community

- **Issues**: Report bugs or request features via GitHub issues
- **Discussions**: Architecture questions and usage patterns
- **Contributions**: Pull requests welcome for improvements

### Professional Support

For enterprise deployments, consider:

- **Custom Integration**: Tailored data processing pipelines
- **Performance Tuning**: Optimization for specific use cases
- **Training & Setup**: Guided deployment and configuration
- **24/7 Monitoring**: Managed service offerings

---

## 📄 License

This Florida Property Data Agent System is designed for legitimate property research and analysis purposes. Users are responsible for complying with all applicable terms of service and data usage policies from Florida Revenue and other data sources.

**Built with ❤️ for the Florida property data community** 🏠📊