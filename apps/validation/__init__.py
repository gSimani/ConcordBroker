"""
UI Field Validation Package

Validates that UI fields display correct database values by:
1. Crawling website pages with Firecrawl
2. Extracting label-field pairs from HTML
3. Mapping labels to database schema
4. Comparing displayed values with database values
5. Generating validation reports
"""

from .ui_field_validator import UIFieldValidationOrchestrator
from .config import config
from .schema_mapper import SchemaMapper
from .firecrawl_scraper import FirecrawlScraper
from .validator import FieldValidator
from .reporter import ValidationReporter

__all__ = [
    'UIFieldValidationOrchestrator',
    'config',
    'SchemaMapper',
    'FirecrawlScraper',
    'FieldValidator',
    'ValidationReporter'
]

__version__ = '1.0.0'
