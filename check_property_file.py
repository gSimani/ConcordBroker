"""
Check what's in the PropertyData.zip file
"""

import os
from pathlib import Path

file_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD\PropertyData.zip")

print(f"File exists: {file_path.exists()}")
print(f"File size: {file_path.stat().st_size} bytes")

# Read first bytes to check file signature
with open(file_path, 'rb') as f:
    first_bytes = f.read(100)
    
    # Check if it's actually a ZIP file (should start with PK)
    if first_bytes[:2] == b'PK':
        print("This is a valid ZIP file")
    elif first_bytes[:5] == b'<html' or first_bytes[:5] == b'<!DOC':
        print("This is an HTML file (probably an error page)")
        # Read as text to see the content
        f.seek(0)
        content = f.read().decode('utf-8', errors='ignore')
        print("\nContent (first 1000 chars):")
        print(content[:1000])
    else:
        print(f"Unknown file type. First bytes: {first_bytes[:20]}")
        
        # Try to read as text
        f.seek(0)
        try:
            content = f.read().decode('utf-8', errors='ignore')
            print("\nContent as text (first 1000 chars):")
            print(content[:1000])
        except:
            print("Cannot decode as text")