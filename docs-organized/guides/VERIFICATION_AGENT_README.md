# 🧪 Verification Agent - Automatic Code Verification System

## Overview

The **Verification Agent** is a permanent, always-active sub-agent that automatically checks and verifies all work after changes are made to the ConcordBroker project. It provides real-time feedback on code quality, test results, and potential issues.

## Features

✅ **Continuous File Watching** - Monitors all project files for changes
✅ **Automatic Test Selection** - Intelligently runs relevant tests based on changed files
✅ **Real-time Verification** - Provides immediate feedback on code changes
✅ **Intelligent Routing** - Routes different file types to appropriate verification steps
✅ **Self-healing** - Auto-restarts on crashes
✅ **Zero Configuration** - Works out of the box
✅ **Comprehensive Logging** - Detailed history and status tracking

## Quick Start

### Starting the Agent

The verification agent starts automatically when you run:

```bash
npm run claude:start
# or
node claude-code-ultimate-init.cjs
```

To start it manually:

```bash
npm run verify:agent:start
```

### Checking Status

```bash
# View current status
npm run verify:agent:status

# View last verification result
npm run verify:last

# View verification history
npm run verify:history

# View current queue
npm run verify:queue
```

### Accessing the Dashboard

The agent provides a real-time HTTP interface:

- **Health Check**: http://localhost:3009/health
- **Current Status**: http://localhost:3009/status
- **Verification History**: http://localhost:3009/history
- **Queue Status**: http://localhost:3009/queue

## How It Works

### File Watching

The agent monitors these directories:
- `apps/web/src/` - Frontend React/TypeScript files
- `apps/api/` - Backend Python files
- `mcp-server/` - MCP server files

### Verification Flow

1. **File Change Detected** → Agent detects change via file watcher
2. **Debouncing** → Waits 2 seconds to collect related changes
3. **Queue** → Adds file to verification queue
4. **Analysis** → Determines appropriate verification steps
5. **Execute** → Runs verification steps sequentially
6. **Report** → Saves results and updates status

### Verification Steps by File Type

#### TypeScript/React Files (.ts, .tsx)
1. ✅ TypeScript compilation check
2. ✅ ESLint validation
3. ✅ Component-specific Playwright tests (if available)

#### Critical Components
Special handling for important files:

**PropertySearch.tsx**:
- TypeScript check
- ESLint
- Property search E2E tests
- Filter functionality audit

**MiniPropertyCard.tsx**:
- TypeScript check
- ESLint
- Comprehensive test suite

**AdvancedPropertyFilters.tsx**:
- TypeScript check
- ESLint
- Filter audit tests

#### Python Files (.py)
1. ✅ Python syntax validation
2. ✅ API health check (if API is running)
3. ✅ Integration tests (conditional)

#### Configuration Files (.json, .yml, .yaml)
1. ✅ JSON/YAML syntax validation
2. ✅ Service restart warnings (if needed)

#### MCP Server Files
1. ✅ JavaScript syntax check
2. ✅ MCP server health check

## Verification Results

### Result Structure

Each verification produces a detailed result:

```json
{
  "file": "apps/web/src/pages/properties/PropertySearch.tsx",
  "timestamp": "2025-10-20T22:30:00.000Z",
  "duration": 15234,
  "steps": [
    {
      "name": "TypeScript Check",
      "passed": true,
      "duration": 8123,
      "output": "✅ No errors found"
    },
    {
      "name": "ESLint",
      "passed": true,
      "duration": 4211,
      "output": "✅ No issues found"
    },
    {
      "name": "Property Search Tests",
      "passed": true,
      "duration": 2900,
      "output": "✅ All tests passed"
    }
  ],
  "passed": true,
  "critical_failures": []
}
```

### Status Indicators

- **✅ PASSED** - All verification steps succeeded
- **❌ FAILED** - One or more critical steps failed
- **⚠️ WARNING** - Non-critical steps failed
- **⏭️ SKIPPED** - No verification needed for this file type

## Configuration

### Agent Configuration

Located in `.claude/agents/verification-agent.json`:

```json
{
  "name": "verification-agent",
  "autoStart": true,
  "port": 3009,
  "debounceDelay": 2000,
  "verificationTimeout": 120000
}
```

### Workflow Configuration

Located in `.claude/workflows/auto-verify.json`:

Defines verification workflows for different file types and special cases.

### Hook Configuration

Located in `.claude/hooks/post-change.cjs`:

Optional hook that can notify the agent about changes (if not using file watching).

## Commands Reference

### Agent Control
```bash
# Start the agent
npm run verify:agent:start

# View status
npm run verify:agent:status

# Restart the agent
npm run verify:agent:restart
```

### Viewing Results
```bash
# View last verification
npm run verify:last

# View full history
npm run verify:history

# View current queue
npm run verify:queue
```

### Manual Verification
```bash
# Run all verifications manually
npm run verify:all

# Type checking only
npm run verify:types

# Linting only
npm run verify:lint

# Tests only
npm run verify:tests
```

## Logs and Status

### Log Files

All logs are stored in the `logs/` directory:

- **verification-status.json** - Current agent status
- **verification-history.jsonl** - Complete verification history (JSON Lines format)
- **ultimate-init.log** - Initialization logs

### Status File Format

```json
{
  "agentStarted": "2025-10-20T22:29:42.502Z",
  "status": "active",
  "port": 3009,
  "verificationCount": 42,
  "lastVerification": { /* result object */ },
  "currentlyVerifying": false,
  "history": [ /* last 10 results */ ]
}
```

## Troubleshooting

### Agent Not Starting

1. Check if port 3009 is available:
   ```bash
   netstat -ano | findstr :3009
   ```

2. View initialization logs:
   ```bash
   type logs\ultimate-init.log
   ```

3. Try manual start:
   ```bash
   node verification-agent.cjs
   ```

### No Verifications Running

1. Check agent health:
   ```bash
   curl http://localhost:3009/health
   ```

2. Verify file watchers are active:
   ```bash
   curl http://localhost:3009/status
   ```

3. Check the queue:
   ```bash
   npm run verify:queue
   ```

### Verification Failing

1. View the last verification result:
   ```bash
   npm run verify:last
   ```

2. Run manual verification:
   ```bash
   npm run verify:all
   ```

3. Check the detailed history:
   ```bash
   npm run verify:history
   ```

## Integration

### With Claude Code

The verification agent integrates seamlessly with Claude Code:

1. **Auto-start**: Starts automatically via `claude-code-ultimate-init.cjs`
2. **Status Display**: Shows in the success message after initialization
3. **Continuous Operation**: Runs throughout your entire coding session

### With MCP Server

The agent works alongside the MCP server:

- **MCP Server Port**: 3005
- **Verification Agent Port**: 3009
- **Independent Operation**: Can work even if MCP server is down

### With CI/CD

Future integration planned:
- Pre-commit hooks
- GitHub Actions
- Deployment gates

## Best Practices

1. **Let It Run**: Keep the agent running throughout your session
2. **Check Results**: Review verification results after making changes
3. **Fix Issues Promptly**: Address critical failures immediately
4. **Monitor History**: Review the history periodically for patterns
5. **Trust the Agent**: The agent catches issues early - listen to it!

## Advanced Usage

### Custom Verification Steps

To add custom verification for specific files, edit:
`.claude/agents/verification-agent.json`

Add to the `specialCases` section:

```json
{
  "specialCases": {
    "YourComponent.tsx": {
      "additionalTests": [
        "tests/your-component-test.spec.ts"
      ],
      "critical": true,
      "description": "Your component description"
    }
  }
}
```

### Disabling for Specific Files

Add patterns to `ignorePatterns` in the agent configuration.

### Adjusting Timeouts

Modify `verificationTimeout` in the configuration (in milliseconds):

```json
{
  "verificationTimeout": 180000  // 3 minutes
}
```

## Performance

The agent is designed to be lightweight:

- **Memory Usage**: ~50-100 MB
- **CPU Usage**: Minimal when idle, spikes during verification
- **Disk Usage**: Logs rotate automatically
- **Network**: Only local HTTP requests

## Security

- **Local Only**: Runs only on localhost
- **No External Calls**: All verification is local
- **No Data Sent**: Results stay on your machine
- **Read-Only**: Agent only reads files, never modifies

## Support

For issues or questions:

1. Check the logs in `logs/` directory
2. Review this README
3. Examine the agent configuration files
4. Check the main project `CLAUDE.md` for more context

## Version

Current Version: **1.0.0**
Last Updated: **October 20, 2025**

---

**Remember**: The verification agent is your coding companion. It's here to catch issues early and give you confidence in your changes. Trust it, and let it help you build better code! 🚀
