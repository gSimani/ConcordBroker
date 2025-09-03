# Contributing to ConcordBroker

Thank you for your interest in contributing to ConcordBroker! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Issues

- Check if the issue already exists in the issue tracker
- Provide clear description and steps to reproduce
- Include relevant logs and screenshots

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Follow the coding standards
4. Write or update tests
5. Update documentation and PDR if needed
6. Submit PR with clear description

## Development Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker
- PNPM
- Poetry

### Setup Instructions

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

## Coding Standards

### Python

- Use Black for formatting
- Use ruff for linting
- Type hints required
- 100% test coverage for new code

### TypeScript/JavaScript

- Use Prettier for formatting
- Use ESLint
- Use TypeScript for all new code

### Commits

- Follow conventional commits format
- Examples:
  - `feat(api): add parcel search endpoint`
  - `fix(workers): handle missing fields in DOR loader`
  - `docs: update API documentation`

## Testing

```bash
# Run Python tests
poetry run pytest

# Run frontend tests
pnpm test

# Run linting
poetry run ruff check .
pnpm lint
```

## Documentation

- Update the PDR for any architectural changes
- Add docstrings to all functions
- Update README if adding new features

## Questions?

Open an issue for any questions about contributing.