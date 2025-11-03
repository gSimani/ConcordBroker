# 🤖 ConcordBroker Agent Library

**Location:** `.claude/agents/`
**Purpose:** Specialized agents for project management, verification, and maintenance tasks
**Status:** Active

---

## 📋 Available Agents

### 1. Scheduled Report Monitor Agent ⭐
**File:** `scheduled-report-monitor.json`
**Version:** 1.0.0
**Purpose:** Automatically monitor and maintain reports on a schedule
**Script:** `.claude/scheduler.cjs`
**Status:** ✅ Active & Tested

**Automated Tasks:**
- **Daily (2:00 AM):** Health checks, INDEX updates, duplicate detection
- **Weekly (Sunday 3:00 AM):** Weekly summaries, obsolete report identification
- **Monthly (1st, 4:00 AM):** Archive old reports, cleanup, monthly summaries

**Quick Commands:**
```bash
node .claude/scheduler.cjs --daily    # Run daily tasks now
node .claude/scheduler.cjs --weekly   # Run weekly tasks now
node .claude/scheduler.cjs --monthly  # Run monthly tasks now
node .claude/scheduler.cjs --health   # Health check only
```

**Setup:** See `.claude/SCHEDULER_SETUP.md` for Windows Task Scheduler / cron setup

---

### 2. Report Manager Agent
**File:** `report-manager.json`
**Version:** 1.0.0
**Purpose:** Manage agent task reports in `.claude/reports/`

**Capabilities:**
- ✅ List all reports with metadata (date, size, category, status)
- ✅ Archive old reports (> 30 days) to `archive/YYYY-MM/`
- ✅ Delete obsolete/superseded reports (with confirmation)
- ✅ Generate/update `INDEX.md` for easy navigation
- ✅ Cleanup duplicate reports

**Usage Examples:**
```
"List all reports from October 2025"
"Archive reports older than 30 days"
"Delete obsolete reports"
"Generate report index"
"Clean up duplicate reports"
```

**Quick Commands:**
- View index: `cat .claude/reports/INDEX.md`
- List reports: `ls -lh .claude/reports/*.md`
- Archive: Request agent to archive old reports

---

### 2. Verification Agent
**File:** `verification-agent.json`
**Version:** 1.0.0
**Purpose:** UI verification using Playwright MCP

**Capabilities:**
- ✅ Pre-work baseline verification
- ✅ Post-work verification
- ✅ Console error/warning analysis
- ✅ Network request monitoring
- ✅ Screenshot capture
- ✅ Comparison reports

**Usage Examples:**
```
"Run pre-work baseline verification on /properties page"
"Verify the fix for N+1 query problem"
"Compare baseline vs post-work metrics"
```

---

## 📁 Folder Structure

```
.claude/
├── agents/
│   ├── README.md                  # This file
│   ├── report-manager.json        # Report management agent
│   └── verification-agent.json    # UI verification agent
├── reports/
│   ├── INDEX.md                   # Auto-generated report index
│   ├── 2025-10-23_*.md           # Daily reports
│   └── archive/                   # Archived reports (> 30 days)
│       └── 2025-10/               # Monthly archive folders
├── hooks/                         # Git hooks and event hooks
├── settings.json                  # Claude Code settings
└── workflows/                     # Custom workflows
```

---

## 🎯 Agent Usage Guidelines

### How to Invoke an Agent:

1. **Direct Request:**
   ```
   "Use the Report Manager agent to list all reports"
   "Run the Verification Agent on /properties page"
   ```

2. **By Capability:**
   ```
   "Archive old reports"  → Invokes Report Manager
   "Verify UI changes"    → Invokes Verification Agent
   ```

3. **Automatic Invocation:**
   - Verification Agent runs automatically after UI changes (per permanent memory)
   - Report Manager can be scheduled for monthly cleanup

---

## 📝 Creating New Agents

### Agent Configuration Template:

```json
{
  "name": "Agent Name",
  "version": "1.0.0",
  "description": "Brief description of agent purpose",
  "type": "utility|verification|deployment|analysis",
  "capabilities": [
    "capability_1",
    "capability_2"
  ],
  "commands": {
    "command_name": {
      "description": "What this command does",
      "example": "Example usage"
    }
  },
  "rules": [
    "Rule 1: Description",
    "Rule 2: Description"
  ],
  "workflow": {
    "step_name": [
      "1. First action",
      "2. Second action"
    ]
  }
}
```

### Agent Best Practices:

1. **Single Responsibility:** Each agent should have one clear purpose
2. **Clear Commands:** Define specific commands users can request
3. **Safety Rules:** Include rules for destructive operations (require confirmation)
4. **Workflow Documentation:** Document step-by-step processes
5. **Versioning:** Use semantic versioning (major.minor.patch)

---

## 🔄 Agent Lifecycle

### Active Agents:
- Listed in this README
- Available for invocation
- Maintained and updated regularly

### Deprecated Agents:
- Moved to `archive/deprecated/`
- Documented with deprecation reason
- Replaced by newer agents

### Development Agents:
- In `dev/` subfolder
- Not yet production-ready
- Testing and validation phase

---

## 📊 Agent Metrics

**Current Stats:**
- Active Agents: 3
- Total Capabilities: 16
- Reports Generated: 7
- Last Agent Added: Scheduled Report Monitor (Oct 23, 2025)
- Automation Status: ✅ Scheduler tested and working

---

## 🚀 Future Agents (Planned)

### 1. Deployment Agent
- Deploy to Vercel, Railway, Supabase
- Run pre-deployment checks
- Monitor deployment health

### 2. Code Quality Agent
- Run linting, type checking
- Analyze code complexity
- Suggest improvements

### 3. Database Agent
- Schema migrations
- Data validation
- Query optimization

### 4. Performance Agent
- Bundle size analysis
- Lighthouse scoring
- Performance regression detection

---

## 📞 Support

**Issues:** Report agent issues in `.claude/agents/ISSUES.md`
**Requests:** Request new agents or capabilities in same file
**Documentation:** Full docs in `CLAUDE.md` and `PERMANENT_MEMORY_*.md` files

---

**Last Updated:** October 23, 2025
**Maintainer:** ConcordBroker Team
**Status:** ✅ Active Library
