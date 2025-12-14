# Permanent Memory & Automated Verification System
## 🧠 Always Following Rules, Always Verifying Work

**Last Updated:** October 12, 2025
**Status:** ✅ Production Ready

---

## Overview

The ConcordBroker MCP Server now includes three powerful systems that work together to ensure:
1. **Permanent Memory** - Never forget rules or session context
2. **Automated Rule Enforcement** - Always follow CLAUDE.md guidelines
3. **Playwright Verification** - Automatically test every change

---

## 🧠 Permanent Memory System

### Purpose
Maintains persistent memory across sessions to ensure rules are always followed and work is tracked.

### Features
- **Rule Storage** - All CLAUDE.md rules loaded and cached
- **Session History** - Last 100 sessions tracked
- **Verification History** - Last 200 verifications recorded
- **Integration Status** - All service statuses monitored
- **Redis Backup** - Distributed memory across sessions

### API Endpoints

#### Get Rules
```bash
GET /api/memory/rules
```
Returns all loaded rules from CLAUDE.md

#### Get Recent Sessions
```bash
GET /api/memory/sessions?count=10
```
Returns last N sessions with timestamps

#### Get Verifications
```bash
GET /api/memory/verifications?count=20
```
Returns recent verification results

#### Get Memory Stats
```bash
GET /api/memory/stats
```
Returns memory system statistics

#### Check Rule Compliance
```bash
POST /api/memory/check-compliance
```
Runs immediate rule compliance check

### Rule Compliance Checks

Automatic checks every 10 minutes for:
- ✅ **No uncommitted changes** (Rule 2)
- ✅ **Port 5191 in use** (Rule 1)
- ✅ **No zombie ports** (5177-5180) (Rule 1)
- ✅ **All commits pushed** (Rule 2)

### Storage Location
```
.memory/
├── state.json          # Persistent memory state
└── screenshots/        # Verification screenshots
```

---

## 📚 DeepWiki Integration System

### Purpose
Connects to 21 knowledge repositories for enhanced capabilities

### Integrated Repositories

1. **gSimani/firecrawl** - Web scraping and data extraction
2. **gSimani/memvid** - Permanent memory management
3. **langchain-ai/local-deep-researcher** - Local research
4. **langchain-ai/langchain** - LLM orchestration
5. **huggingface/transformers** - ML transformers
6. **redis/redis** - Caching patterns
7. **codecrafters-io/build-your-own-x** - Learning patterns
8. **TheAlgorithms/Python** - Algorithm implementations
9. **Significant-Gravitas/AutoGPT** - Autonomous agents
10. **Snailclimb/JavaGuide** - Java patterns
11. **ytdl-org/youtube-dl** - Media download
12. **puppeteer/puppeteer** - Browser automation
13. **open-webui/open-webui** - Web UI components
14. **shadcn-ui/ui** - UI component library
15. **n8n-io/n8n** - Workflow automation
16. **doocs/advanced-java** - Advanced Java
17. **coder/code-server** - Remote development
18. **syncthing/syncthing** - File sync
19. **kdn251/interviews** - Interview prep
20. **browser-use/browser-use** - Browser patterns
21. **marktext/marktext** - Markdown editing

### API Endpoints

#### Get All Repositories
```bash
GET /api/deepwiki/repositories
```

#### Search Repositories
```bash
GET /api/deepwiki/search?q=automation
```
Searches all repositories for relevant content

#### Get Specific Repository
```bash
GET /api/deepwiki/:repository
```
Example: `/api/deepwiki/firecrawl`

### Usage Example

```javascript
// Search for automation patterns
const response = await fetch('http://localhost:3001/api/deepwiki/search?q=automation', {
  headers: {
    'x-api-key': 'concordbroker-mcp-key-claude'
  }
});

const data = await response.json();
// Returns repositories sorted by relevance
```

---

## 🎭 Playwright Verification System

### Purpose
Automatically tests and verifies all changes using browser automation

### Features
- **Frontend Verification** - Check UI loads correctly
- **MCP Server Verification** - Test health endpoints
- **Property Search Verification** - Test search functionality
- **Screenshot Capture** - Visual evidence of tests
- **History Tracking** - All verifications recorded

### API Endpoints

#### Verify Frontend
```bash
POST /api/verify/frontend
{
  "url": "http://localhost:5191"
}
```

#### Verify MCP Server
```bash
POST /api/verify/mcp
{
  "url": "http://localhost:3001"
}
```

#### Verify Property Search
```bash
POST /api/verify/property-search
```

#### Run All Verifications
```bash
POST /api/verify/all
```
Runs complete verification suite

#### Get Verification History
```bash
GET /api/verify/history?count=10
```

### Verification Schedule

- **Manual:** Via API endpoints
- **Automatic:** Every 30 minutes
- **On Demand:** After major changes

### Verification Checks

#### Frontend Verification
- ✅ Page loads (HTTP 200)
- ✅ No console errors
- ✅ React root element exists
- ✅ Search bar present
- 📸 Screenshot captured

#### MCP Server Verification
- ✅ Health endpoint responding
- ✅ Services healthy
- ✅ Docs endpoint available
- ✅ Service count accurate

#### Property Search Verification
- ✅ Search input found
- ✅ Search query works
- ✅ Results appear
- 📸 Screenshot captured

---

## 🚀 Auto-Start Configuration

### Start MCP Server with All Systems

```bash
cd mcp-server
npm start
```

This automatically initializes:
1. ✅ Permanent Memory System
2. ✅ DeepWiki Integrations (21 repositories)
3. ✅ Playwright Verification
4. ✅ All MCP services
5. ✅ Rule compliance monitoring

### Initialization Sequence

```
🚀 Starting ConcordBroker MCP Server...
🧠 Initializing Permanent Memory System...
   ✅ Redis memory cache connected
   ✅ Previous memory state restored
   📋 Loaded 15 rules

📚 Initializing DeepWiki Integrations...
   ✅ 21 DeepWiki repositories configured

🎭 Initializing Playwright Verification System...
   ✅ Playwright Verification System ready

✅ MCP Configuration loaded successfully
✅ Services initialized
🤖 LangChain integration initialized

🔧 Initializing Supabase MCP integration...
✅ Supabase MCP integration ready

📊 Initial Service Health:
✅ vercel: healthy
✅ railway: healthy
✅ supabase: healthy
... [all services listed]

🌐 MCP Server running on http://localhost:3001
📚 API Documentation: http://localhost:3001/docs
💚 Health Check: http://localhost:3001/health
🔌 WebSocket server running on ws://localhost:3001

✨ MCP Server ready to handle requests!

🔍 Running initial rule compliance check...
✅ All rules compliant

✅ All systems initialized and running!

📚 DeepWiki Repositories: 21
📋 Rules Loaded: 15
🎭 Playwright Verification: Active
```

---

## 📊 Monitoring & Status

### Check System Status

```bash
# Memory system stats
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  http://localhost:3001/api/memory/stats

# Current rules
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  http://localhost:3001/api/memory/rules

# Run compliance check
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  -X POST http://localhost:3001/api/memory/check-compliance

# Run full verification
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  -X POST http://localhost:3001/api/verify/all
```

### Dashboard Access

- **MCP Server:** http://localhost:3001
- **API Docs:** http://localhost:3001/docs
- **Frontend:** http://localhost:5191
- **AI Dashboard:** http://localhost:8004

---

## 🔧 Configuration

### Enable/Disable Systems

In `.env.mcp`:

```env
# Permanent Memory
REDIS_URL=redis://...  # Required for distributed memory

# Playwright Verification
PLAYWRIGHT_HEADLESS=true  # Set false to see browser

# Rule Checking
RULE_CHECK_INTERVAL=600000  # 10 minutes (milliseconds)
VERIFICATION_INTERVAL=1800000  # 30 minutes (milliseconds)
```

### Memory Persistence

Memory is saved:
- **Automatically:** Every 5 minutes
- **On Shutdown:** Clean shutdown saves all state
- **On Verification:** After each verification
- **Redis Backup:** Real-time to Redis (24hr TTL)

---

## 🛠️ Troubleshooting

### Memory System Issues

**Problem:** Memory not persisting

**Solution:**
```bash
# Check .memory directory
ls -la .memory

# Check Redis connection
curl http://localhost:3001/api/memory/stats

# Verify Redis URL in .env.mcp
echo $REDIS_URL
```

### Playwright Issues

**Problem:** Verifications failing

**Solution:**
```bash
# Install Playwright browsers
cd mcp-server
npx playwright install chromium

# Run manual verification
curl -X POST http://localhost:3001/api/verify/frontend

# Check screenshots
ls -la .memory/screenshots
```

### Rule Compliance Failures

**Problem:** Rule violations detected

**Common Violations:**
1. Uncommitted changes → Run `git add` and `git commit`
2. Zombie ports → Run `npm run port:clean`
3. Wrong port → Check vite.config.ts (should be 5191)
4. Unpushed commits → Run `git push`

---

## 📋 Complete API Reference

### Permanent Memory Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/memory/rules` | GET | Get all loaded rules |
| `/api/memory/sessions?count=N` | GET | Get recent sessions |
| `/api/memory/verifications?count=N` | GET | Get verifications |
| `/api/memory/stats` | GET | Get memory statistics |
| `/api/memory/check-compliance` | POST | Check rule compliance |

### DeepWiki Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/deepwiki/repositories` | GET | List all repositories |
| `/api/deepwiki/search?q=query` | GET | Search repositories |
| `/api/deepwiki/:repository` | GET | Get specific repo |

### Playwright Verification Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/verify/frontend` | POST | Verify frontend |
| `/api/verify/mcp` | POST | Verify MCP server |
| `/api/verify/property-search` | POST | Verify property search |
| `/api/verify/all` | POST | Run all verifications |
| `/api/verify/history?count=N` | GET | Get verification history |

---

## 🎯 Best Practices

### 1. Always Run Verifications Before Committing
```bash
curl -X POST http://localhost:3001/api/verify/all
```

### 2. Check Rule Compliance Regularly
```bash
curl -X POST http://localhost:3001/api/memory/check-compliance
```

### 3. Review Verification History
```bash
curl http://localhost:3001/api/verify/history?count=20
```

### 4. Monitor Memory Stats
```bash
curl http://localhost:3001/api/memory/stats
```

### 5. Use DeepWiki for Patterns
```bash
curl 'http://localhost:3001/api/deepwiki/search?q=browser+automation'
```

---

## 📖 Rules Being Enforced

From CLAUDE.md:

1. **ONE UI Website - ONE Port - ONE Branch**
   - UI on port 5191
   - No zombie ports (5177-5180)
   - One branch workflow

2. **Continuous Merge - Commit Immediately**
   - Commit after every feature/fix
   - Push commits immediately
   - Never end session with uncommitted changes

3. **Verify Work Complete**
   - Run `npm run verify:complete`
   - All changes committed
   - All commits pushed
   - No zombie servers

4. **Golden Rules**
   - If not committed/pushed, it doesn't exist
   - If zombie port, kill it
   - If not port 5191, it's wrong
   - ONE UI website, not multiple
   - Work merges continuously

---

## 🚀 Quick Start

### 1. Start Everything
```bash
# From project root
node start-session.bat

# Or manually
cd mcp-server && npm start
cd apps/web && npm run dev
```

### 2. Verify It's Working
```bash
# Check all systems
curl http://localhost:3001/api/memory/stats
curl http://localhost:3001/api/deepwiki/repositories
curl -X POST http://localhost:3001/api/verify/all
```

### 3. Monitor Status
```bash
# Watch logs
tail -f mcp-server/claude-init.log

# Check memory
ls -la .memory/
```

---

## ✅ Success Checklist

Before ending any session:

- [ ] Run full verification: `POST /api/verify/all`
- [ ] Check rule compliance: `POST /api/memory/check-compliance`
- [ ] Review any violations
- [ ] Commit all changes
- [ ] Push all commits
- [ ] Verify memory saved
- [ ] No zombie ports running

---

**Your MCP Server now has permanent memory, automated rule enforcement, and continuous verification!** 🎉

Every session remembers the rules. Every change is verified. Every rule is enforced.
