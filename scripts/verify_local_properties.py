#!/usr/bin/env python3
"""
Verify local properties page parity against production snapshot.

Actions:
- Ensure a local server is running at 5173 that serves apps/web/live-dist and proxies /api to API_PROXY (defaults to https://api.concordbroker.com)
- Run Playwright Python tests in tests/e2e/local_properties_playwright.py

Usage:
  python scripts/verify_local_properties.py
  API_PROXY=https://api.concordbroker.com python scripts/verify_local_properties.py
"""
import os
import socket
import subprocess
import sys
import time
from contextlib import closing


def port_open(port: int) -> bool:
  with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
    sock.settimeout(0.5)
    return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
  dist_dir = os.environ.get("DIST_DIR", "apps/web/live-dist")
  api_proxy = os.environ.get("API_PROXY", "https://api.concordbroker.com")

  # Ensure live-dist exists
  if not os.path.exists(os.path.join(dist_dir, "index.html")):
    print(f"Downloading production snapshot into {dist_dir} ...")
    subprocess.run([sys.executable, "scripts/download_vercel_assets.py", dist_dir], check=True)

  # Start server if 5173 not open
  if not port_open(5173):
    print("Starting local server on 5173 (serve-dist.cjs)...")
    env = os.environ.copy()
    env["DIST_DIR"] = dist_dir
    env["API_PROXY"] = api_proxy
    subprocess.Popen(["node", "scripts/serve-dist.cjs"], env=env)
    # Wait a bit for server to bind
    for _ in range(20):
      if port_open(5173):
        break
      time.sleep(0.25)
    if not port_open(5173):
      print("ERROR: Could not start local server on 5173")
      return 2

  # Ensure pytest + playwright present
  try:
    import pytest  # noqa
  except Exception:
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "playwright"], check=False)
  # Ensure browser
  try:
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
  except Exception:
    pass

  # Run tests
  print("Running Playwright checks for /properties ...")
  result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/e2e/local_properties_playwright.py"], check=False)
  return result.returncode


if __name__ == "__main__":
  sys.exit(main())

