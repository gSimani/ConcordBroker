"""
Florida Revenue NAL Manual Download Helper
This script helps organize manually downloaded NAL files
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import webbrowser

class NALManualHelper:
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.downloads_path = Path.home() / "Downloads"
        
        # County mapping
        self.counties = {
            "01": "ALACHUA", "02": "BAKER", "03": "BAY", "04": "BRADFORD",
            "05": "BREVARD", "06": "BROWARD", "07": "CALHOUN", "08": "CHARLOTTE",
            "09": "CITRUS", "10": "CLAY", "11": "COLLIER", "12": "COLUMBIA",
            "13": "DESOTO", "14": "DIXIE", "15": "DUVAL", "16": "ESCAMBIA",
            "17": "FLAGLER", "18": "FRANKLIN", "19": "GADSDEN", "20": "GILCHRIST",
            "21": "GLADES", "22": "GULF", "23": "HAMILTON", "24": "HARDEE",
            "25": "HENDRY", "26": "HERNANDO", "27": "HIGHLANDS", "28": "HILLSBOROUGH",
            "29": "HOLMES", "30": "INDIAN RIVER", "31": "JACKSON", "32": "JEFFERSON",
            "33": "LAFAYETTE", "34": "LAKE", "35": "LEE", "36": "LEON",
            "37": "LEVY", "38": "LIBERTY", "39": "MADISON", "40": "MANATEE",
            "41": "MARION", "42": "MARTIN", "43": "MIAMI-DADE", "44": "MONROE",
            "45": "NASSAU", "46": "OKALOOSA", "47": "OKEECHOBEE", "48": "ORANGE",
            "49": "OSCEOLA", "50": "PALM BEACH", "51": "PASCO", "52": "PINELLAS",
            "53": "POLK", "54": "PUTNAM", "55": "SANTA ROSA", "56": "SARASOTA",
            "57": "SEMINOLE", "58": "ST. JOHNS", "59": "ST. LUCIE", "60": "SUMTER",
            "61": "SUWANNEE", "62": "TAYLOR", "63": "UNION", "64": "VOLUSIA",
            "65": "WAKULLA", "66": "WALTON", "67": "WASHINGTON"
        }
    
    def open_florida_revenue_site(self):
        """Open the Florida Revenue NAL 2025P page"""
        url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P"
        print("\nOpening Florida Revenue NAL 2025P page...")
        print("="*60)
        print("MANUAL DOWNLOAD INSTRUCTIONS:")
        print("="*60)
        print("1. The browser will open to the NAL 2025P page")
        print("2. You should see a list of Excel files (NAL25P_01.xlsx, etc.)")
        print("3. Download each file by clicking on it")
        print("4. Save all files to your Downloads folder")
        print("5. After downloading all files, come back here and press Enter")
        print("="*60)
        
        webbrowser.open(url)
        input("\nPress Enter after you've downloaded all NAL files...")
    
    def find_nal_files(self):
        """Find all NAL files in Downloads folder"""
        print("\nSearching for NAL files in Downloads folder...")
        nal_files = []
        
        # Look for NAL files
        patterns = ["NAL25P*.xlsx", "NAL25P*.xls", "NAL25P*.zip"]
        for pattern in patterns:
            files = list(self.downloads_path.glob(pattern))
            nal_files.extend(files)
        
        print(f"Found {len(nal_files)} NAL files")
        return nal_files
    
    def extract_county_from_filename(self, filename):
        """Extract county from filename"""
        # Try to extract county code
        if "NAL25P" in filename:
            # Try to find the county code (2 digits after NAL25P_)
            parts = filename.replace("NAL25P_", "").replace("NAL25P", "")
            code = parts[:2] if len(parts) >= 2 else None
            
            if code and code in self.counties:
                return self.counties[code]
        
        # Try to match county name directly
        filename_upper = filename.upper()
        for code, county in self.counties.items():
            if county.replace(" ", "").replace(".", "") in filename_upper:
                return county
        
        return None
    
    def organize_files(self, files):
        """Move files to appropriate county folders"""
        print("\nOrganizing files into county folders...")
        print("="*60)
        
        success_count = 0
        failed_files = []
        
        for file in files:
            filename = file.name
            county = self.extract_county_from_filename(filename)
            
            if county:
                # Create county NAL folder
                county_folder = self.base_path / county / "NAL"
                county_folder.mkdir(parents=True, exist_ok=True)
                
                # Destination path
                dest_path = county_folder / filename
                
                try:
                    # If it's a zip file, extract it
                    if filename.endswith('.zip'):
                        print(f"Extracting {filename} for {county}...")
                        with zipfile.ZipFile(file, 'r') as zip_ref:
                            zip_ref.extractall(county_folder)
                        # Remove the zip file from Downloads
                        file.unlink()
                        print(f"  -> Extracted to {county_folder}")
                    else:
                        # Move the file
                        shutil.move(str(file), str(dest_path))
                        print(f"Moved {filename} -> {county}/NAL/")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"  ERROR: Failed to process {filename}: {e}")
                    failed_files.append(filename)
            else:
                print(f"  WARNING: Could not determine county for {filename}")
                failed_files.append(filename)
        
        return success_count, failed_files
    
    def check_status(self):
        """Check which counties have NAL files"""
        print("\nChecking NAL file status for all counties...")
        print("="*60)
        
        has_files = []
        missing = []
        
        for code, county in self.counties.items():
            county_folder = self.base_path / county / "NAL"
            excel_files = list(county_folder.glob("*.xlsx")) + list(county_folder.glob("*.xls"))
            
            if excel_files:
                has_files.append(county)
            else:
                missing.append(county)
        
        print(f"Counties with NAL files: {len(has_files)}")
        print(f"Counties missing NAL files: {len(missing)}")
        
        if missing and len(missing) <= 10:
            print("\nMissing counties:")
            for county in missing:
                print(f"  - {county}")
        elif missing:
            print(f"\nFirst 10 missing counties:")
            for county in missing[:10]:
                print(f"  - {county}")
            print(f"  ... and {len(missing) - 10} more")
        
        return has_files, missing
    
    def run(self):
        """Main execution"""
        print("Florida Revenue NAL Manual Download Helper")
        print("="*60)
        
        # Check current status
        has_files, missing = self.check_status()
        
        if len(missing) == 0:
            print("\n[SUCCESS] All counties have NAL files!")
            return
        
        print(f"\nNeed to download NAL files for {len(missing)} counties")
        
        # Ask if user wants to open the website
        response = input("\nOpen Florida Revenue website to download files? (y/n): ")
        if response.lower() == 'y':
            self.open_florida_revenue_site()
            
            # Process downloaded files
            nal_files = self.find_nal_files()
            
            if nal_files:
                success, failed = self.organize_files(nal_files)
                
                print("\n" + "="*60)
                print("ORGANIZATION COMPLETE")
                print("="*60)
                print(f"Successfully organized: {success} files")
                if failed:
                    print(f"Failed to organize: {len(failed)} files")
                
                # Check final status
                has_files, missing = self.check_status()
                
                if len(missing) == 0:
                    print("\n[SUCCESS] All counties now have NAL files!")
                else:
                    print(f"\n[INFO] Still missing {len(missing)} counties")
                    print("You may need to download these manually")
            else:
                print("\nNo NAL files found in Downloads folder")
                print("Please download the files manually and run this script again")
        else:
            print("\nPlease download the NAL files manually from:")
            print("https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P")
            print("\nAfter downloading, run this script again to organize the files")


def main():
    helper = NALManualHelper()
    helper.run()


if __name__ == "__main__":
    main()