"""
Meilisearch Configuration for Property Search
"""
import os
from typing import Dict, List

# Meilisearch connection
MEILISEARCH_URL = os.getenv('MEILISEARCH_URL', 'http://localhost:7700')
MEILISEARCH_KEY = os.getenv('MEILISEARCH_KEY', 'concordbroker-meili-master-key')

# Index name
PROPERTIES_INDEX = 'florida_properties'

# Meilisearch Index Settings
MEILISEARCH_SETTINGS = {
    "searchableAttributes": [
        "parcel_id",
        "address",
        "phy_addr1",
        "city",
        "phy_city",
        "owner_name",
        "owner",
        "county"
    ],
    "filterableAttributes": [
        "county",
        "propertyType",
        "landUseCode",
        "yearBuilt",
        "buildingSqFt",
        "landSqFt",
        "marketValue",
        "assessedValue",
        "isTaxDelinquent",
        "hasHomestead",
        "bedrooms",
        "bathrooms",
        "lastSalePrice",
        "isDistressed"
    ],
    "sortableAttributes": [
        "marketValue",
        "buildingSqFt",
        "landSqFt",
        "yearBuilt",
        "lastSaleDate",
        "lastSalePrice",
        "pricePerSqFt",
        "investmentScore"
    ],
    "rankingRules": [
        "words",
        "typo",
        "proximity",
        "attribute",
        "sort",
        "exactness"
    ],
    "typoTolerance": {
        "enabled": True,
        "minWordSizeForTypos": {
            "oneTypo": 4,
            "twoTypos": 8
        },
        "disableOnAttributes": ["parcel_id", "zipCode"]
    },
    "faceting": {
        "maxValuesPerFacet": 1000
    },
    "pagination": {
        "maxTotalHits": 1000000  # Support up to 1M results per query
    },
    "displayedAttributes": [
        "parcel_id",
        "address",
        "city",
        "county",
        "zipCode",
        "owner",
        "propertyType",
        "yearBuilt",
        "bedrooms",
        "bathrooms",
        "buildingSqFt",
        "landSqFt",
        "marketValue",
        "assessedValue",
        "taxAmount",
        "lastSalePrice",
        "lastSaleDate",
        "latitude",
        "longitude",
        "investmentScore",
        "capRate",
        "pricePerSqFt"
    ]
}

# Facets configuration for UI
FACETS_CONFIG = {
    "county": {
        "label": "County",
        "type": "select",
        "multi": True
    },
    "propertyType": {
        "label": "Property Type",
        "type": "select",
        "multi": True,
        "options": [
            "Residential",
            "Commercial",
            "Industrial",
            "Agricultural",
            "Vacant",
            "Government",
            "Religious"
        ]
    },
    "yearBuilt": {
        "label": "Year Built",
        "type": "range",
        "ranges": [
            {"label": "New (2020+)", "min": 2020, "max": 2025},
            {"label": "Modern (2000-2019)", "min": 2000, "max": 2019},
            {"label": "Recent (1980-1999)", "min": 1980, "max": 1999},
            {"label": "Older (Pre-1980)", "min": 1900, "max": 1979}
        ]
    },
    "marketValue": {
        "label": "Market Value",
        "type": "range",
        "ranges": [
            {"label": "Under $100K", "min": 0, "max": 100000},
            {"label": "$100K - $250K", "min": 100000, "max": 250000},
            {"label": "$250K - $500K", "min": 250000, "max": 500000},
            {"label": "$500K - $1M", "min": 500000, "max": 1000000},
            {"label": "$1M - $2M", "min": 1000000, "max": 2000000},
            {"label": "$2M+", "min": 2000000, "max": 999999999}
        ]
    },
    "buildingSqFt": {
        "label": "Building Size",
        "type": "range",
        "ranges": [
            {"label": "Small (0-1,500)", "min": 0, "max": 1500},
            {"label": "Medium (1,500-2,500)", "min": 1500, "max": 2500},
            {"label": "Large (2,500-5,000)", "min": 2500, "max": 5000},
            {"label": "Very Large (5,000-10,000)", "min": 5000, "max": 10000},
            {"label": "Mega (10,000+)", "min": 10000, "max": 999999}
        ]
    }
}

# Batch sizes for indexing
BATCH_SIZE = 10000  # Documents per batch
MAX_CONCURRENT_BATCHES = 4  # Parallel uploads

# Sync configuration
SYNC_SCHEDULE = "0 2 * * *"  # Daily at 2 AM EST
SYNC_BATCH_SIZE = 5000
SYNC_CHECK_INTERVAL = 3600  # Check for updates every hour

# Performance settings
CACHE_TTL = 300  # 5 minutes
AUTOCOMPLETE_CACHE_TTL = 60  # 1 minute
FACETS_CACHE_TTL = 600  # 10 minutes
