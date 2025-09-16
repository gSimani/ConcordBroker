"""
Inventory local county datasets and summarize Supabase ingestion status.
"""

import os
import glob
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "TEMP", "DATABASE PROPERTY APP")
LOGS = os.path.join(ROOT, "logs")

def scan_local():
    result = {"counties": {}, "totals": {"NAL":0,"NAP":0,"NAV":0,"SDF":0}}
    if not os.path.isdir(DATA_DIR):
        return result
    for name in sorted(os.listdir(DATA_DIR)):
        if name in ("NAL_2025","NAL_2025P"):
            continue
        cpath = os.path.join(DATA_DIR, name)
        if not os.path.isdir(cpath):
            continue
        entry = {}
        for dtype in ("NAL","NAP","NAV","SDF"):
            dpath = os.path.join(cpath, dtype)
            if os.path.isdir(dpath):
                files = glob.glob(os.path.join(dpath, "*"))
                entry[dtype] = len(files)
                if dtype in result["totals"]:
                    result["totals"][dtype] += 1 if len(files)>0 else 0
            else:
                entry[dtype] = 0
        result["counties"][name] = entry
    return result

def main():
    os.makedirs(LOGS, exist_ok=True)
    local = scan_local()
    out_path = os.path.join(LOGS, "datasets_inventory.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(local, f, indent=2)
    print(f"Wrote {out_path}")
    total_counties = len(local.get("counties", {}))
    nal_cov = sum(1 for c in local.get("counties",{}).values() if c.get("NAL",0)>0)
    print(f"Counties found: {total_counties} | NAL available for {nal_cov}")
    for cname, info in list(local.get("counties",{}).items())[:10]:
        print(f" - {cname}: NAL={info['NAL']} NAP={info['NAP']} NAV={info['NAV']} SDF={info['SDF']}")

if __name__ == "__main__":
    main()
