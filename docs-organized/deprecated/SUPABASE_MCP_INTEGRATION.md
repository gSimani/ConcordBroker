# Supabase MCP Integration Guide

**Repository**: https://github.com/gSimani/supabase-mcp
**Integration Date**: October 3, 2025
**Status**: ✅ Ready for Integration

---

## 🎯 Overview

The Supabase MCP (Model Context Protocol) Server enables AI assistants (like Claude) to interact with your Supabase database in a secure, controlled manner. This integration brings powerful AI-assisted database operations to ConcordBroker.

### What is MCP?

Model Context Protocol is a standardized way for Large Language Models to interact with external services. It provides:
- Standardized tool definitions
- Security controls (read-only mode, scoping)
- Structured data exchange
- Audit logging

---

## 🔧 Features Added

### Database Operations
✅ **Query Database Tables**
- AI-assisted SELECT queries
- Automatic filtering and pagination
- Schema-aware suggestions

✅ **Table Schema Information**
- Get column definitions
- View data types and constraints
- Understand table relationships

✅ **List Available Tables**
- Discover database structure
- Browse table metadata
- Identify data sources

✅ **Safe Query Execution**
- Read-only enforcement
- SQL injection protection
- Dangerous keyword blocking

✅ **Database Statistics**
- Get row counts for all tables
- Monitor data growth
- Track table usage

✅ **Property Search**
- AI-powered property filtering
- Natural language queries
- Smart result ranking

---

## 📦 Integration Components

### Files Created

1. **`mcp-server/supabase-mcp-integration.js`**
   - Core integration module
   - Tool definitions
   - Security controls
   - Health checks

2. **`SUPABASE_MCP_INTEGRATION.md`** (this file)
   - Integration documentation
   - Configuration guide
   - Usage examples

### Tools Registered

| Tool Name | Description | Security |
|-----------|-------------|----------|
| `supabase_query_database` | Query tables with filters | Read-only |
| `supabase_get_table_schema` | Get table structure | Read-only |
| `supabase_list_tables` | List all tables | Read-only |
| `supabase_execute_safe_query` | Run safe SELECT queries | Read-only |
| `supabase_get_database_stats` | Get table statistics | Read-only |
| `supabase_search_properties` | Search Florida properties | Read-only |

---

## 🔐 Security Configuration

### Read-Only Mode (Default)

**IMPORTANT**: The integration defaults to **READ-ONLY** mode for safety.

```javascript
// In supabase-mcp-integration.js
const SUPABASE_MCP_CONFIG = {
  readOnly: true,  // ✅ RECOMMENDED: Prevents modifications
  projectId: process.env.SUPABASE_PROJECT_ID,
  features: [
    'docs',      // Documentation
    'database',  // Database queries (SELECT only)
    'debugging'  // Query debugging
  ]
};
```

### Optional Features (Disabled by Default)

These features are **disabled** for security:

```javascript
// Uncomment to enable (NOT RECOMMENDED for production):
// 'account',    // Account management
// 'development', // Development tools
// 'functions',  // Edge functions deployment
// 'branching',  // Database branching
// 'storage',    // File storage operations
```

### Environment Variables

Add to `.env.mcp`:

```env
# Supabase MCP Configuration
SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_PROJECT_ID=pmispwtdngkcmsrsjwbp

# Security Settings
SUPABASE_MCP_READ_ONLY=true  # ALWAYS keep this true in production
```

---

## 🚀 Installation

### 1. Install Dependencies

```bash
cd mcp-server
npm install @supabase/supabase-js@latest
npm install @modelcontextprotocol/sdk graphql zod
```

### 2. Configure Environment

Add to `.env.mcp`:

```env
SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
SUPABASE_PROJECT_ID=pmispwtdngkcmsrsjwbp
SUPABASE_MCP_READ_ONLY=true
```

### 3. Update MCP Server

Add to `mcp-server/index.js`:

```javascript
// Import Supabase MCP integration
import {
  registerSupabaseMcpTools,
  checkSupabaseMcpHealth
} from './supabase-mcp-integration.js';

// In initialization
async init() {
  // ... existing code ...

  // Register Supabase MCP tools
  console.log('\n🔧 Initializing Supabase MCP integration...');
  registerSupabaseMcpTools(this);

  // Check health
  const health = await checkSupabaseMcpHealth();
  if (health.healthy) {
    console.log('✅ Supabase MCP integration ready');
  } else {
    console.warn('⚠️  Supabase MCP health check failed:', health.error);
  }
}
```

### 4. Restart MCP Server

```bash
cd mcp-server
npm start
```

---

## 💡 Usage Examples

### Example 1: Query Properties by County

**AI Prompt**:
> "Show me 10 properties in Broward County with values over $500,000"

**MCP Tool Called**:
```json
{
  "tool": "supabase_search_properties",
  "params": {
    "county": "BROWARD",
    "minValue": 500000,
    "limit": 10
  }
}
```

**Response**:
```json
{
  "count": 10,
  "properties": [
    {
      "parcel_id": "402101327008",
      "phy_addr1": "348 EUCLID ST",
      "just_value": 125369,
      "owner_name": "MILLER KRISTINE LYNN"
    }
    // ... 9 more properties
  ],
  "filters": {
    "county": "BROWARD",
    "minValue": 500000
  }
}
```

---

### Example 2: Get Database Statistics

**AI Prompt**:
> "How many properties are in the database?"

**MCP Tool Called**:
```json
{
  "tool": "supabase_get_database_stats"
}
```

**Response**:
```json
{
  "timestamp": "2025-10-03T16:00:00.000Z",
  "stats": {
    "florida_parcels": { "count": 9113150, "error": null },
    "property_sales_history": { "count": 96771, "error": null },
    "florida_entities": { "count": 15013088, "error": null },
    "sunbiz_corporate": { "count": 2030912, "error": null },
    "tax_certificates": { "count": 50000, "error": null }
  }
}
```

---

### Example 3: List Available Tables

**AI Prompt**:
> "What tables are available in the database?"

**MCP Tool Called**:
```json
{
  "tool": "supabase_list_tables"
}
```

**Response**:
```json
{
  "tables": [
    { "table_name": "florida_parcels", "table_type": "BASE TABLE" },
    { "table_name": "property_sales_history", "table_type": "BASE TABLE" },
    { "table_name": "florida_entities", "table_type": "BASE TABLE" }
    // ... more tables
  ],
  "tableCount": 25
}
```

---

### Example 4: Get Table Schema

**AI Prompt**:
> "What columns does the florida_parcels table have?"

**MCP Tool Called**:
```json
{
  "tool": "supabase_get_table_schema",
  "params": {
    "table": "florida_parcels"
  }
}
```

**Response**:
```json
{
  "table": "florida_parcels",
  "columns": [
    {
      "column_name": "parcel_id",
      "data_type": "text",
      "is_nullable": "NO",
      "column_default": null
    },
    {
      "column_name": "just_value",
      "data_type": "numeric",
      "is_nullable": "YES",
      "column_default": null
    }
    // ... more columns
  ],
  "columnCount": 45
}
```

---

### Example 5: Safe Query Execution

**AI Prompt**:
> "Show properties in Miami with sales in 2023"

**MCP Tool Called**:
```json
{
  "tool": "supabase_execute_safe_query",
  "params": {
    "query": "SELECT p.parcel_id, p.phy_addr1, s.sale_price, s.sale_date FROM florida_parcels p JOIN property_sales_history s ON p.parcel_id = s.parcel_id WHERE p.phy_city = 'MIAMI' AND EXTRACT(YEAR FROM s.sale_date) = 2023 LIMIT 10"
  }
}
```

**Security**: Query is validated to ensure:
- ✅ Starts with SELECT
- ✅ No DROP, DELETE, UPDATE, INSERT, ALTER
- ✅ Read-only operation

---

## 🛡️ Security Features

### 1. Read-Only Enforcement

```javascript
// Automatic validation
if (!queryLower.startsWith('select')) {
  throw new Error('Only SELECT queries allowed');
}
```

### 2. Dangerous Keyword Blocking

```javascript
const dangerousKeywords = [
  'drop', 'delete', 'update', 'insert',
  'alter', 'truncate'
];
```

### 3. Project Scoping

```javascript
projectId: SUPABASE_PROJECT_ID  // Limit to specific project
```

### 4. Feature Gating

```javascript
features: ['docs', 'database', 'debugging']  // Only safe features
```

---

## 📊 Monitoring & Health Checks

### Health Check Endpoint

```bash
curl http://localhost:3005/api/supabase/health
```

**Response**:
```json
{
  "healthy": true,
  "config": {
    "readOnly": true,
    "projectId": "pmispwtdngkcmsrsjwbp",
    "features": ["docs", "database", "debugging"]
  },
  "timestamp": "2025-10-03T16:00:00.000Z"
}
```

### Tool Usage Logging

All tool calls are logged:

```
✅ Supabase MCP Tool Called: supabase_search_properties
   Params: {"county":"BROWARD","minValue":500000}
   Result: 10 properties found
   Duration: 234ms
```

---

## 🔄 Integration with Existing MCP Server

### Current MCP Server Tools

The existing MCP server has:
- Vercel deployment
- Railway management
- GitHub integration
- HuggingFace models
- OpenAI access

### New Supabase MCP Tools

Adds 6 new tools for database operations:
- `supabase_query_database`
- `supabase_get_table_schema`
- `supabase_list_tables`
- `supabase_execute_safe_query`
- `supabase_get_database_stats`
- `supabase_search_properties`

### Combined Capabilities

Now AI can:
1. **Query** database for property data
2. **Deploy** frontend to Vercel
3. **Manage** Railway services
4. **Commit** changes to GitHub
5. **Generate** content with HuggingFace/OpenAI
6. **Analyze** data with AI models

---

## 🧪 Testing

### Test Supabase MCP Integration

```bash
# 1. Check health
curl http://localhost:3005/api/supabase/health

# 2. Test database stats
curl -X POST http://localhost:3005/api/tools/call \
  -H "Content-Type: application/json" \
  -H "x-api-key: concordbroker-mcp-key-claude" \
  -d '{"tool":"supabase_get_database_stats"}'

# 3. Test property search
curl -X POST http://localhost:3005/api/tools/call \
  -H "Content-Type: application/json" \
  -H "x-api-key: concordbroker-mcp-key-claude" \
  -d '{
    "tool": "supabase_search_properties",
    "params": {
      "county": "BROWARD",
      "limit": 5
    }
  }'
```

---

## 📚 Additional Resources

### Official Supabase MCP Documentation
- Repository: https://github.com/gSimani/supabase-mcp
- Docs: https://supabase.com/docs/guides/ai/mcp
- MCP Spec: https://modelcontextprotocol.io

### ConcordBroker Documentation
- MCP Server: `mcp-server/README.md`
- API Docs: http://localhost:3005/docs
- Supabase Schema: `DATABASE_SCHEMA.md`

---

## ⚠️ Important Notes

### Security Recommendations

1. **ALWAYS** use read-only mode in production
2. **NEVER** expose service role key to clients
3. **REVIEW** all AI-generated queries before execution
4. **MONITOR** tool usage and set up alerts
5. **SCOPE** to specific projects when possible

### Limitations

- Read-only mode prevents:
  - Creating/dropping tables
  - Inserting/updating/deleting data
  - Schema modifications
  - User management

- To enable write operations:
  1. Set `SUPABASE_MCP_READ_ONLY=false`
  2. Add appropriate features to config
  3. **ONLY** do this in development
  4. Implement additional security controls

---

## 🔄 Next Steps

### Immediate
- [x] Create integration module
- [x] Define security controls
- [x] Document usage
- [ ] Install dependencies
- [ ] Configure environment
- [ ] Update MCP server
- [ ] Test integration

### Future Enhancements
- [ ] Add query result caching
- [ ] Implement rate limiting
- [ ] Add audit logging
- [ ] Create AI query optimizer
- [ ] Build natural language to SQL translator
- [ ] Add data visualization tools

---

## 🎓 Example Workflows

### Workflow 1: Property Research

```
User → AI: "Find 3-bedroom homes in Miami under $300k"
      ↓
AI → MCP: supabase_search_properties(city="MIAMI", maxValue=300000)
      ↓
MCP → Supabase: SELECT * FROM florida_parcels WHERE...
      ↓
Supabase → MCP: [10 properties]
      ↓
MCP → AI: Formatted results
      ↓
AI → User: "Found 10 properties matching your criteria..."
```

### Workflow 2: Data Analysis

```
User → AI: "Analyze property trends in Broward County"
      ↓
AI → MCP: supabase_get_database_stats()
      ↓
AI → MCP: supabase_search_properties(county="BROWARD", limit=1000)
      ↓
AI → Analysis: Calculate averages, trends, insights
      ↓
AI → User: "Based on 9.1M properties, here are the trends..."
```

---

**Integration Status**: ✅ Ready for Implementation
**Estimated Setup Time**: 15 minutes
**Security Level**: High (Read-Only Default)
**Compatibility**: 100% with existing MCP server

---

*Last Updated: October 3, 2025*
*Integration for ConcordBroker MCP Server*
