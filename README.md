# ConcordBroker

Automated real estate investment property acquisition system for Broward County, Florida.

## Overview

ConcordBroker automates the collection and analysis of property data from multiple Florida government sources to identify investment opportunities in Broward County. The system normalizes owner/entity information, scores properties based on configurable criteria, and surfaces candidates through a modern web interface.

## Features

- **Automated Data Collection**: ETL pipelines for Florida DOR, Broward Official Records, and Sunbiz
- **Entity Resolution**: Intelligent matching of property owners to corporate entities
- **Property Scoring**: Multi-factor scoring algorithm for investment potential
- **Web Interface**: React-based UI for searching and analyzing properties
- **Real-time Updates**: Daily synchronization with official data sources
- **Authentication**: Secure access with Twilio Verify
- **Notifications**: Email alerts for new opportunities via SendGrid

## Architecture

- **Frontend**: Vercel (Vite/React + Tailwind + shadcn)
- **Backend API**: FastAPI on Railway
- **Database**: Supabase (Postgres + pgvector)
- **Workers**: Python ETL pipelines on Railway
- **Authentication**: Twilio Verify
- **Email**: Twilio SendGrid
- **CDN/Security**: Cloudflare
- **Monitoring**: Sentry

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- PNPM
- Poetry
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/gSimani/ConcordBroker.git
cd ConcordBroker

# Install frontend dependencies
cd apps/frontend
pnpm install

# Install API dependencies
cd ../api
poetry install

# Install worker dependencies
cd ../workers
poetry install
```

### Configuration

1. Copy the template environment file:
```bash
cp infra/secrets/.template.env .env
```

2. Configure required environment variables:
- Supabase credentials
- Twilio/SendGrid API keys
- OpenAI/HuggingFace tokens (for RAG)
- Sentry DSN

### Development

```bash
# Run the API
cd apps/api
poetry run uvicorn main:app --reload

# Run the frontend
cd apps/frontend
pnpm dev

# Run workers locally
cd apps/workers
poetry run python -m dor_loader.main
```

## Documentation

- [Project Design & Runbook (PDR)](docs/PDR.md) - Single source of truth
- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## Data Sources

- **Florida DOR**: Property assessment rolls (NAL/SDF files)
- **Broward Official Records**: Daily document recordings
- **Sunbiz**: Florida corporate entity database

## Project Structure

```
ConcordBroker/
├── apps/
│   ├── frontend/     # React UI
│   ├── api/          # FastAPI backend
│   └── workers/      # ETL pipelines
├── infra/
│   ├── terraform/    # Infrastructure as Code
│   └── scripts/      # Deployment scripts
├── docs/             # Documentation
├── tests/            # Test suites
└── db/               # Database schemas
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please use the GitHub issue tracker.

## Roadmap

- Week 1: Core schema, DOR/Sunbiz loaders, API skeleton
- Week 2: Official Records loader, scoring algorithm, basic UI
- Week 3: Authentication, email notifications, Cloudflare integration
- Week 4: Playwright scrapers, UI polish, performance optimization
>>>>>>> 10fd2a978f3bac09eec27d108b16b10b67c89fa2
## Local Environment & AI Provider

- Environment files
  - Use `.env.mcp` for local development (server-side only secrets).
  - Frontend must only use public vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
  - Backend uses `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (never expose to frontend).

- Quick env check
  - `python scripts/tools/preflight_env.py` (prints presence, no secret values)

- Supabase smoke test (backend)
  - `python -c "from dotenv import load_dotenv; import os; from supabase import create_client; load_dotenv('.env.mcp'); c=create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')); print(c.table('auction_sites').select('county').limit(3).execute().data)"`

- AI provider selection
  - Preferred: Vercel AI Gateway (`AI_GATEWAY_API_KEY`) → `https://ai-gateway.vercel.sh/v1`
  - Fallback: OpenAI (`OPENAI_API_KEY`) → `https://api.openai.com/v1`
  - Helper: `from scripts.common.ai_client import get_openai_client_config`

Example (Python):

```python
from dotenv import load_dotenv
from scripts.common.ai_client import get_openai_client_config
import os, requests, json

load_dotenv('.env.mcp')
base_url, api_key = get_openai_client_config()
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': 'ping'}]}
print(requests.post(f'{base_url}/chat/completions', headers=headers, data=json.dumps(payload)).json())
```
