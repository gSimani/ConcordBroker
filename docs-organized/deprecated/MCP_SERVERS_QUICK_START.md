# MCP Servers Quick Start Guide
## ConcordBroker - Fast Installation & Configuration

**Last Updated:** 2025-10-20

---

## TL;DR - One Command Installation

```bash
# Install ALL critical MCP servers at once
npm install --save-dev \
  @modelcontextprotocol/server-filesystem \
  @modelcontextprotocol/server-memory \
  @modelcontextprotocol/server-postgres \
  @modelcontextprotocol/server-sequential-thinking \
  @modelcontextprotocol/server-fetch \
  @playwright/mcp \
  @railway/mcp-server \
  mcp-handler \
  supabase-mcp \
  @huggingface/mcp-client \
  aistudio-mcp-server \
  @e2b/mcp-server \
  @redis/mcp-redis \
  mcp-server-firecrawl \
  @modelcontextprotocol/server-cloudflare
```

---

## Quick Configuration

**Step 1: Install Servers** (see command above)

**Step 2: Copy Configuration**

Create/update: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {"POSTGRES_URL": "${POSTGRES_URL}"}
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "railway": {
      "command": "npx",
      "args": ["-y", "@railway/mcp-server"],
      "env": {"RAILWAY_API_TOKEN": "${RAILWAY_API_TOKEN}"}
    },
    "vercel": {
      "command": "npx",
      "args": ["-y", "mcp-handler"],
      "env": {"VERCEL_API_TOKEN": "${VERCEL_API_TOKEN}"}
    },
    "supabase": {
      "command": "npx",
      "args": ["-y", "supabase-mcp"],
      "env": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}"
      }
    },
    "huggingface": {
      "command": "npx",
      "args": ["-y", "@huggingface/mcp-client"],
      "env": {"HUGGINGFACE_API_TOKEN": "${HUGGINGFACE_API_TOKEN}"}
    },
    "gemini": {
      "command": "npx",
      "args": ["-y", "aistudio-mcp-server"],
      "env": {"GEMINI_API_KEY": "${GOOGLE_AI_STUDIO_API_KEY}"}
    },
    "e2b": {
      "command": "npx",
      "args": ["-y", "@e2b/mcp-server"],
      "env": {"E2B_API_KEY": "${E2B_API_KEY}"}
    },
    "redis": {
      "command": "npx",
      "args": ["-y", "@redis/mcp-redis"],
      "env": {"REDIS_URL": "${REDIS_URL}"}
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "mcp-server-firecrawl"],
      "env": {"FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY}"}
    }
  }
}
```

**Step 3: Set Environment Variables**

Add to `.env.mcp`:

```bash
# Critical - Required for all servers
POSTGRES_URL=postgresql://postgres.pmispwtdngkcmsrsjwbp:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key_here
RAILWAY_API_TOKEN=your_key_here
VERCEL_API_TOKEN=your_key_here

# AI/ML - Recommended
HUGGINGFACE_API_TOKEN=your_key_here
GOOGLE_AI_STUDIO_API_KEY=your_key_here
E2B_API_KEY=your_key_here

# Infrastructure - Optional
REDIS_URL=your_redis_url_here
FIRECRAWL_API_KEY=your_key_here
CLOUDFLARE_API_TOKEN=your_key_here
```

**Step 4: Restart Claude Desktop**

---

## Verify Installation

```bash
# Test a few servers
npx @modelcontextprotocol/server-filesystem --version
npx @playwright/mcp --version
npx @railway/mcp-server --version
```

---

## What You Get

| Server | What It Does | Priority |
|--------|--------------|----------|
| **filesystem** | File operations, search, read/write | CRITICAL |
| **memory** | Persistent knowledge graph memory | CRITICAL |
| **postgres** | Direct database queries | CRITICAL |
| **playwright** | Browser automation & testing | CRITICAL |
| **railway** | Railway deployment & management | CRITICAL |
| **vercel** | Vercel deployment & management | CRITICAL |
| **supabase** | Supabase database operations | CRITICAL |
| **huggingface** | AI model inference | HIGH |
| **gemini** | Google Gemini AI integration | HIGH |
| **e2b** | Code execution sandbox | HIGH |
| **redis** | Redis cache management | MEDIUM |
| **firecrawl** | Web scraping | MEDIUM |

---

## Troubleshooting

**Problem:** `npx` command not found
```bash
# Windows - verify Node.js installation
where npx
# Should show: C:\Program Files\nodejs\npx.cmd
```

**Problem:** MCP server fails to start
```bash
# Check environment variables
echo $env:POSTGRES_URL  # PowerShell
echo %POSTGRES_URL%     # CMD
```

**Problem:** Claude Desktop doesn't see servers
1. Close Claude Desktop completely
2. Check `claude_desktop_config.json` syntax (use JSON validator)
3. Restart Claude Desktop
4. Check Claude Desktop logs: `%APPDATA%\Claude\logs\`

**Problem:** Permission errors
```bash
# Run as administrator (Windows)
# Or use global install
npm install -g @modelcontextprotocol/server-filesystem
```

---

## Next Steps

1. ✅ Install servers (see command above)
2. ✅ Configure Claude Desktop
3. ✅ Set environment variables
4. ✅ Restart Claude Desktop
5. ✅ Test file operations in Claude
6. ✅ Test database queries in Claude
7. ✅ Test deployments in Claude

**Full details:** See `MCP_SERVERS_COMPLETE_AUDIT.md`

---

## Quick Reference

```bash
# List all installed MCP servers
npm list --depth=0 | grep mcp

# Update all MCP servers
npm update @modelcontextprotocol/server-* @playwright/mcp @railway/mcp-server mcp-handler supabase-mcp

# Remove all MCP servers (if needed)
npm uninstall @modelcontextprotocol/server-* @playwright/mcp @railway/mcp-server mcp-handler supabase-mcp

# Test MCP server manually
npx @modelcontextprotocol/server-filesystem
```

---

**Time to implement:** 30 minutes
**Difficulty:** Easy
**Impact:** HIGH - Unlocks full Claude Code potential
