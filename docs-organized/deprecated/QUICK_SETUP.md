# ConcordBroker Quick Setup Guide

## 🚀 TLDR - One Command Setup

When you start Claude Code, simply run:

```bash
node claude-code-robust-init.cjs
```

This will automatically:
- ✅ Load proper environment from `.env.mcp`
- ✅ Kill any conflicting processes on ports 3005-3008
- ✅ Start MCP Server on dedicated port (3005)
- ✅ Connect to all APIs (Supabase, Vercel, Railway, GitHub)
- ✅ Verify all services are healthy
- ✅ Provide fallback recovery if anything fails

## 📋 What We Fixed

### Original Issues:
1. **Invalid OpenAI API Key** → LangChain initialization failure
2. **Port Conflicts** → Multiple agents using same ports
3. **Environment Confusion** → Wrong `.env` file being loaded
4. **No Error Recovery** → Single point of failure

### Solutions Applied:
1. **Auto-disable LangChain** → `DISABLE_LANGCHAIN=true` by default
2. **Dedicated Port Management** → Port 3005 with auto-fallback to 3006-3008
3. **Proper Environment Loading** → Always use `.env.mcp` configuration
4. **Robust Error Handling** → Multiple retry mechanisms and recovery options

## 🔧 Manual Troubleshooting

### If Auto-Setup Fails:

1. **Check Port Usage**:
   ```bash
   netstat -ano | findstr :3005
   ```

2. **Kill Conflicting Processes**:
   ```bash
   taskkill /F /IM node.exe
   ```

3. **Verify Environment**:
   ```bash
   # Check if .env.mcp exists
   dir .env.mcp

   # Verify key variables are set
   echo %MCP_PORT%
   echo %MCP_API_KEY%
   ```

4. **Test Connection**:
   ```bash
   curl http://localhost:3005/health
   curl -H "x-api-key: concordbroker-mcp-key-claude" http://localhost:3005/api/supabase/User
   ```

## 🎯 Expected Results

When successful, you should see:

```
✅ Loaded 25 environment variables from .env.mcp
✅ MCP Server is healthy and ready!
✅ Supabase connection verified
✅ Vercel connection verified
✅ GitHub connection verified
🎉 Claude Code initialization completed successfully!
📡 MCP Server running at: http://localhost:3005
🔑 API Key: concordbro...
```

## 🔌 Available APIs

Once connected, you can access:

### Core Services:
- **Supabase**: `http://localhost:3005/api/supabase/:table`
- **Vercel**: `http://localhost:3005/api/vercel/project`
- **Railway**: `http://localhost:3005/api/railway/status`
- **GitHub**: `http://localhost:3005/api/github/commits`

### Authentication:
All API calls require header:
```
x-api-key: concordbroker-mcp-key-claude
```

### WebSocket:
Real-time updates available at:
```
ws://localhost:3005
```

## 🆘 Emergency Commands

### Nuclear Reset:
```bash
taskkill /F /IM node.exe
timeout 3
node claude-code-robust-init.cjs
```

### Check What's Running:
```bash
netstat -ano | findstr :300
tasklist | findstr node
```

### View Logs:
```bash
type mcp-server\claude-init.log
```

## ✨ What's Different from Before

| **Before** | **Now** |
|------------|---------|
| Manual port guessing | Dedicated port 3005 with auto-fallback |
| Single initialization attempt | Multi-retry with recovery mechanisms |
| LangChain blocking startup | Auto-disabled if problematic |
| Generic error messages | Detailed logging and troubleshooting |
| No process cleanup | Intelligent cleanup of conflicts |
| Environment confusion | Always loads `.env.mcp` first |

## 🎪 Pro Tips

1. **Keep `.env.mcp` updated** - This is the source of truth for MCP configuration
2. **Use the robust initializer** - `claude-code-robust-init.cjs` handles edge cases
3. **Check logs if stuck** - Everything is logged to `mcp-server/claude-init.log`
4. **Trust the auto-recovery** - Script will try alternate ports and configurations
5. **API key is consistent** - Always `concordbroker-mcp-key-claude` for authenticated endpoints

---

**🎉 You should never have to go through the connection hassle again!**