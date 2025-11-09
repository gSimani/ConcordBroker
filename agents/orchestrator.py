from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import asdict
from pathlib import Path
import json
import re
from typing import Iterable, Optional, Tuple

from .config import Settings
from .models import Task
from .queue import InMemoryQueue
from .downloader import download_with_cas
from .extractor import extract_zip
from .ingester import ingest_csv


def iter_ticket_nal(manifest: dict, ticket: str, years: Iterable[int]):
    out = []
    for y in manifest.get('manifest', {}):
        try:
            yi = int(y)
        except:
            continue
        if yi not in years:
            continue
        counties = manifest['manifest'][y]
        for c in counties:
            datasets = counties[c]
            if 'NAL' not in datasets:
                continue
            for item in datasets['NAL']:
                url = item.get('url', '')
                name = item.get('name', '')
                if ticket in url and re.match(rf'^{yi}(F|P)\.zip$', name, re.IGNORECASE):
                    out.append((yi, url, name))
    return sorted(set(out))


class Orchestrator:
    def __init__(self, settings: Settings):
        self.s = settings
        self.q = InMemoryQueue()
        self._ingest_sema = threading.BoundedSemaphore(self.s.ingest_concurrency)

    def load_manifest(self) -> dict:
        return json.loads(self.s.manifest_path.read_text(encoding='utf-8'))

    def enqueue_nal(self, ticket: str, years: Iterable[int], county: str | None = None):
        man = self.load_manifest()
        pairs = iter_ticket_nal(man, ticket, years)
        for yi, url, name in pairs:
            t = Task(dataset='NAL', year=yi, county=county, ticket=ticket, url=url, release=name[-5:-4])
            self.q.put(t)

    def run(self, workers: int = 2, limit: Optional[int] = None, batch_size: int = 500, phase_index: Optional[int] = None, phase_total: Optional[int] = None, county: Optional[str] = None, years: Optional[Tuple[int, int]] = None):
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = []
            total = self.q.size()
            done = 0
            while self.q.size() > 0:
                t = self.q.get()
                if not t:
                    break
                self._write_progress(done, total, phase_index, phase_total, county, years, current=f"enqueue:{t.year}")
                futs.append(ex.submit(self._process_task, t, limit, batch_size, phase_index, phase_total, county, years))
            for f in as_completed(futs):
                try:
                    f.result()
                    done += 1
                    self._write_progress(done, total, phase_index, phase_total, county, years)
                except Exception as e:
                    print(f"[ORCH] Task failed: {e}")

    def _process_task(self, t: Task, limit: Optional[int], batch_size: int, phase_index: Optional[int], phase_total: Optional[int], county: Optional[str], years: Optional[Tuple[int, int]]):
        print(f"\n[ORCH] Processing: {asdict(t)}")
        # 1) Download zip to CAS
        cas_path = download_with_cas(t.url, self.s)
        # 2) Extract
        year_dir = self.s.extracts_dir / f"{t.ticket}_{t.year}"
        csvs = extract_zip(cas_path, year_dir)
        # 3) For each CSV, infer county (or use provided), ingest
        for csv in csvs:
            if 'NAL' not in csv.name.upper():
                continue
            county = t.county or self._guess_county(csv.name)
            if county and t.county and county.upper() != t.county.upper():
                continue
            if not county:
                print(f"[ORCH] Skip county-undetermined: {csv.name}")
                continue
            print(f"[ORCH] Ingest NAL: {csv.name} county={county}")
            with self._ingest_sema:
                ingest_csv('NAL', csv, county=county, year=None, limit=limit, batch_size=batch_size)
            self._write_progress(None, None, phase_index, phase_total, county, years, current=f"ingested:{csv.name}")

    def _guess_county(self, name: str) -> str | None:
        # Heuristic: name may contain '_31Gilchrist_' or textual county name
        from scripts.integrate_historical_data_psycopg2 import COUNTY_CODES
        # textual
        for cname in COUNTY_CODES.keys():
            if cname.replace(' ', '').upper() in name.replace(' ', '').upper():
                return cname
        # numeric code fallback
        m = re.search(r'_(\d{2})([A-Za-z ]+)_', name)
        if m:
            code = str(int(m.group(1)))
            inv = {v: k for k, v in COUNTY_CODES.items()}
            return inv.get(code)
        return None


    def _write_progress(self, done: Optional[int], total: Optional[int], phase_index: Optional[int], phase_total: Optional[int], county: Optional[str], years: Optional[Tuple[int, int]], current: Optional[str] = None):
        try:
            info = {
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()+'Z',
                'phase_index': phase_index,
                'phase_total': phase_total,
                'county': county,
                'years': {'start': years[0], 'end': years[1]} if years else None,
                'done': done,
                'total': total,
                'percent': (int(done*100/total) if (done is not None and total) else None),
                'current': current
            }
            out = Path('.agent/progress.json')
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(info, indent=2), encoding='utf-8')
        except Exception:
            pass



