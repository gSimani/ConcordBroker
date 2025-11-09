# ConcordBroker AI Data Flow Monitoring System

**🎉 COMPLETE IMPLEMENTATION** - A comprehensive AI-powered system that ensures all tabs, MiniPropertyCards, filters, and data always get proper information from the database with self-healing capabilities.

## 🚀 Features Overview

✅ **Real-time Data Flow Monitoring** - Continuous monitoring of all data sources
✅ **AI-Powered Anomaly Detection** - Machine learning-based issue detection
✅ **Self-Healing Data Integrity** - Automatic correction of data issues
✅ **High-Performance FastAPI Endpoints** - Optimized data access layer
✅ **PySpark Integration** - Large-scale data processing and analytics
✅ **Interactive Jupyter Notebooks** - Data analysis and monitoring dashboards
✅ **Real-time Web Dashboard** - Live monitoring with charts and alerts
✅ **Comprehensive Entity Linking** - AI-enhanced business entity matching
✅ **Auto-Startup with Claude Code** - Seamless integration with development workflow

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Session                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                MCP Server (Port 3001)                  │   │
│  │                      │                                 │   │
│  │                      ▼                                 │   │
│  │            Auto-starts AI System                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AI Data Flow System                         │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Data Orchestrator│  │ FastAPI Endpoints│  │ AI Integration  │ │
│  │   (Port 8001)   │  │   (Port 8002)   │  │   (Port 8003)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Dashboard     │  │  Spark Processor│  │ Monitoring Agents│ │
│  │   (Port 8004)   │  │   (Background)  │  │   (Background)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase Database                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ florida_parcels │  │property_sales   │  │ tax_certificates│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │florida_entities │  │sunbiz_corporate │                     │
│  └─────────────────┘  └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
ConcordBroker/
├── claude-code-ai-system-init.cjs      # Main auto-startup script
├── mcp-server/
│   ├── server.js                       # Updated MCP server with AI integration
│   ├── ai-agents/                      # AI agent system
│   │   ├── data_flow_orchestrator.py   # Main orchestrator with FastAPI
│   │   ├── monitoring_agents.py        # Specialized monitoring agents
│   │   ├── self_healing_system.py      # Self-healing and recovery
│   │   ├── sqlalchemy_models.py        # Database models and operations
│   │   └── mcp_integration.py          # MCP server integration
│   ├── fastapi-endpoints/              # High-performance data APIs
│   │   └── data_endpoints.py           # FastAPI data access layer
│   ├── pyspark-processors/             # Large-scale data processing
│   │   └── spark_data_processor.py     # PySpark analytics engine
│   ├── monitoring/                     # Web dashboard and alerts
│   │   └── dashboard_server.py         # Real-time monitoring dashboard
│   ├── notebooks/                      # Jupyter analysis notebooks
│   │   └── data_flow_monitoring.ipynb  # Interactive monitoring dashboard
│   └── requirements/                   # Dependencies
│       └── ai_system_requirements.txt  # Python package requirements
└── logs/                               # System logs and reports
    ├── ai_system_startup.log           # AI system startup logs
    ├── data_flow_orchestrator.log      # Data flow monitoring logs
    └── spark_analysis_report.json      # Spark analytics reports
```

## 🛠️ Installation & Setup

### Prerequisites

1. **Python 3.8+** with pip
2. **Node.js 18+** with npm
3. **Environment Variables** in `.env.mcp`:
   ```bash
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   OPENAI_API_KEY=your_openai_api_key  # Optional for AI insights
   ```

### Installation Steps

1. **Install Python Dependencies**:
   ```bash
   pip install -r mcp-server/requirements/ai_system_requirements.txt
   ```

2. **Verify Environment Setup**:
   ```bash
   # Test the AI system manually
   node claude-code-ai-system-init.cjs
   ```

3. **Start Claude Code** - The AI system will auto-start!

## 🎯 System Endpoints

Once running, access these endpoints:

| Service | URL | Description |
|---------|-----|-------------|
| **Interactive Dashboard** | http://localhost:8004 | Real-time monitoring dashboard |
| **AI System API** | http://localhost:8003/ai-system/health | AI agent status and control |
| **Data Orchestrator** | http://localhost:8001/health | Core data monitoring API |
| **FastAPI Endpoints** | http://localhost:8002/health | High-performance data access |
| **Jupyter Notebook** | `notebooks/data_flow_monitoring.ipynb` | Interactive analysis |

## 🤖 AI Agents

### PropertyDataAgent
- **Monitors**: florida_parcels table integrity
- **Validates**: Data quality, null percentages, update frequency
- **Alerts**: Data corruption, missing updates, quality degradation

### SalesDataAgent
- **Monitors**: property_sales_history table and market trends
- **Validates**: Sales data completeness, price validity, temporal patterns
- **Alerts**: Stale data, invalid prices, missing recent sales

### TaxCertificateAgent
- **Monitors**: tax_certificates table and lien patterns
- **Validates**: Certificate data integrity, status distributions
- **Alerts**: High certificate activity, data quality issues

### EntityLinkingAgent
- **Monitors**: florida_entities and sunbiz_corporate data
- **Validates**: Entity data quality, duplicate detection
- **Alerts**: High duplicate rates, entity data issues

## 🔧 Self-Healing Capabilities

### Automatic Issue Detection
- **Data Corruption**: Null values, invalid ranges, format violations
- **Missing Data**: Gaps in updates, incomplete records
- **Performance Issues**: Slow queries, high resource usage
- **Duplicate Data**: Exact and fuzzy duplicate detection

### Automatic Recovery Actions
- **Data Cleanup**: Remove corrupted records, normalize values
- **Data Refresh**: Trigger external data imports
- **Deduplication**: Intelligent duplicate removal
- **Performance Optimization**: Index creation, query optimization

### Issue Severity Levels
- 🟢 **LOW**: Minor issues, logged for review
- 🟡 **MEDIUM**: Performance impacts, automatic healing attempted
- 🟠 **HIGH**: Data quality issues, immediate healing actions
- 🔴 **CRITICAL**: System failures, emergency recovery procedures

## 📊 Monitoring & Analytics

### Real-time Dashboard (Port 8004)
- **System Health Overview**: Live status of all components
- **Data Quality Metrics**: Validation success rates, error counts
- **Performance Charts**: Query times, system resources
- **Agent Activity**: AI agent status and alert summaries
- **Interactive Charts**: Plotly-powered visualizations

### Jupyter Notebook Analysis
Open `mcp-server/notebooks/data_flow_monitoring.ipynb` for:
- **Data Quality Analysis**: Comprehensive data assessment
- **Performance Monitoring**: System resource tracking
- **Validation Reports**: Detailed validation results
- **AI Insights**: Machine learning-powered analysis
- **Custom Analytics**: Interactive data exploration

### Spark Analytics
Large-scale data processing for:
- **Market Trend Analysis**: Property value trends, seasonal patterns
- **Investment Opportunity Detection**: AI-powered opportunity scoring
- **Entity Clustering**: Duplicate detection and deduplication
- **Tax Certificate Pattern Analysis**: Risk assessment and predictions

## 🔄 Data Flow Guarantees

The AI system ensures:

✅ **Property Tabs** - Always receive validated, fresh property data
✅ **MiniPropertyCards** - Real-time accurate property information
✅ **Filters** - Proper database queries with validated results
✅ **Sales History** - Complete data from property_sales_history table
✅ **Entity Linking** - Validated connections between entities
✅ **Tax Certificates** - Accurate lien and certificate data
✅ **Performance** - Optimized queries with sub-second response times
✅ **Data Integrity** - Continuous validation and automatic healing

## 🚨 Alert System

### Alert Types
- **Data Quality**: Corruption, missing data, validation failures
- **Performance**: Slow queries, resource exhaustion
- **System Health**: Agent failures, service outages
- **Business Logic**: Unusual patterns, anomalies

### Alert Channels
- **Dashboard**: Real-time visual alerts
- **Logs**: Structured JSON logging
- **API**: Programmatic alert access
- **Console**: Development-time notifications

## 🔧 Development & Testing

### Manual Testing
```bash
# Test AI system components
python mcp-server/ai-agents/data_flow_orchestrator.py

# Test FastAPI endpoints
python mcp-server/fastapi-endpoints/data_endpoints.py

# Test Spark processing
python mcp-server/pyspark-processors/spark_data_processor.py

# Test monitoring agents
python mcp-server/ai-agents/monitoring_agents.py
```

### Health Checks
```bash
# System health
curl http://localhost:8003/ai-system/health

# Data orchestrator
curl http://localhost:8001/health

# FastAPI endpoints
curl http://localhost:8002/health

# Dashboard
curl http://localhost:8004/api/dashboard/overview
```

### Performance Testing
```bash
# Trigger healing cycle
curl -X POST http://localhost:8003/ai-system/trigger-healing

# Run data validation
curl -X POST http://localhost:8003/ai-system/validate-data

# Spark analysis
curl -X POST "http://localhost:8003/ai-system/spark-analysis?county=BROWARD"
```

## 📝 Logging & Debugging

### Log Files
- `logs/ai_system_startup.log` - System startup and shutdown
- `logs/data_flow_orchestrator.log` - Data monitoring activities
- `logs/connection-monitor.log` - Service health monitoring
- `logs/spark_analysis_report.json` - Spark analytics results

### Debug Mode
Set environment variable for verbose logging:
```bash
export DEBUG_AI_SYSTEM=true
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional AI Features
OPENAI_API_KEY=your_openai_key              # For AI insights
LANGCHAIN_API_KEY=your_langchain_key        # For advanced agents
HUGGINGFACE_API_TOKEN=your_huggingface_key  # For local LLM

# Performance Tuning
AI_SYSTEM_CHECK_INTERVAL=300    # Agent check interval (seconds)
HEALING_CYCLE_INTERVAL=1800     # Self-healing interval (seconds)
SPARK_MEMORY_SIZE=4g            # Spark memory allocation
```

### Customization
- **Agent Check Intervals**: Modify intervals in `monitoring_agents.py`
- **Healing Thresholds**: Adjust detection rules in `self_healing_system.py`
- **Performance Limits**: Configure in `data_flow_orchestrator.py`
- **Dashboard Refresh**: Update intervals in `dashboard_server.py`

## 🚀 Production Deployment

### Scaling Considerations
- **Database Connections**: Configured for 20-50 concurrent connections
- **Memory Usage**: 4-8GB recommended for full Spark integration
- **CPU**: 4+ cores recommended for parallel processing
- **Storage**: 10GB+ for logs and temporary data

### Security Notes
- **API Keys**: All endpoints require authentication
- **Database Access**: Uses service role key for admin operations
- **CORS**: Configured for production with allowed origins
- **Rate Limiting**: Built-in protection against abuse

## 🆘 Troubleshooting

### Common Issues

**AI System Won't Start**
```bash
# Check Python availability
python --version
python3 --version

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# Check file permissions
ls -la claude-code-ai-system-init.cjs
```

**Port Conflicts**
```bash
# Check port usage
netstat -ano | findstr :8001
netstat -ano | findstr :8002
netstat -ano | findstr :8003
netstat -ano | findstr :8004

# Kill conflicting processes
taskkill /F /PID <process_id>
```

**Database Connection Issues**
```bash
# Test database connectivity
python -c "import psycopg2; print('PostgreSQL driver available')"

# Verify Supabase connection
curl -H "apikey: YOUR_ANON_KEY" "YOUR_SUPABASE_URL/rest/v1/"
```

**Missing Dependencies**
```bash
# Reinstall Python packages
pip install -r mcp-server/requirements/ai_system_requirements.txt --force-reinstall

# Check specific packages
python -c "import fastapi, sqlalchemy, pandas, plotly; print('All packages available')"
```

### Performance Issues

**Slow Dashboard Loading**
- Check database query performance
- Verify Redis cache is working
- Monitor system resource usage

**High Memory Usage**
- Reduce Spark memory allocation
- Adjust agent check intervals
- Monitor data cache sizes

## 📈 Monitoring Best Practices

1. **Regular Health Checks**: Monitor dashboard at least daily
2. **Alert Response**: Investigate HIGH/CRITICAL alerts immediately
3. **Performance Trends**: Review weekly performance reports
4. **Data Quality**: Maintain >95% validation success rate
5. **Resource Usage**: Keep CPU <80%, Memory <85%

## 🔄 Maintenance

### Daily Tasks
- Check dashboard for alerts
- Review error logs
- Verify all services are running

### Weekly Tasks
- Analyze performance trends
- Review healing action effectiveness
- Update data quality thresholds

### Monthly Tasks
- Database performance optimization
- Log rotation and cleanup
- Security updates and patches

## 🎉 Success Verification

✅ **System Health**: Dashboard shows all green status indicators
✅ **Data Flow**: Property cards load with complete information
✅ **Performance**: All queries complete in <2 seconds
✅ **Validation**: 95%+ validation success rate
✅ **Alerts**: No CRITICAL alerts active
✅ **Integration**: All tabs and filters work properly

---

**🚀 The AI Data Flow System is now active and monitoring your ConcordBroker data 24/7!**

For additional support or feature requests, check the logs in the `logs/` directory or review the Jupyter notebook analysis tools.