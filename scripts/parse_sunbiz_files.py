#!/usr/bin/env python3
"""
Sunbiz Fixed-Width File Parser

Parses Florida Department of State business entity files in fixed-width format.
Handles three file types:
1. Corporate filings (c) - Business entity registrations
2. Corporate events (ce) - Status changes and updates
3. Fictitious names (fn) - DBA registrations

File Format: Fixed-width text (not CSV)
Source: SFTP sftp.floridados.gov:/doc/cor/ and /doc/fic/
Pattern: yyyymmddc.txt, yyyymmddce.txt, yyyymmddfn.txt

Usage:
    python scripts/parse_sunbiz_files.py corporate 20251106c.txt output.jsonl
    python scripts/parse_sunbiz_files.py events 20251106ce.txt output.jsonl
    python scripts/parse_sunbiz_files.py fictitious 20251106fn.txt output.jsonl
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Iterator
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SunbizFileParser:
    """Parser for Florida Sunbiz fixed-width format files"""

    # Fixed-width format specifications (based on FL DOS documentation)
    CORPORATE_SPEC = {
        'doc_number': (0, 12),          # Document number (filing number)
        'entity_name': (12, 172),       # Entity name (160 chars)
        'status': (172, 173),           # Status code (A=Active, I=Inactive, etc)
        'filing_type': (173, 175),      # Filing type code
        'filing_date': (175, 183),      # Filing date YYYYMMDD
        'state': (183, 185),            # State code
        'prin_addr1': (185, 225),       # Principal address line 1
        'prin_addr2': (225, 265),       # Principal address line 2
        'prin_city': (265, 305),        # Principal city
        'prin_state': (305, 307),       # Principal state
        'prin_zip': (307, 317),         # Principal ZIP
        'mail_addr1': (317, 357),       # Mailing address line 1
        'mail_addr2': (357, 397),       # Mailing address line 2
        'mail_city': (397, 437),        # Mailing city
        'mail_state': (437, 439),       # Mailing state
        'mail_zip': (439, 449),         # Mailing ZIP
        'fei_number': (449, 461),       # Federal EIN
    }

    EVENTS_SPEC = {
        'doc_number': (0, 12),          # Document number
        'event_date': (12, 20),         # Event date YYYYMMDD
        'event_type': (20, 22),         # Event type code
        'event_desc': (22, 122),        # Event description
        'effective_date': (122, 130),   # Effective date YYYYMMDD
    }

    FICTITIOUS_SPEC = {
        'file_number': (0, 12),         # File number
        'business_name': (12, 92),      # Business name
        'owner_name': (92, 172),        # Owner name
        'owner_addr1': (172, 212),      # Owner address line 1
        'owner_addr2': (212, 252),      # Owner address line 2
        'owner_city': (252, 282),       # Owner city
        'owner_state': (282, 284),      # Owner state
        'owner_zip': (284, 294),        # Owner ZIP
        'filed_date': (294, 302),       # Filed date YYYYMMDD
        'expires_date': (302, 310),     # Expiration date YYYYMMDD
        'status': (310, 311),           # Status code
    }

    def __init__(self, file_type: str):
        """
        Initialize parser for specific file type

        Args:
            file_type: 'corporate', 'events', or 'fictitious'
        """
        self.file_type = file_type.lower()

        if self.file_type == 'corporate':
            self.spec = self.CORPORATE_SPEC
        elif self.file_type == 'events':
            self.spec = self.EVENTS_SPEC
        elif self.file_type == 'fictitious':
            self.spec = self.FICTITIOUS_SPEC
        else:
            raise ValueError(f"Invalid file type: {file_type}. Must be corporate, events, or fictitious")

    def parse_line(self, line: str) -> Dict:
        """
        Parse a single line of fixed-width data

        Args:
            line: Fixed-width text line

        Returns:
            Dictionary with parsed fields
        """
        record = {}

        for field_name, (start, end) in self.spec.items():
            try:
                value = line[start:end].strip()

                # Convert date fields to ISO format
                if field_name.endswith('_date') and value and len(value) == 8:
                    try:
                        date_obj = datetime.strptime(value, '%Y%m%d')
                        value = date_obj.isoformat()
                    except ValueError:
                        value = None

                # Clean empty strings to None
                record[field_name] = value if value else None

            except IndexError:
                # Line too short, field missing
                record[field_name] = None

        return record

    def parse_file(self, input_path: Path) -> Iterator[Dict]:
        """
        Parse entire file line by line

        Args:
            input_path: Path to input file

        Yields:
            Parsed records
        """
        logger.info(f"Parsing {self.file_type} file: {input_path}")

        line_count = 0
        error_count = 0

        with open(input_path, 'r', encoding='latin-1') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1

                # Skip empty lines
                if not line.strip():
                    continue

                try:
                    record = self.parse_line(line)
                    record['_line_number'] = line_num
                    record['_source_file'] = input_path.name
                    yield record

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error parsing line {line_num}: {e}")
                    if error_count > 100:
                        logger.error("Too many errors, stopping")
                        break

        logger.info(f"Parsed {line_count} lines with {error_count} errors")

    def parse_to_jsonl(self, input_path: Path, output_path: Path):
        """
        Parse file and write to JSONL format

        Args:
            input_path: Path to input file
            output_path: Path to output JSONL file
        """
        logger.info(f"Writing to: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as out:
            for record in self.parse_file(input_path):
                json.dump(record, out)
                out.write('\n')

        logger.info(f"Parsing complete: {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) != 4:
        print("Usage: parse_sunbiz_files.py <type> <input_file> <output_file>")
        print("Types: corporate, events, fictitious")
        print("")
        print("Example:")
        print("  parse_sunbiz_files.py corporate 20251106c.txt output.jsonl")
        sys.exit(1)

    file_type = sys.argv[1]
    input_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3])

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    try:
        parser = SunbizFileParser(file_type)
        parser.parse_to_jsonl(input_file, output_file)
        logger.info("Success!")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
