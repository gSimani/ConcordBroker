# ConcordBroker MCP Server

Complete service integration hub for ConcordBroker, managing connections to all external services.

## Architecture

### Frontend: Vercel
- Project: concord-broker
- Domain: https://www.concordbroker.com

### Backend: Railway
- Project: ConcordBroker-Railway
- Environment: concordbrokerproduction

### Database: Supabase
- Project: supabaseconcordbroker
- PostgreSQL with real-time capabilities

### AI/LLM Services
- **HuggingFace**: Model inference and secondary LLM (Gemma 3 270M)
- **OpenAI**: Primary LLM for Agent Lion dynamic generation

### Additional Services
- **GitHub**: Version control and CI/CD
- **Sentry & CodeCo**: Error tracking
- **Cloudflare**: CDN and DDoS protection
- **Playwright MCP**: Browser automation
- **Firecrawl**: Web scraping
- **Memvid**: Memory system
- **RAG/Vector DB**: Document retrieval

## Installation

1. Install dependencies:
```bash
cd mcp-server
npm install
```

2. Configure environment variables:
```bash
cp ../.env.mcp.example ../.env.mcp
# Edit ../.env.mcp with your credentials
```

3. Start the server:
```bash
npm start
# Or for development with auto-reload:
npm run dev
```

## API Endpoints

Base URL: `http://localhost:3001`

### Authentication
All API endpoints require an API key in the `x-api-key` header.

### Health Check
- `GET /health` - Service health status (no auth required)
- `GET /docs` - API documentation

### Vercel Operations
- `GET /api/vercel/deployments` - Get recent deployments
- `POST /api/vercel/deploy` - Trigger deployment
- `GET /api/vercel/project` - Get project info
- `GET /api/vercel/domains` - Get domains

### Railway Operations
- `GET /api/railway/status` - Get project status
- `GET /api/railway/environments` - Get environments
- `POST /api/railway/deploy` - Trigger deployment

### Supabase Database
- `POST /api/supabase/query` - Execute SQL query
- `GET /api/supabase/:table` - Get table data
- `POST /api/supabase/:table` - Insert data
- `PATCH /api/supabase/:table/:id` - Update data
- `DELETE /api/supabase/:table/:id` - Delete data

### HuggingFace AI
- `POST /api/huggingface/inference` - Run model inference
- `POST /api/huggingface/text-generation` - Generate text
- `POST /api/huggingface/classification` - Classify text
- `POST /api/huggingface/qa` - Question answering
- `POST /api/huggingface/summarize` - Summarize text

### OpenAI
- `POST /api/openai/complete` - Chat completion
- `POST /api/openai/embedding` - Generate embeddings
- `POST /api/openai/image` - Generate images
- `POST /api/openai/moderate` - Content moderation

### GitHub
- `GET /api/github/commits` - Get commits
- `POST /api/github/issue` - Create issue
- `POST /api/github/pr` - Create pull request
- `GET /api/github/workflows/:id/runs` - Get workflow runs
- `POST /api/github/workflows/:id/trigger` - Trigger workflow
- `GET /api/github/branches` - Get branches
- `POST /api/github/branch` - Create branch

### Unified Operations
- `POST /api/deploy-all` - Deploy to all services
- `GET /api/status-all` - Get status of all services

## WebSocket Support

Connect to `ws://localhost:3001` for real-time updates.

### Message Types
- `subscribe` - Subscribe to service updates
- `health` - Get health status
- `ping` - Ping server

### Events
- `health_update` - Periodic health status updates (every 30s)
- `connected` - Initial connection confirmation
- `subscribed` - Subscription confirmation

## Environment Variables

Required environment variables in `.env.mcp`:

```env
# Vercel
VERCEL_API_TOKEN=your_token
VERCEL_PROJECT_ID=your_project_id

# Railway
RAILWAY_API_TOKEN=your_token
RAILWAY_PROJECT_ID=your_project_id

# Supabase
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# HuggingFace
HUGGINGFACE_API_TOKEN=your_token

# OpenAI
OPENAI_API_KEY=your_key

# GitHub
GITHUB_API_TOKEN=your_token

# MCP Server
MCP_API_KEY=your_api_key
MCP_PORT=3001

# LangChain / Tracing
LANGSMITH_API_KEY=your_key

# Google Maps (frontend, set in apps/web/.env)
VITE_GOOGLE_MAPS_API_KEY=your_key

# Security / Limits
MCP_API_KEY=concordbroker-mcp-key
CORS_ORIGINS=https://www.concordbroker.com,https://concordbroker.vercel.app
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=120
SUPABASE_ENABLE_SQL=false
```

## Usage Examples

### Check Service Health
```bash
curl http://localhost:3001/health
```

### Deploy to Vercel
```bash
curl -X POST http://localhost:3001/api/vercel/deploy \
  -H "x-api-key: your_api_key" \
  -H "Content-Type: application/json"
```

### Query Supabase
```bash
curl -X POST http://localhost:3001/api/supabase/query \
  -H "x-api-key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM properties LIMIT 10"}'
```

### Generate Text with HuggingFace
```bash
curl -X POST http://localhost:3001/api/huggingface/text-generation \
  -H "x-api-key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "The future of real estate is"}'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:3001');

ws.on('open', () => {
  // Subscribe to health updates
  ws.send(JSON.stringify({ type: 'health' }));
});

ws.on('message', (data) => {
  const message = JSON.parse(data);
  console.log('Received:', message);
});
```

## Monitoring

The server includes built-in monitoring:
- Health checks every 30 seconds
- Real-time WebSocket updates
- Service status dashboard at `/health`
- Detailed logs in console

## Security

- API key authentication for all endpoints
- Environment variables for sensitive data
- CORS configured for web access
- Service keys never exposed in responses

## Troubleshooting

### Service Connection Issues
1. Check environment variables are set correctly
2. Verify API tokens are valid
3. Check network connectivity
4. Review console logs for detailed errors

### WebSocket Issues
1. Ensure port 3001 is not blocked
2. Check firewall settings
3. Verify WebSocket client compatibility

## Development

### Running in Development Mode
```bash
npm run dev
```

### Testing Services
```bash
npm test
```

### Deploying MCP Server
```bash
npm run deploy
```

## Support

For issues or questions:
- GitHub: https://github.com/gSimani/ConcordBroker
- Website: https://www.concordbroker.com
