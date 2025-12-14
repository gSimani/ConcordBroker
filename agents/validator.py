from pathlib import Path
import pandas as pd


def quick_validate_csv(csv_path: Path, required_cols: list[str]) -> bool:
    try:
        df = pd.read_csv(csv_path, nrows=5)
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"[VALIDATE] Missing columns in {csv_path.name}: {missing}")
            return False
        return True
    except Exception as e:
        print(f"[VALIDATE] Error reading {csv_path.name}: {e}")
        return False

