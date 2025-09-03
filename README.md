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