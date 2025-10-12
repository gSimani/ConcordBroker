# MCP Complete Integration Guide for ConcordBroker
## 🎯 Comprehensive Service Integration Architecture

**Last Updated:** October 12, 2025
**MCP Server Version:** 1.0.0
**Status:** Production Ready

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Service Integration Map](#service-integration-map)
4. [API Endpoints](#api-endpoints)
5. [Agent System](#agent-system)
6. [Data Flow](#data-flow)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The ConcordBroker MCP Server is the **central integration hub** that connects:
- 18+ external services
- 6 AI/LLM providers
- 3 deployment platforms
- 9.7M property records
- Real-time data enrichment

### System Ports
- **MCP Server:** Port 3001 (primary) / 3005 (ultimate)
- **Frontend:** Port 5191 (standard dev)
- **Backend API:** Port 8000
- **AI Orchestrator:** Port 8001
- **FastAPI Service:** Port 8002
- **AI Integration:** Port 8003
- **Dashboard:** Port 8004

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP SERVER (Port 3001)                   │
│                  Central Integration Hub                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │Deployment│          │   AI    │          │  Data   │
   │ Stack   │          │ Stack   │          │  Stack  │
   └─────────┘          └─────────┘          └─────────┘
```

---

## Service Integration Map

### 1. 🚀 Deployment Services

#### Vercel (Frontend)
- **URL:** https://www.concordbroker.com
- **Project:** `concord-broker`
- **Team:** `westbocaexecs-projects`
- **API Endpoint:** `/api/vercel/*`
- **Capabilities:**
  - Automatic deployments on git push
  - Preview deployments per PR
  - Edge functions for API routes
  - Analytics and monitoring

#### Railway (Backend)
- **URL:** https://concordbroker.up.railway.app
- **Internal:** concordbroker.railway.internal
- **Project:** `ConcordBroker-Railway`
- **Environment:** `concordbrokerproduction`
- **API Endpoint:** `/api/railway/*`
- **Capabilities:**
  - Auto-scaling containers
  - Database deployments
  - Service orchestration
  - Health monitoring

---

### 2. 🤖 AI/LLM Stack

#### HuggingFace
- **Organization:** Concord Broker
- **MCP Endpoint:** https://huggingface.co/mcp
- **Secondary Model:** Gemma 3 270M
- **API Endpoint:** `/api/huggingface/*`
- **Use Cases:**
  - Property description generation
  - Market analysis summaries
  - Document classification
  - Sentiment analysis

#### OpenAI
- **Purpose:** Agent Lion dynamic generation
- **Models:** GPT-4, GPT-4 Turbo
- **API Endpoint:** `/api/openai/*`
- **Use Cases:**
  - Complex reasoning tasks
  - Code generation
  - Data validation
  - Natural language queries

#### Anthropic Claude
- **Models:**
  - claude-sonnet-4 (balanced)
  - claude-opus-4 (advanced reasoning)
- **API Endpoint:** `/api/anthropic/*`
- **Use Cases:**
  - Advanced code analysis
  - Multi-step reasoning
  - Document understanding
  - Complex data transformations

#### Google AI Studio
- **Purpose:** Codex Concord
- **API Key:** AIzaSyARgCSCBzTgAfa1FiFpTJ8ZewRbdLri7e4
- **API Endpoint:** `/api/google-ai/*`
- **Use Cases:**
  - Specialized property analysis
  - Custom model fine-tuning
  - Multimodal processing

#### LangChain/LangSmith
- **Project:** `concordbroker-agents`
- **Endpoint:** https://api.smith.langchain.com
- **API Endpoint:** `/api/langchain/*`
- **Agents:**
  - Property Analysis Agent
  - Market Research Agent
  - Investment Scoring Agent
  - Data Validation Agent
  - Agent Lion (dynamic)
- **Features:**
  - Agent orchestration
  - Tracing and debugging
  - Performance monitoring
  - Chain optimization

---

### 3. 💾 Data Stack

#### Supabase (Primary Database)
- **URL:** https://pmispwtdngkcmsrsjwbp.supabase.co
- **Project:** `supabaseconcordbroker`
- **Records:** 9,113,150 properties
- **API Endpoint:** `/api/supabase/*`
- **Tables:**
  - `florida_parcels` (9.1M records)
  - `property_sales_history` (96,771 records)
  - `florida_entities` (15M records)
  - `sunbiz_corporate` (2M records)
  - `tax_certificates`
  - `building_permits`

- **Supabase MCP Tools:**
  - `/api/supabase/mcp/query` - Advanced queries
  - `/api/supabase/mcp/schema` - Schema inspection
  - `/api/supabase/mcp/tables` - List all tables
  - `/api/supabase/mcp/stats` - Database stats
  - `/api/supabase/mcp/search` - Property search

#### Redis Cloud (Caching)
- **Host:** redis-19041.c276.us-east-1-2.ec2.cloud.redislabs.com
- **Port:** 19041
- **API Endpoint:** `/api/redis/*`
- **Cache TTLs:**
  - Property data: 3600s (1 hour)
  - Search results: 900s (15 min)
  - Tax deed data: 300s (5 min)
  - Sunbiz data: 86400s (24 hours)
- **Features:**
  - LangChain memory cache
  - API response caching
  - Session management
  - Rate limiting

---

### 4. 🔧 Development Tools

#### GitHub
- **Repository:** https://github.com/gSimani/ConcordBroker
- **Branch:** main
- **API Endpoint:** `/api/github/*`
- **Capabilities:**
  - Commit history
  - Issue tracking
  - PR management
  - Workflow automation
  - Branch management

#### E2B (Code Sandbox)
- **API Key:** e2b_3de7ddd8b0abc47895efa1dae5809510549788fb
- **API Endpoint:** `/api/e2b/*`
- **Capabilities:**
  - Safe code execution
  - Python/JavaScript runtime
  - 60s timeout
  - 2GB memory limit
  - Isolated environment

#### Playwright MCP
- **API Endpoint:** `/api/playwright/*`
- **Browsers:** Chromium, Firefox, WebKit
- **Capabilities:**
  - Browser automation
  - E2E testing
  - Screenshot capture
  - Performance monitoring

---

### 5. 🌐 Infrastructure

#### Firecrawl (Web Scraping)
- **API Key:** fc-35fd492885e4484fbefba01ed3cf4529
- **API Endpoint:** `/api/firecrawl/*`
- **Rate Limit:** 100 req/min
- **Timeout:** 30 seconds
- **Use Cases:**
  - Property data scraping
  - Market research
  - Competitor analysis
  - Document extraction

#### Google Maps
- **API Key:** AIzaSyBZ9ZqsdUi4z3GOD2OqmiIfxIO6v_AC_sQ
- **API Endpoint:** `/api/maps/*`
- **Features:**
  - Geocoding
  - Reverse geocoding
  - Places search
  - Distance matrix
  - Street view

#### Cloudflare (CDN)
- **Purpose:** DDoS protection & CDN
- **API Endpoint:** `/api/cloudflare/*`
- **Features:**
  - Edge caching
  - DDoS mitigation
  - SSL/TLS
  - Analytics

---

### 6. 📊 Monitoring & Memory

#### Memvid (Memory System)
- **Purpose:** Persistent memory for agents
- **Max Size:** 10,000 items
- **API Endpoint:** `/api/memvid/*`
- **Features:**
  - Context persistence
  - Cross-session memory
  - Agent state management

#### RAG/Vector Database
- **Model:** text-embedding-3-small
- **Dimensions:** 1536
- **API Endpoint:** `/api/rag/*`
- **Use Cases:**
  - Document retrieval
  - Semantic search
  - Knowledge base queries

#### Sentry (Error Tracking)
- **API Endpoint:** `/api/sentry/*`
- **Features:**
  - Real-time error monitoring
  - Stack trace analysis
  - Performance tracking

#### CodeCo (Code Quality)
- **API Endpoint:** `/api/codeco/*`
- **Features:**
  - Code quality metrics
  - Security scanning
  - Best practice enforcement

---

## API Endpoints

### Authentication
All API endpoints require authentication:
```
Header: x-api-key: concordbroker-mcp-key-claude
```

### Complete Endpoint List

#### Deployment
- `POST /api/vercel/deploy` - Deploy to Vercel
- `POST /api/railway/deploy` - Deploy to Railway
- `POST /api/deploy-all` - Deploy to all platforms

#### Database
- `GET /api/supabase/:table` - Get table data
- `POST /api/supabase/:table` - Insert data
- `PATCH /api/supabase/:table/:id` - Update data
- `DELETE /api/supabase/:table/:id` - Delete data
- `POST /api/supabase/query` - Custom SQL query

#### Supabase MCP
- `GET /supabase-mcp/health` - Health check (no auth)
- `POST /api/supabase/mcp/query` - Query database
- `POST /api/supabase/mcp/schema` - Get schema
- `POST /api/supabase/mcp/tables` - List tables
- `POST /api/supabase/mcp/execute` - Execute safe query
- `POST /api/supabase/mcp/stats` - Database statistics
- `POST /api/supabase/mcp/search` - Property search

#### AI/LLM
- `POST /api/huggingface/inference` - Run HF model
- `POST /api/openai/complete` - OpenAI completion
- `POST /api/anthropic/complete` - Claude completion
- `POST /api/google-ai/analyze` - Google AI analysis
- `POST /api/langchain/chat` - LangChain chat
- `POST /api/langchain/agent` - Run specific agent

#### Utilities
- `POST /api/firecrawl/scrape` - Scrape URL
- `POST /api/maps/geocode` - Geocode address
- `POST /api/e2b/execute` - Execute code
- `POST /api/playwright/navigate` - Automate browser

#### System
- `GET /health` - System health (no auth)
- `GET /docs` - API documentation (no auth)
- `GET /` - Server info (no auth)

---

## Agent System

### Architecture

```
┌────────────────────────────────────────┐
│      LangChain Agent Orchestrator      │
└────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌──▼───┐ ┌──▼────┐
│Property│ │Market│ │Invest │
│Analysis│ │Research│ │Scoring│
└───────┘ └──────┘ └───────┘
```

### Agent Lion (Dynamic Agent Generator)

**Purpose:** Creates specialized agents on-demand

**How it works:**
1. User requests specific task
2. Agent Lion analyzes requirements
3. Generates custom agent with specific tools
4. Agent executes task
5. Results returned to user

**Example:**
```javascript
POST /api/langchain/agent-lion
{
  "task": "Analyze investment potential for properties in Broward County",
  "context": {
    "county": "BROWARD",
    "budget": 500000,
    "goals": ["appreciation", "cash-flow"]
  }
}
```

### Pre-built Agents

#### 1. Property Analysis Agent
- **Purpose:** Deep dive property analysis
- **Tools:** Supabase, MCP, Maps, Redis
- **Outputs:** Comprehensive property report

#### 2. Market Research Agent
- **Purpose:** Market trends and comparables
- **Tools:** Supabase, Firecrawl, OpenAI
- **Outputs:** Market analysis report

#### 3. Investment Scoring Agent
- **Purpose:** Calculate ROI and investment metrics
- **Tools:** Supabase, Claude, Calculator
- **Outputs:** Investment score (0-100)

#### 4. Data Validation Agent
- **Purpose:** Ensure data quality
- **Tools:** Supabase, MCP, Schema validation
- **Outputs:** Data quality report

---

## Data Flow

### Property Data Enrichment Pipeline

```
1. Base Data (NAL)
   ├─> florida_parcels (12 fields)

2. Assessment Data (NAV)
   ├─> just_value, assessed_value, taxable_value
   ├─> land_value, building_value

3. Sales Data (SDF)
   ├─> property_sales_history
   ├─> sale_date, sale_price, sale_qualification

4. Property Characteristics (TPP)
   ├─> year_built, total_living_area
   ├─> bedrooms, bathrooms, stories

5. Business Entities (Sunbiz)
   ├─> sunbiz_corporate
   ├─> entity_name, filing_number, status

6. Permits & Foreclosures
   ├─> building_permits
   ├─> foreclosure_data

7. Tax Certificates
   ├─> tax_certificates
   ├─> certificate_number, face_amount
```

### Real-time Data Flow

```
User Request
    ↓
Frontend (5191)
    ↓
MCP Server (3001) ← [Auth, Rate Limit, CORS]
    ↓
┌───┴────┐
│ Cache? │ → Yes → Return from Redis
└───┬────┘
    No
    ↓
Supabase MCP
    ↓
PostgreSQL Database
    ↓
Redis Cache (store)
    ↓
Return to User
```

---

## Configuration

### Environment Variables (.env.mcp)

**Required Variables:**
- `SUPABASE_URL` - Database URL
- `SUPABASE_SERVICE_ROLE_KEY` - Admin key
- `OPENAI_API_KEY` - OpenAI access
- `LANGCHAIN_API_KEY` - LangChain access
- `MCP_API_KEY` - MCP authentication

**Optional but Recommended:**
- `ANTHROPIC_API_KEY` - Claude access
- `GOOGLE_AI_STUDIO_API_KEY` - Google AI
- `FIRECRAWL_API_KEY` - Web scraping
- `E2B_API_KEY` - Code sandbox
- `REDIS_URL` - Caching

### MCP Server Configuration (mcp-config.json)

**Key Sections:**
1. **Services** - External service configs
2. **AI** - LLM provider configs
3. **Security** - Auth and CORS
4. **Integrations** - Enabled services
5. **DataEnrichment** - Data source configs

---

## Testing

### Health Checks

```bash
# MCP Server
curl http://localhost:3001/health

# Supabase MCP
curl http://localhost:3001/supabase-mcp/health

# Frontend
curl http://localhost:5191
```

### API Testing

```bash
# Authenticated request
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  http://localhost:3001/api/supabase/mcp/stats

# Property search
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  -X POST http://localhost:3001/api/supabase/mcp/search \
  -d '{"county":"BROWARD","limit":10}'
```

### Agent Testing

```bash
# Run Property Analysis Agent
curl -H "x-api-key: concordbroker-mcp-key-claude" \
  -X POST http://localhost:3001/api/langchain/agent \
  -d '{
    "agent":"propertyAnalysis",
    "parcel_id":"484104011450"
  }'
```

---

## Troubleshooting

### Common Issues

#### 1. MCP Server Won't Start
**Symptom:** Server fails to start or crashes immediately

**Solutions:**
- Check `.env.mcp` has all required keys
- Verify port 3001 is available
- Check logs: `cat mcp-server/claude-init.log`
- Try: `node mcp-server/server.js`

#### 2. API Authentication Errors
**Symptom:** 401 Unauthorized responses

**Solutions:**
- Verify API key: `concordbroker-mcp-key-claude`
- Check header: `x-api-key`
- Ensure key in `.env.mcp`: `MCP_API_KEY`

#### 3. Supabase MCP Health Check Failed
**Symptom:** `relation "public.florida_parcels" does not exist`

**Solutions:**
- Check table exists in Supabase dashboard
- Verify SERVICE_ROLE_KEY permissions
- Check database connection string

#### 4. Agent Not Responding
**Symptom:** LangChain agent timeout or no response

**Solutions:**
- Check `LANGCHAIN_API_KEY` is valid
- Verify `DISABLE_LANGCHAIN=false` (or not set)
- Check LangSmith project exists
- Review agent configuration in mcp-config.json

#### 5. Rate Limiting
**Symptom:** 429 Too Many Requests

**Solutions:**
- Adjust `RATE_LIMIT_MAX` in `.env.mcp`
- Implement exponential backoff
- Use Redis caching to reduce API calls

---

## Integration Checklist

### ✅ Fully Integrated
- [x] Vercel (Frontend deployment)
- [x] Railway (Backend deployment)
- [x] Supabase (Database)
- [x] Supabase MCP (Advanced database tools)
- [x] OpenAI (GPT-4)
- [x] Anthropic Claude (Sonnet 4, Opus 4)
- [x] Google AI Studio (Codex Concord)
- [x] LangChain/LangSmith (Agent orchestration)
- [x] HuggingFace (Gemma 3 270M)
- [x] GitHub (Version control)
- [x] Redis Cloud (Caching)
- [x] Google Maps (Geocoding)
- [x] Firecrawl (Web scraping)
- [x] E2B (Code sandbox)
- [x] Playwright (Browser automation)
- [x] Memvid (Memory system)
- [x] RAG/Vector DB (Document retrieval)

### ⚠️ Pending Configuration
- [ ] Sentry (Error tracking) - Need DSN
- [ ] CodeCo (Code quality) - Need API key
- [ ] Cloudflare (CDN) - Need API token and Zone ID

### 📊 Data Sources Status
- [x] NAL (Name, Address, Legal) - 9.1M records loaded
- [ ] NAV (Assessment values) - Ready to import
- [ ] SDF (Sales data) - Table created, import pending
- [ ] TPP (Property characteristics) - Ready to import
- [ ] Sunbiz (Business entities) - 2M records loaded
- [ ] Permits - Integration pending
- [ ] Tax Certificates - Integration pending

---

## Next Steps

### Immediate Actions
1. **Enable LangChain** - Set `DISABLE_LANGCHAIN=false`
2. **Import NAV Data** - Add property values
3. **Import SDF Data** - Add sales history
4. **Configure Sentry** - Add error tracking
5. **Test All Agents** - Verify agent responses

### Short-term (1-2 weeks)
1. Import TPP property characteristics
2. Add building permits integration
3. Add tax certificate integration
4. Implement advanced caching strategies
5. Create custom Agent Lion templates

### Long-term (1-3 months)
1. Machine learning model integration
2. Predictive analytics for property values
3. Automated market reports
4. Custom report generation
5. Multi-county expansion

---

## Support & Resources

### Documentation
- MCP Server Docs: `/docs` endpoint
- LangChain Docs: https://docs.langchain.com
- Supabase Docs: https://supabase.com/docs
- OpenAI Docs: https://platform.openai.com/docs

### Monitoring
- LangSmith Dashboard: https://smith.langchain.com
- Supabase Dashboard: https://pmispwtdngkcmsrsjwbp.supabase.co
- Vercel Dashboard: https://vercel.com/westbocaexecs-projects/concord-broker
- Railway Dashboard: https://railway.app

### Contact
- Website: https://www.concordbroker.com
- Repository: https://github.com/gSimani/ConcordBroker

---

**Last Updated:** October 12, 2025
**Version:** 1.0.0
**Status:** ✅ Production Ready
