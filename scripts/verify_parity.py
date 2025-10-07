#!/usr/bin/env python3
"""
Verify local UI parity with production without requiring a headless browser.

Checks:
- Ensures local server on 5173 is serving apps/web/live-dist
- Fetches production /properties HTML + asset URLs
- Compares local apps/web/live-dist files to freshly-downloaded production assets (byte-for-byte)
- Probes key API endpoints via local proxy and directly against production API and compares payloads for small queries

Exit codes:
 0 = parity OK
 1 = parity failed (mismatch)
 2 = environment/server issue
"""
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from urllib.parse import urljoin
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIST = REPO_ROOT / 'apps' / 'web' / 'live-dist'
LOCAL_BASE = 'http://localhost:5173'
PROD_BASE = 'https://www.concordbroker.com'
PROD_API = os.environ.get('PROD_API_URL', 'https://api.concordbroker.com')


def port_open(host: str, port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def sha256(data: bytes) -> str:
    h = hashlib.sha256(); h.update(data); return h.hexdigest()


def ensure_live_snapshot():
    index = LIVE_DIST / 'index.html'
    if not index.exists():
        print('[verify] Downloading production snapshot to apps/web/live-dist ...')
        subprocess.run([sys.executable, str(REPO_ROOT / 'scripts' / 'download_vercel_assets.py'), str(LIVE_DIST)], check=True)


def ensure_server():
    if not port_open('127.0.0.1', 5173):
        env = os.environ.copy()
        env.setdefault('DIST_DIR', str(LIVE_DIST))
        # Prefer production API; user can override via RAILWAY_PUBLIC_URL.txt already set.
        env.setdefault('API_PROXY', PROD_API)
        subprocess.Popen(['node', str(REPO_ROOT / 'scripts' / 'serve-dist.cjs')], cwd=str(REPO_ROOT), env=env)
        for _ in range(30):
            if port_open('127.0.0.1', 5173):
                break
            time.sleep(0.2)
        if not port_open('127.0.0.1', 5173):
            print('[verify] ERROR: Could not start local server on 5173')
            sys.exit(2)


def compare_assets() -> bool:
    tmp = REPO_ROOT / '_parity_tmp'
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    # Fetch production HTML
    html = fetch(urljoin(PROD_BASE, '/properties')).decode('utf-8', errors='ignore')
    # Extract assets
    assets = sorted(set(re.findall(r"/assets/[^\"'>]+\.(?:js|css)", html)))
    ok = True
    mismatches = []
    for rel in assets:
        prod_bytes = fetch(urljoin(PROD_BASE, rel))
        local_path = LIVE_DIST / rel.lstrip('/')
        if not local_path.exists():
            print(f"[verify] MISSING local asset: {local_path}")
            ok = False
            continue
        local_bytes = local_path.read_bytes()
        if sha256(prod_bytes) != sha256(local_bytes):
            mismatches.append(rel)
            ok = False
    if not ok:
        print('[verify] Asset mismatches:', json.dumps(mismatches[:10]))
    else:
        print('[verify] Assets match production')
    return ok


def compare_api() -> bool:
    ok = True
    # Minimal probes for equality of payload for small queries
    tests = [
        '/api/properties/search?limit=1',
        '/api/properties?limit=1',
    ]
    for path in tests:
        try:
            local = fetch(urljoin(LOCAL_BASE, path))
            prod = fetch(urljoin(PROD_API, path))
            if local != prod:
                # Allow formatting differences if JSON. Compare parsed if possible
                try:
                    lobj = json.loads(local.decode('utf-8'))
                    pobj = json.loads(prod.decode('utf-8'))
                    if lobj != pobj:
                        print(f'[verify] API payload differs for {path}')
                        ok = False
                except Exception:
                    print(f'[verify] API raw differs for {path}')
                    ok = False
        except Exception as e:
            # Non-fatal if endpoint not present; but signal
            print(f'[verify] API probe failed {path}: {e}')
            ok = False
    if ok:
        print('[verify] API parity checks passed')
    return ok


def main() -> int:
    ensure_live_snapshot()
    ensure_server()
    a = compare_assets()
    p = compare_api()
    if a and p:
        print('[verify] Parity OK: local UI and API match production')
        return 0
    print('[verify] Parity FAILED')
    return 1


if __name__ == '__main__':
    sys.exit(main())
