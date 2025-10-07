"""
Florida NAV File Finder
Discovers available NAV files from Florida Department of Revenue
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path

class NAVFileFinder:
    def __init__(self):
        self.base_urls = {
            'D': 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20D',
            'N': 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20N'
        }

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_nav_file_list(self, nav_type='D'):
        """Scrape the Florida Revenue site for available NAV files"""
        url = self.base_urls[nav_type]

        try:
            print(f"Fetching NAV {nav_type} file list from: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links to .TXT files
            nav_files = []
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                if href.endswith('.TXT') and f'NAV{nav_type}' in href.upper():
                    # Extract filename
                    filename = href.split('/')[-1]
                    # Build full URL
                    full_url = urljoin(url, href)
                    nav_files.append({
                        'filename': filename,
                        'url': full_url,
                        'type': nav_type
                    })

            print(f"Found {len(nav_files)} NAV {nav_type} files")
            return nav_files

        except Exception as e:
            print(f"Error fetching NAV {nav_type} files: {e}")
            return []

    def download_sample_files(self, max_files=5):
        """Download a few sample files to test the data structure"""
        sample_dir = Path("TEMP/NAV_SAMPLES")
        sample_dir.mkdir(parents=True, exist_ok=True)

        for nav_type in ['D', 'N']:
            files = self.get_nav_file_list(nav_type)

            for i, file_info in enumerate(files[:max_files]):
                print(f"\nDownloading sample: {file_info['filename']}")

                try:
                    response = self.session.get(file_info['url'], stream=True, timeout=60)
                    response.raise_for_status()

                    local_path = sample_dir / file_info['filename']

                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print(f"Downloaded: {local_path}")

                    # Check if it's actually data (not HTML)
                    with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('<!DOCTYPE') or first_line.startswith('<html'):
                            print(f"Warning: {file_info['filename']} appears to be HTML, not data")
                        else:
                            print(f"Data preview: {first_line[:100]}")

                except Exception as e:
                    print(f"Error downloading {file_info['filename']}: {e}")

    def generate_file_report(self):
        """Generate a report of all available NAV files"""
        all_files = []

        for nav_type in ['D', 'N']:
            files = self.get_nav_file_list(nav_type)
            all_files.extend(files)

        if all_files:
            df = pd.DataFrame(all_files)
            report_path = Path("TEMP/NAV_File_Report.csv")
            df.to_csv(report_path, index=False)
            print(f"\nFile report saved to: {report_path}")
            print(f"Total files found: {len(all_files)}")

            # Show summary by type
            type_counts = df['type'].value_counts()
            print("\nFiles by type:")
            for nav_type, count in type_counts.items():
                print(f"  NAV {nav_type}: {count} files")

        return all_files

def main():
    finder = NAVFileFinder()

    print("Florida NAV File Discovery Tool")
    print("=" * 40)

    # Generate file report
    files = finder.generate_file_report()

    if files:
        print(f"\nDownloading sample files...")
        finder.download_sample_files(max_files=3)
    else:
        print("\nNo NAV files found. The Florida Revenue site structure may have changed.")

if __name__ == "__main__":
    main()