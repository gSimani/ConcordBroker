# Claude Code Configuration

This project is configured to automatically start the MCP Server when Claude Code begins a new session with **robust error handling and failsafe mechanisms**.

## Automatic Services Connection (IMPROVED)

When you start Claude Code in this project, the following services are automatically connected:

### Active Services:
- ✅ **Vercel** - Frontend deployment (https://www.concordbroker.com)
- ✅ **Railway** - Backend API services
- ✅ **Supabase** - PostgreSQL database with Redis Cloud caching
- ✅ **HuggingFace** - AI/LLM inference
- ✅ **OpenAI** - GPT-4 for Agent Lion
- ✅ **LangChain/LangSmith** - Agent orchestration and tracing (auto-disabled if problematic)
- ✅ **GitHub** - Version control

### MCP Server Features (ULTIMATE):
- **Ultimate Auto-start**: `claude-code-ultimate-init.cjs` with integrated monitoring
- **Dedicated Monitoring Agent**: Continuous connection monitoring and conflict prevention
- **Intelligent Port Management**: Primary port 3005 with auto-fallback to 3006-3008
- **Real-time Conflict Detection**: Automatically detects and resolves port conflicts
- **Self-healing Connections**: Auto-recovery when services go down
- **Advanced Cleanup**: Terminates conflicting processes before startup
- **Continuous Health Monitoring**: Checks all services every 15 seconds
- **WebSocket support**: Real-time updates with proper authentication
- **API endpoints**: RESTful API at `http://localhost:3005`
- **Emergency Recovery**: Multi-level fallback and recovery mechanisms
- **Session persistence**: Maintains connections throughout all Claude Code sessions

## Quick Commands

### Check MCP Server Status
```bash
curl http://localhost:3005/health
```

### Test API Access (with proper authentication)
```bash
curl -H "x-api-key: concordbroker-mcp-key-claude" http://localhost:3005/api/supabase/User
```

### Manual Start Options
```bash
# ULTIMATE: Complete system with monitoring (RECOMMENDED)
node claude-code-ultimate-init.cjs

# Robust: Initialization without persistent monitoring
node claude-code-robust-init.cjs

# Monitor Only: Start just the monitoring agent
node connection-monitor-agent.cjs

# Basic: Direct server start
cd mcp-server && npm start

# Emergency: Start with LangChain disabled
cd mcp-server && DISABLE_LANGCHAIN=true npm start
```

### Check Monitoring Status
```bash
# View monitoring agent status
type logs\monitor-status.json

# View monitoring logs
type logs\connection-monitor.log

# View ultimate system status
type logs\ultimate-status.json
```

### Force Reset (if stuck)
```bash
# Nuclear option: Kill everything and restart with ultimate system
taskkill /F /IM node.exe
timeout 3
node claude-code-ultimate-init.cjs

# Alternative: Just restart monitoring
node connection-monitor-agent.cjs
```

### View Logs
```bash
cat mcp-server/claude-init.log
```

### Smoke Test

Run a quick end-to-end smoke test (MCP + LangChain + RAG + chat):
```bash
npm run smoke
# or within MCP folder
cd mcp-server && npm run smoke
```

WebSocket connections now enforce API key validation during handshake. Include `x-api-key` header matching `MCP_API_KEY`.

### Escalation Queue

- When a chat response is marked `escalated: true`, the API appends a masked event to `logs/escalations.jsonl` (local sink).
- Each line contains timestamp, session id, agent name, confidence, strict flag, and masked message/response.
- This enables human triage and optional ingestion into a ticketing system.

### Request Correlation

- MCP and LangChain API emit JSON logs with a request ID. MCP propagates `x-request-id` to LangChain calls.
- When building new tools or services, pass `x-request-id` along so logs across systems correlate cleanly.

## API Access

All API endpoints are available at `http://localhost:3001/api/*`

Include the API key in headers:
```
x-api-key: concordbroker-mcp-key
```

## Service Endpoints

### Database Operations
- Query: `POST /api/supabase/query`
- Get data: `GET /api/supabase/:table`
- Insert: `POST /api/supabase/:table`
- Update: `PATCH /api/supabase/:table/:id`
- Delete: `DELETE /api/supabase/:table/:id`

### Deployment
- Vercel: `POST /api/vercel/deploy`
- Railway: `POST /api/railway/deploy`
- Both: `POST /api/deploy-all`

### AI/LLM
- HuggingFace: `POST /api/huggingface/inference`
- OpenAI: `POST /api/openai/complete`

### GitHub
- Commits: `GET /api/github/commits`
- Issues: `POST /api/github/issue`
- PRs: `POST /api/github/pr`

## Troubleshooting (ENHANCED)

If services don't connect automatically:

### Common Issues & Solutions:

1. **Port Conflicts**:
   - Check if port 3005 is in use: `netstat -ano | findstr :3005`
   - The robust initializer will auto-switch to ports 3006, 3007, 3008 if needed

2. **Environment Variables**:
   - Verify `.env.mcp` exists and has all required keys
   - Check API keys are valid and not expired

3. **Process Conflicts**:
   - Kill conflicting processes: `taskkill /F /IM node.exe`
   - Use robust initializer: `node claude-code-robust-init.cjs`

4. **API Authentication**:
   - Use correct API key: `concordbroker-mcp-key-claude`
   - Include in headers: `x-api-key: concordbroker-mcp-key-claude`

### Health Checks:
```bash
# Basic health check
curl http://localhost:3005/health

# Authenticated health check
curl -H "x-api-key: concordbroker-mcp-key-claude" http://localhost:3005/health

# View detailed logs
cat mcp-server/claude-init.log
```

### Emergency Recovery:
```bash
# Nuclear option: Kill everything and restart
taskkill /F /IM node.exe
timeout 3
node claude-code-robust-init.cjs
```

## Configuration

Settings are stored in:
- `.claude-code/config.json` - Claude Code configuration
- `mcp-server/mcp-config.json` - Service configuration
- `.env.mcp` - Credentials (keep secure!)

## Session Management

- Sessions auto-expire after 1 hour of inactivity
- Server automatically restarts on new session
- WebSocket reconnects automatically
- All services maintain persistent connections

## Security Notes

- API keys are stored in `.env.mcp` (never commit!)
- All endpoints require authentication
- CORS configured for web access
- Service keys never exposed in responses

PII Guardrail: Outgoing chat responses from LangChain API apply lightweight PII masking (emails/phone numbers) by default. Avoid including sensitive data in prompts unless explicitly required and consented.

Confidence Threshold: The chat API estimates a confidence score in [0,1] using the secondary LLM. Set `CONFIDENCE_THRESHOLD` (default `0.7`) in the environment to mark responses below the threshold as `escalated: true` in the metadata. This does not block the response by default; adjust behavior as needed.

---

*This configuration ensures all services are ready whenever you work with Claude Code.*

## Secrets & API Access

- Required secrets for full functionality:
  - `VERCEL_API_TOKEN`, `VERCEL_PROJECT_ID`
  - `RAILWAY_API_TOKEN`, `RAILWAY_PROJECT_ID`
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `OPENAI_API_KEY`
  - `LANGCHAIN_API_KEY`, `LANGSMITH_API_KEY` (for agent orchestration and tracing via LangChain/LangSmith)
  - `HUGGINGFACE_API_TOKEN` (optional local/secondary LLM)
  - `GITHUB_API_TOKEN`
  - Frontend: `VITE_GOOGLE_MAPS_API_KEY`

- Where to place them:
  - MCP/server: put backend/service keys in `/.env.mcp` (use `mcp-server/.env.example` as a guide).
  - LangChain/agents: export `LANGCHAIN_API_KEY`, `LANGSMITH_API_KEY` and `OPENAI_API_KEY` in your shell or add to root `/.env`.
  - Frontend: set `apps/web/.env` with `VITE_GOOGLE_MAPS_API_KEY=...`.

- How Claude Code picks them up:
  - On session start, `claude-code-init.cjs` auto-launches MCP using `/.env.mcp`.
  - LangChain API inherits `LANGCHAIN_API_KEY`, `LANGSMITH_API_KEY` and `OPENAI_API_KEY` from your environment.
  - The web app reads `VITE_*` vars at build/dev time from `apps/web/.env`.

- Quick setup steps:
  - Copy `mcp-server/.env.example` to `/.env.mcp` and fill values.
  - Create `apps/web/.env` with `VITE_GOOGLE_MAPS_API_KEY=your_key`.
  - Export in shell (or add to root `/.env`):
    - `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, `LANGSMITH_API_KEY`, optional `HUGGINGFACE_API_TOKEN`.
  - Start Claude Code; it will auto-start MCP and verify health.

- Validation:
  - MCP: `curl http://localhost:3001/health`
  - LangChain: `curl http://localhost:8003/health`
  - Frontend map: ensure `VITE_GOOGLE_MAPS_API_KEY` renders maps in UI.

### Confidence & Escalation Controls

- `CONFIDENCE_THRESHOLD` (default `0.7`): chat responses below this score are marked `escalated: true` in metadata.
- `STRICT_ESCALATION` (default `false`): when `true`, any response below the threshold is replaced with a standard human‑review message instead of the model output.

CI note: a basic secret scan + guardrail check runs on PRs via `.github/workflows/security.yml`.

## Explanations Without Chain-of-Thought

- You can request a concise rationale summary with chat by sending `explain: true` in the request body to `/chat`.
- The rationale is a short, high-level explanation (2–3 bullets) and explicitly avoids revealing chain-of-thought.
- Responses also include `metadata.confidence` [0,1] and `metadata.escalated` (true if below `CONFIDENCE_THRESHOLD`, default 0.7).

## Agent Design Rules (Based on OpenAI Guide)

### Core Principles
1. **Start Simple**: Always begin with single-agent systems before multi-agent architectures
2. **Tool Atomicity**: Each tool should do ONE thing well with comprehensive error handling
3. **Guardrails First**: Implement safety measures BEFORE production deployment
4. **Human Escalation**: Escalate to humans when confidence < 70% or for high-risk operations

### ConcordBroker Agent Standards

#### Data Operations
- Property queries MUST include county filter
- Tax deed queries default to 'upcoming' status
- Always validate parcel ID format before database operations
- Cache frequently accessed data for performance

#### Workflow Requirements
- Property analysis requires minimum 3 data sources
- Investment recommendations need ROI calculation
- Market comparisons use 6-month window default
- Alert users for properties with >20% value change

#### Safety Guardrails
- NEVER expose PII without explicit consent
- ALWAYS validate inputs before database operations
- Implement rate limiting on external APIs
- Log all high-risk operations for audit
- Require human approval for transactions >$100,000

### Agent Orchestration Patterns
1. **Single Agent**: Use for <15 distinct tools, linear workflows
2. **Manager Pattern**: Use when coordinating >3 specialized domains
3. **Handoff Pattern**: Use for workflows with distinct phases

### Testing Requirements
Every agent must have:
- Happy path tests
- Edge case coverage
- Error handling validation
- Guardrail effectiveness tests
- Performance benchmarks

### Monitoring Standards
- Track agent success rates (target: >85%)
- Monitor tool usage patterns
- Review guardrail violations weekly
- Update instructions based on failure patterns

### Implementation Checklist
- [ ] Define clear success/failure criteria
- [ ] Start with most capable model (optimize later)
- [ ] Create atomic, reusable tools
- [ ] Implement layered guardrails
- [ ] Add comprehensive error handling
- [ ] Set up monitoring and logging
- [ ] Test with real data
 - [ ] Document workflow and decisions

## MCP Security Notes

- All `/api/*` endpoints now require an API key in `x-api-key` matching `MCP_API_KEY` (default: `concordbroker-mcp-key`).
- Basic IP rate limiting is enabled. Configure via `RATE_LIMIT_WINDOW_MS` and `RATE_LIMIT_MAX`.
- CORS in production is restricted to `CORS_ORIGINS` (comma-separated); otherwise requests are blocked.
- Direct Supabase SQL execution is disabled by default; set `SUPABASE_ENABLE_SQL=true` only if using a vetted RPC.

## Supabase Usage Rules

- Do not introduce or rely on generic `execute_sql` RPCs for raw SQL. Prefer:
  - PostgREST table endpoints with filters for standard CRUD.
  - Vetted RPCs with parameter validation, proper RLS, and limited scope for complex operations.
- If you must run SQL (e.g., one-time schema deploy), set `SUPABASE_ENABLE_SQL=true` locally and document the action. Avoid leaving this enabled in production.
- Never commit credentials or full connection strings. Use env vars only.

Workers note: any worker that needs to create tables (e.g., permits) will skip SQL execution unless `SUPABASE_ENABLE_SQL=true`. Provision schemas via Supabase dashboard or a vetted migration pipeline for production.

## Completion Verification (Mandatory)

- Everything completed must be verified 100% before considered done. Use the verification flow:
  - Run static verification: `npm run verify`.
  - Ensure CI jobs pass (secrets scan, guardrail tests, linting).
  - For integrated changes, run the smoke test: `npm run smoke`.
  - Confirm MCP health: `curl http://localhost:3001/health` and LangChain: `curl http://localhost:8003/health`.
  - If changes involve WebSocket or auth, validate `x-api-key` is enforced on both REST and WS.
  - If changes involve Supabase, confirm no new raw `execute_sql` usage was introduced and RLS/parameterized RPCs are used.

- Only mark tasks complete when all checks above pass with 0 failures. Warnings should be triaged or documented.

## Property Appraiser Data System Rules

### Data Location and Structure
- Property appraiser data is in `TEMP\DATABASE PROPERTY APP\{COUNTY}\{TYPE}\*.csv`
- Types: NAL (names/addresses), NAP (characteristics), NAV (values), SDF (sales)  
- 67 Florida counties with ~9.7M total properties
- Data source: https://floridarevenue.com/property/dataportal/Pages/default.aspx

### Column Mapping (NAL → florida_parcels)
CRITICAL: Use exact mappings to avoid errors:
- `LND_SQFOOT` → `land_sqft` (NOT land_square_footage)
- `PHY_ADDR1/PHY_ADDR2` → `phy_addr1/phy_addr2` (NOT property_address)
- `OWN_ADDR1/OWN_ADDR2` → `owner_addr1/owner_addr2` (NOT owner_address)
- `OWN_STATE` → `owner_state` (truncate to 2 chars - "FLORIDA" → "FL")
- `JV` → `just_value` (NOT total_value)
- `sale_date` → Build from SALE_YR1/SALE_MO1 as YYYY-MM-01T00:00:00 or NULL (never empty string)

### Upload Process Requirements
1. **Pre-upload SQL** (run in order):
   - CREATE_INDEXES.sql - Creates unique index on (parcel_id, county, year)
   - APPLY_TIMEOUTS_NOW.sql - Disables timeouts for all roles

2. **Upload Configuration**:
   - Use SERVICE_ROLE_KEY for bulk operations
   - Batch size: 1000 records
   - Parallel workers: 4 threads
   - Headers: `Prefer: return=minimal,resolution=merge-duplicates,count=none`
   - Upsert on conflict: `(parcel_id, county, year)`

3. **Post-upload SQL**:
   - REVERT_TIMEOUTS_AFTER.sql - Restores timeout settings

### Error Handling Patterns
| Error Code | Issue | Solution |
|------------|-------|----------|
| 57014 | Statement timeout | Apply timeout removal SQL before upload |
| 22001 | Value too long | Truncate fields (e.g., owner_state to 2 chars) |
| PGRST204 | Column not found | Check exact column mapping above |
| 429 | Rate limiting | Use exponential backoff: delay = 2^attempt + random(0,1) |

### Data Validation Rules
- **Required**: parcel_id (non-empty), county (uppercase), year (integer 2025)
- **Calculate**: building_value = just_value - land_value (when both exist)
- **Clean**: NaN → NULL for numeric, empty string for text (except timestamps)
- **Timestamps**: Use NULL not empty string for sale_date
- **State codes**: Always 2 characters (FL not FLORIDA)

### Performance Expectations
- Single thread: ~500-1000 records/second
- 4 parallel workers: ~2000-4000 records/second  
- Full dataset (9.7M): 1.5-3 hours
- Memory usage: 2-4 GB

### Monitoring Agent Requirements
- Check daily at 2 AM EST for updates at Florida Revenue site
- Monitor file changes: NAL, NAP, NAV, SDF for all 67 counties
- Store checksums for change detection
- Alert on: new files, size changes >5%, missing expected files
- Log all download attempts with timestamp, county, file type, status
