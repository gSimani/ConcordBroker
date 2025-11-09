# 🤖 Sunbiz Supervisor Agent - Permanent Orchestration System

## Overview
The **Sunbiz Supervisor Agent** is a comprehensive, permanent system that oversees the daily extraction and updating of the Florida Sunbiz database. It ensures your database stays synchronized with zero manual intervention.

## 🎯 Key Features

### **Permanent Operation**
- Runs continuously as a system service (Windows) or daemon (Linux)
- Automatic startup on system boot
- Self-monitoring and self-healing capabilities
- Graceful shutdown handling

### **Intelligent Orchestration**
- **Daily Updates**: Automatically processes new files at 2 AM EST
- **Verification**: Validates updates 30 minutes after processing
- **Weekly Audits**: Comprehensive system audit every Sunday
- **Task Prioritization**: Critical, High, Normal, and Low priority levels

### **Health Monitoring**
- Database connectivity checks every 5 minutes
- SFTP server availability monitoring
- Data freshness validation
- Error rate tracking
- Automatic recovery from failures

### **Self-Healing Capabilities**
- Automatic retry with exponential backoff
- Connection pool management
- Graceful degradation
- Error recovery workflows
- Configurable max retry attempts

### **Real-Time Dashboard**
- Web-based monitoring interface
- Live metrics and statistics
- Task execution history
- Health status visualization
- Manual control triggers

## 📦 Components

### 1. **sunbiz_supervisor_agent.py**
Core orchestration engine with:
- Task scheduling and execution
- Health monitoring loops
- Error handling and recovery
- Metric collection
- Notification system

### 2. **sunbiz_supervisor_service.py**
Platform-specific service wrapper:
- Windows Service implementation
- Linux daemon support
- Process monitoring
- Automatic restart on failure

### 3. **sunbiz_supervisor_dashboard.py**
Web dashboard with:
- Real-time status monitoring
- Performance metrics
- Task management
- Health check visualization
- Manual intervention controls

### 4. **Daily Update Components**
- `florida_daily_updater.py` - Local execution
- `florida_cloud_updater.py` - Cloud-ready version

## 🚀 Installation

### Windows Installation

Run PowerShell as Administrator:
```powershell
# Quick install
.\install_sunbiz_supervisor.ps1

# Manual install
python apps/agents/sunbiz_supervisor_service.py install
python apps/agents/sunbiz_supervisor_service.py start
```

### Linux Installation

```bash
# Install dependencies
pip install psycopg2-binary paramiko schedule fastapi uvicorn python-daemon

# Install as systemd service
sudo cp sunbiz_supervisor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sunbiz_supervisor
sudo systemctl start sunbiz_supervisor
```

### Docker Installation

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY apps/agents/ ./agents/
CMD ["python", "agents/sunbiz_supervisor_agent.py"]
```

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│         SUNBIZ SUPERVISOR AGENT         │
│                                         │
│  ┌─────────────┐    ┌─────────────┐   │
│  │  Scheduler  │────│   Monitor   │   │
│  └─────────────┘    └─────────────┘   │
│         │                  │           │
│         ▼                  ▼           │
│  ┌─────────────┐    ┌─────────────┐   │
│  │Task Manager │    │Health Check │   │
│  └─────────────┘    └─────────────┘   │
│         │                  │           │
└─────────┬──────────────────┬───────────┘
          │                  │
          ▼                  ▼
   ┌──────────┐        ┌──────────┐
   │   SFTP   │        │ Supabase │
   │  Server  │        │ Database │
   └──────────┘        └──────────┘
```

## 🔧 Configuration

### Environment Variables
```bash
DATABASE_URL=postgres://user:pass@host:port/database
UPDATE_SCHEDULE=02:00
HEALTH_CHECK_INTERVAL=300
MAX_RETRIES=3
ENABLE_AUTO_RECOVERY=true
ALERT_EMAIL=admin@example.com
WEBHOOK_URL=https://hooks.slack.com/services/...
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic
```

### Configuration File
Create `sunbiz_supervisor_config.json`:
```json
{
  "database_url": "postgres://...",
  "update_schedule": "02:00",
  "health_check_interval": 300,
  "max_retries": 3,
  "enable_auto_recovery": true,
  "alert_email": "admin@example.com",
  "webhook_url": "https://..."
}
```

## 📈 Monitoring

### Dashboard Access
```
http://localhost:8080
```

### Key Metrics
- **System Status**: IDLE, PROCESSING, ERROR, RECOVERING
- **Uptime**: Continuous operation time
- **Success Rate**: Percentage of successful updates
- **Records Processed**: Total entities synchronized
- **Last Update**: Timestamp of most recent sync

### Health Checks
- Database connectivity
- SFTP server availability
- Data freshness (< 48 hours)
- Error rate (< 10%)

## 🔍 Database Schema

The supervisor creates and maintains these tables:

### sunbiz_supervisor_status
- Current operational status
- Performance metrics
- Error logs
- Timestamps

### sunbiz_task_log
- Task execution history
- Duration and performance
- Error details
- Metadata

### sunbiz_health_metrics
- Health check results
- Threshold violations
- System metrics
- Timestamps

### florida_daily_processed_files
- Processed file tracking
- Record counts
- Processing times
- Status flags

## 🛠️ Management Commands

### Windows
```powershell
# Service management
Start-Service -Name SunbizSupervisor
Stop-Service -Name SunbizSupervisor
Restart-Service -Name SunbizSupervisor
Get-Service -Name SunbizSupervisor

# View logs
Get-Content "C:\ProgramData\SunbizSupervisor\logs\sunbiz_supervisor.log" -Tail 50
```

### Linux
```bash
# Service management
sudo systemctl start sunbiz_supervisor
sudo systemctl stop sunbiz_supervisor
sudo systemctl restart sunbiz_supervisor
sudo systemctl status sunbiz_supervisor

# View logs
sudo journalctl -u sunbiz_supervisor -f
```

### Manual Control
```python
# Trigger immediate update
python -c "from sunbiz_supervisor_agent import *; agent = SunbizSupervisorAgent(); agent._run_daily_update()"

# Run health check
python -c "from sunbiz_supervisor_agent import *; agent = SunbizSupervisorAgent(); print(agent._perform_health_check())"

# Get status
python -c "from sunbiz_supervisor_agent import *; agent = SunbizSupervisorAgent(); print(agent.get_status())"
```

## 📊 Performance

### Processing Capabilities
- **Files per day**: Unlimited (processes all available)
- **Records per second**: ~1,000
- **Memory usage**: < 200MB
- **CPU usage**: < 5% idle, 20-30% processing
- **Network efficiency**: Direct streaming, no local storage

### Automatic Optimizations
- Connection pooling
- Batch processing
- Efficient deduplication
- PostgreSQL COPY for bulk inserts
- Incremental updates only

## 🔐 Security

### Built-in Security Features
- Credential storage via environment variables
- Secure SFTP connections
- SSL database connections
- No sensitive data in logs
- Audit trail maintenance

### Access Control
- Dashboard authentication (optional)
- Service runs under restricted account
- Database user with minimal privileges

## 🚨 Alerts & Notifications

### Alert Conditions
- Update failures
- Health check failures
- Data staleness (> 48 hours)
- High error rate (> 10%)
- Service crashes

### Notification Channels
- Email alerts
- Webhook notifications (Slack, Teams, Discord)
- AWS SNS integration
- Dashboard visual alerts
- Log file entries

## 🔄 Recovery Procedures

### Automatic Recovery
1. **Connection failures**: Automatic reconnection with backoff
2. **Task failures**: Retry with configurable attempts
3. **Service crashes**: Auto-restart via service manager
4. **Data corruption**: Transaction rollback and retry

### Manual Recovery
```bash
# Clear error state
UPDATE sunbiz_supervisor_status SET status = 'idle' WHERE id = (SELECT MAX(id) FROM sunbiz_supervisor_status);

# Reset task log
DELETE FROM sunbiz_task_log WHERE status = 'failed' AND created_at < NOW() - INTERVAL '7 days';

# Force immediate update
curl -X POST http://localhost:8080/api/tasks/trigger -H "Content-Type: application/json" -d '{"task_name":"daily_update"}'
```

## 📈 Success Metrics

The system is operating correctly when:
- ✅ Daily updates complete by 3 AM EST
- ✅ Success rate > 95%
- ✅ All health checks passing
- ✅ No unrecovered errors > 24 hours old
- ✅ Dashboard accessible and responsive

## 🤝 Support & Troubleshooting

### Common Issues

1. **Service won't start**
   - Check database connectivity
   - Verify credentials in config
   - Review service logs

2. **Updates failing**
   - Check SFTP server status
   - Verify network connectivity
   - Review Florida DOS announcements

3. **High memory usage**
   - Restart service
   - Check for memory leaks
   - Review batch size settings

4. **Dashboard not accessible**
   - Check port 8080 availability
   - Verify FastAPI is running
   - Review firewall settings

### Log Locations
- **Windows**: `C:\ProgramData\SunbizSupervisor\logs\`
- **Linux**: `/var/log/sunbiz_supervisor/`
- **Docker**: `docker logs sunbiz_supervisor`

## 🎉 Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Permanent Operation | ✅ | Runs 24/7 as system service |
| Daily Updates | ✅ | Automatic at 2 AM EST |
| Health Monitoring | ✅ | Every 5 minutes |
| Self-Healing | ✅ | Automatic recovery |
| Web Dashboard | ✅ | Real-time monitoring |
| Notifications | ✅ | Email, webhook, SNS |
| Weekly Audits | ✅ | Comprehensive validation |
| Error Recovery | ✅ | Retry with backoff |
| Task Prioritization | ✅ | 4 priority levels |
| Graceful Shutdown | ✅ | Clean termination |

---

**Built with reliability and automation in mind - ensuring your Florida business data is always current!** 🚀