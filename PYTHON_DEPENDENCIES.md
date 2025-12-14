# Python Dependency Management

## Overview

ConcordBroker now uses `pyproject.toml` for centralized Python dependency management instead of multiple `requirements-*.txt` files.

## Installation

### Option 1: Using pip (Simple)

```bash
# Install core dependencies only
pip install -e .

# Install with specific features
pip install -e ".[langchain,agents]"

# Install everything
pip install -e ".[all]"
```

### Option 2: Using Poetry (Recommended for Development)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install with optional groups
poetry install --with langchain,agents

# Install everything
poetry install --all-extras
```

## Available Dependency Groups

- **Core** (installed by default): FastAPI, Supabase, Redis, basic data processing
- **agents**: Agent system dependencies (async MQTT, scheduling, monitoring)
- **langchain**: LangChain & LLM orchestration
- **langgraph**: LangGraph state machines
- **vectorstores**: ChromaDB, FAISS, embeddings
- **documents**: PDF, DOCX, Excel processing
- **llm-providers**: Anthropic, OpenAI, Cohere, Google AI
- **nlp**: spaCy, NLTK, Transformers
- **ml**: TensorFlow, PyTorch, Keras, XGBoost
- **data-science**: Scipy, matplotlib, seaborn, plotly
- **scraping**: Playwright, Selenium, Scrapy
- **florida-data**: PyArrow, Polars, Dask (for large datasets)
- **graphdb**: Neo4j, NetworkX
- **dev**: pytest, black, ruff, mypy

## Examples

### For API Development
```bash
pip install -e ".[dev]"
```

### For Agent Development
```bash
pip install -e ".[agents,langchain,dev]"
```

### For Data Processing
```bash
pip install -e ".[florida-data,data-science,dev]"
```

### For Complete Development Environment
```bash
pip install -e ".[all]"
```

## Migrating from old requirements files

**Old approach:**
```bash
pip install -r requirements-langchain.txt
pip install -r requirements-agents.txt
```

**New approach:**
```bash
pip install -e ".[langchain,agents]"
```

## Development Workflow

1. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run tests**
   ```bash
   pytest
   ```

4. **Format code**
   ```bash
   black .
   ruff check . --fix
   ```

5. **Type checking**
   ```bash
   mypy .
   ```

## Adding New Dependencies

Edit `pyproject.toml` and add to the appropriate section:

```toml
[project]
dependencies = [
    # Add core dependencies here
    "new-package>=1.0.0",
]

[project.optional-dependencies]
your-feature = [
    # Add optional dependencies here
    "optional-package>=2.0.0",
]
```

Then reinstall:
```bash
pip install -e ".[your-feature]"
```

## Notes

- `requirements.txt` is kept for backward compatibility but should not be updated
- All new dependencies should be added to `pyproject.toml`
- Use semantic versioning (e.g., `>=1.0.0`) to allow compatible updates
- Pin exact versions only when necessary for stability
