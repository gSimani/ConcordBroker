#!/usr/bin/env python3
"""
Run the NAL orchestrator with live progress, starting with a single county (optional).

Examples:
  python scripts/run_agents.py --ticket ~20251103-1264400 --years 2009-2023 --county GILCHRIST
  python scripts/run_agents.py --ticket ~20251103-1264400 --years 2009-2012
"""
import argparse
from agents.config import Settings
from agents.orchestrator import Orchestrator


def main():
    ap = argparse.ArgumentParser(description='Run multi-agent orchestrator (NAL) with live progress')
    ap.add_argument('--ticket', default='~20251103-1264400', help='Public Records ticket (e.g., ~20251103-1264400)')
    ap.add_argument('--years', default='2009-2023', help='Year range (e.g., 2009-2023)')
    ap.add_argument('--county', help='Single county (e.g., GILCHRIST)')
    ap.add_argument('--limit', type=int, help='Row limit per CSV ingestion')
    ap.add_argument('--batch-size', type=int, default=500)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--ingest-workers', type=int, help='DB-heavy ingest concurrency (default from Settings)')
    ap.add_argument('--phase-index', type=int, help='Phase index (e.g., 1)')
    ap.add_argument('--phase-total', type=int, help='Total phases (e.g., 4)')
    ap.add_argument('--ingest-workers', type=int, help='DB-heavy ingest concurrency (default from Settings)')
    args = ap.parse_args()

    # Parse years
    if '-' in args.years:
        a, b = args.years.split('-', 1)
        years = list(range(int(a), int(b) + 1))
    else:
        years = [int(args.years)]

    s = Settings()
    if args.ingest_workers:
        s.ingest_concurrency = args.ingest_workers
    orch = Orchestrator(s)
    orch.enqueue_nal(ticket=args.ticket, years=years, county=args.county)
    orch.run(workers=args.workers, limit=args.limit, batch_size=args.batch_size, phase_index=args.phase_index, phase_total=args.phase_total, county=args.county, years=(min(years), max(years)))


if __name__ == '__main__':
    main()

