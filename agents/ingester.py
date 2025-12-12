from pathlib import Path
from typing import Optional
from scripts.integrate_historical_data_psycopg2 import HistoricalDataIntegratorPG


def ingest_csv(dataset: str, csv_path: Path, county: str, year: Optional[int] = None,
               limit: Optional[int] = None, batch_size: int = 500):
    ing = HistoricalDataIntegratorPG()
    if not ing.connect():
        raise RuntimeError('DB connect failed')
    try:
        if dataset.upper() == 'NAL':
            df = ing.parse_nal_file(csv_path, county)
            if limit:
                df = df.head(limit)
            ing.upload_to_postgres(df, batch_size=batch_size)
        elif dataset.upper() == 'SDF':
            if year is None:
                raise ValueError('year is required for SDF ingestion')
            df = ing.parse_sdf_file(csv_path, county, year)
            if limit:
                df = df.head(limit)
            ing.upload_sdf_to_postgres(df, batch_size=batch_size)
        elif dataset.upper() == 'NAP':
            df = ing.parse_nap_file(csv_path, county)
            if limit:
                df = df.head(limit)
            ing.upload_nap_to_postgres(df, batch_size=batch_size)
        else:
            raise ValueError(f'Unsupported dataset: {dataset}')
    finally:
        ing.disconnect()

