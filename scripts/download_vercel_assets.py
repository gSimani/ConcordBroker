import os
import re
import sys
import pathlib
from urllib.parse import urljoin

import urllib.request


BASE_URL = "https://www.concordbroker.com"
START_PATH = "/properties"
# Allow override via CLI arg or OUT_DIR env
def get_out_dir():
    import os, sys
    if len(sys.argv) > 1:
        return pathlib.Path(sys.argv[1]).resolve()
    env_out = os.getenv("OUT_DIR")
    if env_out:
        return pathlib.Path(env_out).resolve()
    return pathlib.Path("apps/web/dist").resolve()


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def ensure_parent(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def main():
    out_dir = get_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    start_url = urljoin(BASE_URL, START_PATH)
    html = fetch(start_url)
    index_path = out_dir / "index.html"
    ensure_parent(index_path)
    index_path.write_bytes(html)
    print(f"Saved {index_path}")

    text = html.decode("utf-8", errors="ignore")
    # Extract asset urls (js/css)
    assets = set(re.findall(r"/assets/[^\"'>]+\.(?:js|css)", text))
    if not assets:
        print("No assets found under /assets in HTML.")
    for rel in sorted(assets):
        url = urljoin(BASE_URL, rel)
        out_path = out_dir / rel.lstrip("/")
        ensure_parent(out_path)
        try:
            data = fetch(url)
            out_path.write_bytes(data)
            print(f"Saved {out_path}")
            # Try sourcemap, if any
            if out_path.suffix == ".js":
                map_url = url + ".map"
                map_path = pathlib.Path(str(out_path) + ".map")
                try:
                    data_map = fetch(map_url)
                    map_path.write_bytes(data_map)
                    print(f"Saved {map_path}")
                except Exception:
                    pass
        except Exception as e:
            print(f"Failed {url}: {e}")


if __name__ == "__main__":
    sys.exit(main())
