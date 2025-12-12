# Broward County Daily Index Extract Files

## Overview
Daily recording index files available for 7 days after creation.

## File Types

### CFN Files (MM-DD-YYcfn.txt)
One record per Clerk's File Number containing:
- Recording date/time
- Document type
- Consideration amount
- Book/page numbers
- Legal description
- Parcel ID

### Name Files (MM-DD-YYnme.txt)
Multiple name records per document:
- Party name
- Party type (direct or reverse)
- Name sequence

### Link Files (MM-DD-YYlnk.txt)
Links new recordings to prior related records.
Example: Satisfaction of Mortgage linked to original Mortgage

## File Format
- Delimiter: Pipe character (|)
- Trailing spaces removed
- Leading zeros removed from numeric data
- Empty fields: null (||)
- No activity: 0 byte file

## Scope
Broward County ONLY - other counties may have different systems.
