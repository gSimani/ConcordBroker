from pathlib import Path
import zipfile


def extract_zip(zip_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(out_dir)
    cs = list(out_dir.rglob('*.csv'))
    print(f"[EXTRACT] {zip_path.name} -> {out_dir} ({len(cs)} CSVs)")
    return cs

