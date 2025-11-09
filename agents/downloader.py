from pathlib import Path
import hashlib
import requests
from .config import Settings


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stream_download(url: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get('Content-Length', '0'))
        downloaded = 0
        chunk = 1024 * 64
        print(f"[DOWN] {url}")
        with open(out_path, 'wb') as f:
            for data in r.iter_content(chunk_size=chunk):
                if not data:
                    continue
                f.write(data)
                downloaded += len(data)
                # simple inline bar
                _render(downloaded, total or 1)
    print()


def _render(done: int, total: int):
    pct = int((done / total) * 100)
    width = 30
    fill = int(width * done / total)
    bar = '#' * fill + '-' * (width - fill)
    print(f"\r[DOWN] [{bar}] {pct:3d}%  {done:,}/{total:,}", end='', flush=True)


def download_with_cas(url: str, settings: Settings) -> Path:
    # download to temp file
    tmp = settings.downloads_dir / (Path(url).name or 'artifact')
    stream_download(url, tmp)
    # move to CAS
    digest = sha256_file(tmp)
    cas_dir = settings.cas_dir / digest[:2] / digest[2:4]
    cas_dir.mkdir(parents=True, exist_ok=True)
    cas_path = cas_dir / digest
    if not cas_path.exists():
        tmp.replace(cas_path)
    else:
        tmp.unlink(missing_ok=True)
    print(f"[CAS] {digest} -> {cas_path}")
    return cas_path

