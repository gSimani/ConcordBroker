# ConcordBroker Dependency Monitoring System

Automated monitoring system for Python and Node.js dependencies with MCP Server integration.

## 🎯 Overview

This system automatically monitors all critical dependencies across your ConcordBroker project and alerts you to updates, security patches, and breaking changes.

## 📦 Monitored Dependencies

### Python (Critical Libraries)
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing foundation
- **fastapi** - Modern web framework for APIs
- **supabase** - Database client for Supabase
- **sqlalchemy** - Database interaction ORM
- **matplotlib** - Data visualization
- **seaborn** - Statistical data visualization
- **scikit-learn** - Machine learning library
- **tensorflow** - Deep learning framework
- **torch** - PyTorch deep learning
- **beautifulsoup4** - Web scraping
- **scrapy** - Web scraping framework
- **opencv-python** - Computer vision
- **nltk** - Natural language processing
- **spacy** - Advanced NLP
- **pyspark** - Big data processing
- **jupyter** - Interactive notebooks
- **keras** - Neural network models
- **pillow** - Image processing

### Node.js/NPM (Critical Libraries)
- **react** - Frontend UI library
- **react-dom** - React DOM bindings
- **vite** - Frontend build tool
- **typescript** - Type safety
- **@supabase/supabase-js** - Supabase client
- **fastify** - Backend web framework
- **express** - Alternative web framework
- **axios** - HTTP client
- **eslint** - Code linting
- **prettier** - Code formatting
- **vitest** - Testing framework
- **jest** - Alternative testing
- **tailwindcss** - CSS framework

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install Python monitoring dependencies
pip install -r requirements-dependency-monitor.txt

# Install Node.js dependencies (if not already installed)
cd apps/web && npm install
cd mcp-server && npm install
```

### 2. Run Manual Check
```bash
# Check Python dependencies
python apps/workers/dependency_monitor_agent.py

# Check NPM dependencies
node apps/workers/npm_dependency_monitor.js

# Check both with summary
python apps/workers/dependency_scheduler.py --once
```

### 3. Start Automatic Monitoring
```bash
# Start the dependency scheduler (runs continuously)
python apps/workers/dependency_scheduler.py

# Or use the startup script
start_dependency_monitor.bat
```

## ⚙️ Configuration

### Monitoring Schedule
- **Regular checks**: Every 6 hours
- **Daily reports**: 9:00 AM
- **Immediate alerts**: Critical updates

### Notification Levels
- 🚨 **Critical**: Security patches, breaking changes, major version updates
- 📦 **Optional**: Minor updates, patches, feature additions

### MCP Server Integration
- Automatic notifications for critical updates
- Integration with existing alert system
- API endpoints for dependency status

## 📊 Generated Reports

### Files Created
- `dependency_monitor_report.json` - Python dependency status
- `npm_dependency_report.json` - NPM dependency status
- `dependency_summary.json` - Combined summary
- `update_dependencies.bat` - Auto-generated update script
- `update_npm_dependencies.bat` - NPM update script

### Report Structure
```json
{
  "timestamp": "2025-09-16T12:40:23.027531",
  "packages": {
    "package_name": {
      "current_version": "1.0.0",
      "latest_version": "1.1.0",
      "has_update": true,
      "is_critical": true,
      "description": "Package description",
      "release_notes_url": "https://...",
      "update_command": "pip install -U package_name"
    }
  },
  "summary": {
    "total_checked": 19,
    "updates_available": 3,
    "critical_updates": 1,
    "errors": 0
  }
}
```

## 🔧 Manual Update Commands

### Python Updates
```bash
# Update all critical packages
py -m pip install -U pandas numpy fastapi supabase sqlalchemy

# Update specific package
py -m pip install -U numpy

# Update from requirements with eager strategy
py -m pip install -U --upgrade-strategy eager -r requirements.txt

# Check for conflicts
py -m pip check
```

### NPM Updates
```bash
# Update all packages in a project
cd apps/web && npm update

# Update specific package
npm install package@latest

# Check for outdated packages
npm outdated

# Audit for security issues
npm audit
```

### Batch Update Scripts
```bash
# Run auto-generated Python update script
update_dependencies.bat

# Run auto-generated NPM update script
update_npm_dependencies.bat
```

## 🔍 Troubleshooting

### Common Issues

**Unicode Error (Windows)**
```bash
# Set UTF-8 encoding
set PYTHONIOENCODING=utf-8
python apps/workers/dependency_monitor_agent.py
```

**MCP Server Connection Failed**
- Ensure MCP Server is running on port 3001
- Check API key: `concordbroker-mcp-key`
- Verify network connectivity

**Package Not Found**
- Check if package is installed: `pip list | grep package_name`
- Verify package name spelling
- Check if package is in monitored list

### Logs and Debugging
```bash
# View dependency reports
cat dependency_monitor_report.json
cat npm_dependency_report.json

# Check MCP Server logs
cat mcp-server/claude-init.log

# Manual dependency check
py -m pip list --outdated
npm outdated
```

## 🔒 Security Features

### Automatic Security Monitoring
- Monitors for security advisories
- Alerts on CVE announcements
- Tracks dependency vulnerabilities
- Integration with `npm audit` and `pip audit`

### Update Safety
- **Dry-run mode**: Test updates before applying
- **Version pinning**: Prevent breaking changes
- **Rollback capability**: Quick revert options
- **Dependency conflict detection**

## 📈 Integration with MCP Server

### API Endpoints
```bash
# Get dependency status via MCP
curl -H "x-api-key: concordbroker-mcp-key" \
  http://localhost:3001/api/dependencies/status

# Trigger manual check
curl -X POST -H "x-api-key: concordbroker-mcp-key" \
  http://localhost:3001/api/dependencies/check
```

### Notifications
- Critical updates trigger MCP alerts
- Integration with existing notification system
- Email/Slack notifications (if configured)
- Dashboard widgets for status display

## 🎛️ Advanced Configuration

### Custom Package Lists
Edit the monitored packages in:
- `apps/workers/dependency_monitor_agent.py` (Python)
- `apps/workers/npm_dependency_monitor.js` (Node.js)

### Schedule Customization
Modify check intervals in:
- `apps/workers/dependency_scheduler.py`

### Alert Thresholds
Configure notification levels for:
- Major version updates
- Security patches
- Breaking changes
- End-of-life announcements

## 📝 Best Practices

### Update Strategy
1. **Review release notes** before updating
2. **Test in development** environment first
3. **Update critical packages** immediately
4. **Batch non-critical updates** weekly
5. **Monitor for regressions** after updates

### Version Management
- Use semantic versioning rules
- Pin critical dependencies to specific versions
- Allow patch updates automatically
- Review minor/major updates manually

### Backup Strategy
- Backup `requirements.txt` before updates
- Tag git commits before major updates
- Keep rollback scripts ready
- Document known working versions

## 🚨 Emergency Procedures

### Critical Security Update
```bash
# Immediate update for security patch
py -m pip install -U package_name==specific_version

# Verify system functionality
python -c "import package_name; print('OK')"

# Run full test suite
python -m pytest
```

### Rollback Procedure
```bash
# Revert to previous version
py -m pip install package_name==previous_version

# Restore from backup requirements
py -m pip install -r requirements-backup.txt

# Check for conflicts
py -m pip check
```

---

## 📞 Support

For issues with the dependency monitoring system:
1. Check the troubleshooting section above
2. Review generated reports and logs
3. Verify MCP Server connectivity
4. Check GitHub issues for known problems
5. Contact system administrator

**System Files:**
- Monitor Agent: `apps/workers/dependency_monitor_agent.py`
- NPM Monitor: `apps/workers/npm_dependency_monitor.js`
- Scheduler: `apps/workers/dependency_scheduler.py`
- Startup Script: `start_dependency_monitor.bat`