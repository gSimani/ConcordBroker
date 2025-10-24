"""
Download County Property Data
Downloads NAL, NAP, NAV, and SDF files for a specific county using Playwright
"""

import asyncio
import argparse
import hashlib
from pathlib import Path
from datetime import date
from playwright.async_api import async_playwright


PORTAL_URL = "https://floridarevenue.com/property/dataportal/"
DATA_DIR = Path(__file__).parent.parent / 'data' / 'raw'


async def download_county_files(county: str, file_types: list = None):
    """Download files for a specific county"""

    if file_types is None:
        file_types = ['NAL', 'NAP', 'NAV', 'SDF']

    county_upper = county.upper()
    year = date.today().year

    print("=" * 80)
    print(f"DOWNLOADING {county_upper} COUNTY DATA")
    print("=" * 80)

    print(f"\n📅 Year: {year}")
    print(f"📁 File types: {', '.join(file_types)}")

    # Create output directory
    output_dir = DATA_DIR / str(date.today())
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Output directory: {output_dir}")

    downloaded_files = []

    async with async_playwright() as p:
        print("\n🤖 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Set download handler
        async def handle_download(download):
            # Save to output directory
            file_path = output_dir / download.suggested_filename
            await download.save_as(file_path)

            # Calculate checksum
            checksum = calculate_checksum(file_path)

            downloaded_files.append({
                'file': file_path,
                'size': file_path.stat().st_size,
                'checksum': checksum
            })

            print(f"   ✅ Downloaded: {file_path.name}")
            print(f"      Size: {file_path.stat().st_size:,} bytes")
            print(f"      MD5: {checksum}")

        page.on("download", handle_download)

        try:
            print("\n📡 Navigating to portal...")
            await page.goto(PORTAL_URL, wait_until='networkidle', timeout=30000)

            # Navigate to Tax Roll Data Files
            print("🔍 Looking for Tax Roll Data Files...")
            tax_roll_link = await page.query_selector("text=/Tax Roll Data Files/i")

            if not tax_roll_link:
                print("❌ Could not find Tax Roll Data Files link")
                print("⚠️  Portal structure may have changed")
                return downloaded_files

            print("✅ Found Tax Roll Data Files")
            await tax_roll_link.click()
            await page.wait_for_load_state('networkidle')

            # Process each file type
            for file_type in file_types:
                print(f"\n📂 Processing {file_type} files...")

                # Navigate to file type folder
                file_type_link = await page.query_selector(f"text=/{file_type}/i")

                if not file_type_link:
                    print(f"   ⚠️  {file_type} folder not found, skipping")
                    continue

                await file_type_link.click()
                await page.wait_for_load_state('networkidle')
                print(f"   ✅ Opened {file_type} folder")

                # Look for county file
                county_pattern = f"{county_upper}.*{year}"
                print(f"   🔍 Looking for: {county_pattern}")

                county_file_link = await page.query_selector(f"text=/{county_pattern}/i")

                if not county_file_link:
                    print(f"   ⚠️  {county_upper} file not found in {file_type}")
                else:
                    print(f"   📥 Downloading {county_upper}_{file_type}_{year}...")
                    await county_file_link.click()

                    # Wait for download to complete
                    await asyncio.sleep(2)

                # Go back to Tax Roll Data Files
                await page.go_back()
                await page.wait_for_load_state('networkidle')

            print("\n" + "=" * 80)
            print("✅ DOWNLOAD COMPLETE")
            print("=" * 80)

            if downloaded_files:
                print(f"\n📊 Downloaded {len(downloaded_files)} files:")
                total_size = sum(f['size'] for f in downloaded_files)

                for f in downloaded_files:
                    print(f"\n   📄 {f['file'].name}")
                    print(f"      Size: {f['size']:,} bytes")
                    print(f"      MD5: {f['checksum']}")

                print(f"\n   Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
            else:
                print("\n⚠️  No files downloaded")
                print("   This could mean:")
                print("   1. Files not available for this county")
                print("   2. Portal structure changed")
                print("   3. Manual download required")

        except Exception as e:
            print(f"\n❌ Error: {e}")

            # Take error screenshot
            error_path = Path(__file__).parent.parent / 'test-screenshots' / f'download-error-{county_upper}.png'
            error_path.parent.mkdir(exist_ok=True)
            await page.screenshot(path=str(error_path))
            print(f"📸 Error screenshot: {error_path}")

        finally:
            print("\n🔚 Closing browser...")
            await browser.close()

    return downloaded_files


def calculate_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of file"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Download Florida County Property Data')
    parser.add_argument('--county', required=True, help='County name (e.g., BROWARD)')
    parser.add_argument('--file-types', nargs='+', default=['NAL', 'NAP', 'NAV', 'SDF'],
                        help='File types to download (default: NAL NAP NAV SDF)')

    args = parser.parse_args()

    # Run download
    downloaded = asyncio.run(download_county_files(args.county, args.file_types))

    if downloaded:
        print("\n✅ Download successful!")
        print("\n💡 Next steps:")
        print("   1. Parse downloaded files: python scripts/parse_county_files.py")
        print("   2. Load into database: python scripts/load_county_data.py")
    else:
        print("\n⚠️  Download incomplete - see messages above")


if __name__ == '__main__':
    main()
