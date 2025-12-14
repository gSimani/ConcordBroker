from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    # SharePoint
    public_records_url: str = (
        "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path="
        "/property/dataportal/Documents/PTO%20Data%20Portal/~Public%20Records"
    )
    manifest_path: Path = Path("data/manifests/dor_public_records_manifest.json")
    cas_dir: Path = Path(".cas")
    downloads_dir: Path = Path("historical_data/downloads")
    extracts_dir: Path = Path("historical_data/extracts")

    # DB (reuse existing settings from integrate_historical_data_psycopg2.py)
    pg_host: str = 'aws-1-us-east-1.pooler.supabase.com'
    pg_port: int = 5432
    pg_db: str = 'postgres'
    pg_user: str = 'postgres.pmispwtdngkcmsrsjwbp'
    pg_password: str = 'West@Boca613!'
    pg_sslmode: str = 'require'
    pg_statement_timeout_ms: int = 300000

    # Concurrency
    download_concurrency: int = 4
    ingest_concurrency: int = 2  # DB-heavy concurrent ingests (tuned for 2 cores)

