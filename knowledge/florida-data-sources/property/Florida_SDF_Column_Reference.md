# Florida SDF (Sales Data File) Column Reference

## Purpose
Sales Data File contains property transaction history for all 67 Florida counties.

## Key Columns

### Transaction Identifiers
| Column | Type | Description |
|--------|------|-------------|
| CO_NO | INT | County code |
| PARCEL_ID | TEXT | Parcel identifier |
| SALE_YR | INT | Year of sale |
| SALE_MO | INT | Month of sale |
| OR_BOOK | TEXT | Official Records book |
| OR_PAGE | TEXT | Official Records page |

### Sale Details
| Column | Type | Description |
|--------|------|-------------|
| SALE_PRC | BIGINT | Sale price |
| QUAL_CD | TEXT | Qualification code |
| VI_CD | TEXT | Validity indicator |
| MULTI_PAR | TEXT | Multi-parcel sale flag |

## Qualification Codes (Common)
- Q = Qualified (arm's length transaction)
- U = Unqualified
- V = Vacant land
- I = Improved property

## Validity Indicators
- 0 = Valid sale
- 1-9 = Various disqualification reasons

## Usage in ConcordBroker
Sales history is stored in `property_sales_history` table.
NAL file contains most recent 2 sales (SALE_PRC1, SALE_PRC2).
SDF contains full transaction history.
