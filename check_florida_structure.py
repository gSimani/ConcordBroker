import os
from pathlib import Path

root_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

print("Directory structure created:")
print("=" * 60)

# List first 5 county directories
counties = [d for d in root_dir.iterdir() if d.is_dir()]
for county in counties[:5]:
    print(f"\n{county.name}/")
    # List subdirectories (NAL, NAP, NAV, SDF)
    for subdir in county.iterdir():
        if subdir.is_dir():
            print(f"  ├── {subdir.name}/")
            # Check if any files exist
            files = list(subdir.glob("*"))
            if files:
                for f in files[:3]:
                    print(f"  │   └── {f.name}")
            else:
                print(f"  │   └── (empty)")

print(f"\n... and {len(counties)-5} more counties")
print(f"\nTotal counties: {len(counties)}")