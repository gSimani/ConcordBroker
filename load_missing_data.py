# Load missing Florida data sources

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# List of data files to download and load
FILES_TO_LOAD = {
    'SDF': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF16P202501.csv',
    'NAV': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV16P202501.csv',
    'NAP': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP16P202501.csv',
}

# Download and load each file
for name, url in FILES_TO_LOAD.items():
    print(f"Downloading {name} from {url}")
    # Download logic here
    # Load to appropriate table
