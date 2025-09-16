"""
LangChain Configuration Module
Loads configuration from environment; no secrets are hardcoded.
"""

import os
from pathlib import Path


# Read API keys from environment only
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")


def configure_langsmith():
    """Configure LangSmith environment variables if provided."""
    if LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
        os.environ["LANGCHAIN_PROJECT"] = os.getenv(
            "LANGCHAIN_PROJECT", "concordbroker-property-analysis"
        )
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
            "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
        )
    return LANGSMITH_API_KEY


def configure_huggingface():
    """Configure HuggingFace environment variables if provided."""
    if HUGGINGFACE_API_TOKEN:
        os.environ["HUGGINGFACE_API_TOKEN"] = HUGGINGFACE_API_TOKEN
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACE_API_TOKEN
    return HUGGINGFACE_API_TOKEN


def get_openai_key():
    """Get OpenAI API key from environment or optional .env file."""
    for key_name in ["OPENAI_API_KEY", "OPENAI_KEY", "OPENAI_API"]:
        key = os.getenv(key_name)
        if key:
            return key

    # Optional: check root .env if present (not required)
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if "OPENAI" in line and "=" in line and not line.strip().startswith("#"):
                    key = line.split("=", 1)[1].strip()
                    if key:
                        return key
    return None


# Auto-configure from environment on import
configure_langsmith()
configure_huggingface()


# Configuration dictionary
LANGCHAIN_CONFIG = {
    # API Keys
    "langsmith_api_key": LANGSMITH_API_KEY,
    "huggingface_api_token": HUGGINGFACE_API_TOKEN,
    "openai_api_key": get_openai_key(),

    # LangSmith Settings
    "langchain_tracing": os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true",
    "langchain_project": os.getenv("LANGCHAIN_PROJECT", "concordbroker-property-analysis"),
    "langchain_endpoint": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),

    # Model Settings (updated to current models)
    "primary_model": os.getenv("PRIMARY_MODEL", "gpt-4o"),
    "secondary_model": os.getenv("SECONDARY_MODEL", "gpt-4o-mini"),
    "local_model": os.getenv("LOCAL_MODEL", "google/gemma-2b"),
    "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "4000")),

    # Vector Store Settings
    "vector_store_path": os.getenv("VECTOR_STORE_PATH", "./vector_stores"),
    "chroma_persist_dir": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
    "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),

    # RAG Settings
    "chunk_size": int(os.getenv("RAG_CHUNK_SIZE", "1000")),
    "chunk_overlap": int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
    "retrieval_k": int(os.getenv("RAG_RETRIEVAL_K", "5")),

    # Memory Settings
    "memory_storage_path": os.getenv("MEMORY_STORAGE_PATH", "./memory_storage"),
    "conversation_window_k": int(os.getenv("CONVERSATION_WINDOW_K", "10")),
    "max_token_limit": int(os.getenv("MAX_TOKEN_LIMIT", "2000")),

    # Agent Settings
    "max_iterations": int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
    "agent_timeout_minutes": int(os.getenv("AGENT_TIMEOUT_MINUTES", "30")),
    "verbose": os.getenv("AGENT_VERBOSE", "true").lower() == "true",
    "return_intermediate_steps": os.getenv("AGENT_RETURN_STEPS", "true").lower() == "true",

    # API Server Settings
    "api_host": os.getenv("API_HOST", "0.0.0.0"),
    "api_port": int(os.getenv("API_PORT", "8003")),

    # Database Settings (Optional)
    "postgres_host": os.getenv("POSTGRES_HOST"),
    "postgres_port": os.getenv("POSTGRES_PORT", "5432"),
    "postgres_db": os.getenv("POSTGRES_DB"),
    "postgres_user": os.getenv("POSTGRES_USER"),
    "postgres_password": os.getenv("POSTGRES_PASSWORD"),
    "database_url": os.getenv("DATABASE_URL"),

    # Supabase Settings
    "supabase_url": os.getenv("SUPABASE_URL"),
    "supabase_key": os.getenv("SUPABASE_ANON_KEY"),
}


def validate_config():
    """Validate configuration and report any issues"""
    issues = []
    if not LANGCHAIN_CONFIG["langsmith_api_key"]:
        issues.append("LangSmith API key not configured")
    if not LANGCHAIN_CONFIG["openai_api_key"]:
        issues.append("OpenAI API key not found - some features will be limited")
    if not LANGCHAIN_CONFIG["supabase_url"]:
        issues.append("Supabase URL not configured - database features may be limited")
    return issues


def get_config():
    """Get the full configuration dictionary"""
    return LANGCHAIN_CONFIG


def print_config():
    """Print current configuration (no secrets printed)."""
    print("=" * 60)
    print("LangChain Configuration")
    print("=" * 60)

    print("\n[API Keys]")
    print(f"  LangSmith: {'SET' if LANGSMITH_API_KEY else 'NOT SET'}")
    print(f"  HuggingFace: {'SET' if HUGGINGFACE_API_TOKEN else 'NOT SET'}")

    openai_key = get_openai_key()
    print(f"  OpenAI: {'SET' if openai_key else 'NOT SET'}")

    print("\n[Settings]")
    print(f"  Project: {LANGCHAIN_CONFIG['langchain_project']}")
    print(f"  Primary Model: {LANGCHAIN_CONFIG['primary_model']}")
    print(f"  Embeddings: {LANGCHAIN_CONFIG['embedding_model']}")

    print("\n[Validation]")
    issues = validate_config()
    if issues:
        for issue in issues:
            print(f"  [WARNING] {issue}")
    else:
        print("  [OK] All configurations valid")

    print("=" * 60)


if __name__ == "__main__":
    print_config()

