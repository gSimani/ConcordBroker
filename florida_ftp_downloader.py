"""
Florida Revenue FTP Downloader
Downloads property data files from Florida Department of Revenue FTP server
"""

import os
import ftplib
import zipfile
import time
from pathlib import Path
from datetime import datetime
import json

class FloridaFTPDownloader:
    def __init__(self):
        # FTP server details for Florida Department of Revenue
        self.ftp_host = "sdrftp03.dor.state.fl.us"
        self.ftp_user = "anonymous"
        self.ftp_pass = ""
        
        self.root_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.download_log = []
        
        # Florida counties
        self.counties = [
            "ALACHUA", "BAKER", "BAY", "BRADFORD", "BREVARD", "BROWARD",
            "CALHOUN", "CHARLOTTE", "CITRUS", "CLAY", "COLLIER", "COLUMBIA",
            "DESOTO", "DIXIE", "DUVAL", "ESCAMBIA", "FLAGLER", "FRANKLIN",
            "GADSDEN", "GILCHRIST", "GLADES", "GULF", "HAMILTON", "HARDEE",
            "HENDRY", "HERNANDO", "HIGHLANDS", "HILLSBOROUGH", "HOLMES", "INDIAN RIVER",
            "JACKSON", "JEFFERSON", "LAFAYETTE", "LAKE", "LEE", "LEON",
            "LEVY", "LIBERTY", "MADISON", "MANATEE", "MARION", "MARTIN",
            "MIAMI-DADE", "MONROE", "NASSAU", "OKALOOSA", "OKEECHOBEE", "ORANGE",
            "OSCEOLA", "PALM BEACH", "PASCO", "PINELLAS", "POLK", "PUTNAM",
            "SANTA ROSA", "SARASOTA", "SEMINOLE", "ST. JOHNS", "ST. LUCIE", "SUMTER",
            "SUWANNEE", "TAYLOR", "UNION", "VOLUSIA", "WAKULLA", "WALTON", "WASHINGTON"
        ]
        
        # File types
        self.file_types = ["NAL", "NAP", "NAV", "SDF"]
        
        print(f"[INIT] FTP Server: {self.ftp_host}")
        print(f"[INIT] Root directory: {self.root_dir}")
        
    def connect_ftp(self):
        """Connect to the FTP server"""
        try:
            print(f"\n[FTP] Connecting to {self.ftp_host}...")
            ftp = ftplib.FTP(self.ftp_host)
            ftp.login(self.ftp_user, self.ftp_pass)
            print(f"[FTP] Connected successfully")
            
            # List root directory
            print(f"[FTP] Listing root directory...")
            files = []
            ftp.dir(files.append)
            
            print(f"[FTP] Found {len(files)} items in root:")
            for f in files[:10]:  # Show first 10
                print(f"  {f}")
            
            return ftp
            
        except Exception as e:
            print(f"[ERROR] FTP connection failed: {e}")
            return None
    
    def explore_ftp_structure(self, ftp):
        """Explore the FTP directory structure to find property data files"""
        print("\n[EXPLORE] Exploring FTP structure...")
        
        try:
            # Common FTP paths for Florida property data
            paths_to_check = [
                "/",
                "/Tax Roll Data Files",
                "/Tax_Roll_Data_Files",
                "/TAXROLL",
                "/TaxRoll",
                "/Data",
                "/PropertyData",
                "/NAL",
                "/NAP",
                "/NAV", 
                "/SDF"
            ]
            
            for path in paths_to_check:
                try:
                    print(f"\n[CHECK] Checking path: {path}")
                    ftp.cwd(path)
                    
                    # List directory
                    files = []
                    ftp.nlst(files.append)
                    
                    if files:
                        print(f"  Found {len(files)} items:")
                        for f in files[:5]:
                            print(f"    - {f}")
                        
                        # Check for county files
                        for county in self.counties[:3]:  # Test with first 3
                            for file_type in self.file_types:
                                patterns = [
                                    f"{county}_{file_type}_2025.zip",
                                    f"{county}_{file_type}_2025P.zip",
                                    f"{county}_{file_type}_2024.zip",
                                    f"{county}_{file_type}.zip"
                                ]
                                
                                for pattern in patterns:
                                    if any(pattern.upper() in f.upper() for f in files):
                                        print(f"  [FOUND] {pattern}")
                                        return path
                        
                except ftplib.error_perm:
                    continue
            
            # Try going into year folders
            current_year = "2025"
            year_paths = [
                f"/{current_year}",
                f"/{current_year}P",
                "/2024",
                "/Current"
            ]
            
            for year_path in year_paths:
                try:
                    print(f"\n[CHECK] Checking year path: {year_path}")
                    ftp.cwd(year_path)
                    
                    # List directory
                    files = []
                    ftp.nlst(files.append)
                    
                    if files:
                        print(f"  Found {len(files)} items")
                        return year_path
                        
                except ftplib.error_perm:
                    continue
            
        except Exception as e:
            print(f"[ERROR] Failed to explore FTP: {e}")
        
        return None
    
    def download_file(self, ftp, remote_file, local_path):
        """Download a file from FTP server"""
        try:
            print(f"  [DOWNLOAD] {remote_file}...")
            
            # Create local file
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
            
            file_size = os.path.getsize(local_path)
            print(f"  [OK] Downloaded {file_size:,} bytes")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Download failed: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            return False
    
    def extract_zip(self, zip_path, extract_to):
        """Extract a ZIP file and remove the archive"""
        try:
            print(f"  [EXTRACT] Extracting {zip_path.name}...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                extracted = zip_ref.namelist()
                print(f"  [EXTRACTED] {len(extracted)} files")
            
            # Remove ZIP file
            zip_path.unlink()
            print(f"  [CLEANUP] Removed ZIP file")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Extraction failed: {e}")
            return False
    
    def download_county_files(self, ftp, county):
        """Download all file types for a county"""
        county_code = county.replace(" ", "_").replace(".", "")
        
        for file_type in self.file_types:
            print(f"\n[{county}] Downloading {file_type}...")
            
            # Try different file name patterns
            patterns = [
                f"{county_code}_{file_type}_2025.zip",
                f"{county_code}_{file_type}_2025P.zip",
                f"{county_code}_{file_type}_2024.zip",
                f"{county_code}_{file_type}.zip",
                f"{county_code.lower()}_{file_type.lower()}_2025.zip",
                f"{county_code.upper()}_{file_type.upper()}_2025.ZIP"
            ]
            
            local_dir = self.root_dir / county / file_type
            local_dir.mkdir(parents=True, exist_ok=True)
            
            downloaded = False
            for pattern in patterns:
                try:
                    # Check if file exists on FTP
                    files = []
                    ftp.nlst(files.append)
                    
                    if pattern in files or pattern.upper() in [f.upper() for f in files]:
                        # Download the file
                        local_path = local_dir / pattern
                        
                        if self.download_file(ftp, pattern, local_path):
                            # Extract if it's a ZIP
                            if pattern.endswith('.zip') or pattern.endswith('.ZIP'):
                                self.extract_zip(local_path, local_dir)
                            
                            self.download_log.append({
                                'timestamp': datetime.now().isoformat(),
                                'county': county,
                                'file_type': file_type,
                                'file_name': pattern,
                                'status': 'success'
                            })
                            
                            downloaded = True
                            break
                            
                except Exception as e:
                    continue
            
            if not downloaded:
                print(f"  [NOT FOUND] No {file_type} file for {county}")
                self.download_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'county': county,
                    'file_type': file_type,
                    'status': 'not_found'
                })
    
    def run(self):
        """Main execution"""
        print("="*70)
        print("FLORIDA REVENUE FTP DOWNLOADER")
        print("="*70)
        
        # Connect to FTP
        ftp = self.connect_ftp()
        if not ftp:
            print("[ABORT] Could not connect to FTP server")
            return
        
        try:
            # Explore structure
            data_path = self.explore_ftp_structure(ftp)
            
            if data_path:
                print(f"\n[PATH] Found data at: {data_path}")
                ftp.cwd(data_path)
            
            # Download files for each county
            for i, county in enumerate(self.counties, 1):
                print(f"\n{'='*50}")
                print(f"[{i}/{len(self.counties)}] Processing {county}")
                print('='*50)
                
                self.download_county_files(ftp, county)
                
                # Be nice to the server
                time.sleep(1)
            
        finally:
            ftp.quit()
            print("\n[FTP] Connection closed")
        
        # Save log
        log_file = self.root_dir / f"ftp_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'ftp_server': self.ftp_host,
                'counties_processed': len(self.counties),
                'file_types': self.file_types,
                'downloads': self.download_log
            }, f, indent=2)
        
        print(f"\n[LOG] Saved to: {log_file}")
        
        # Summary
        successful = sum(1 for log in self.download_log if log['status'] == 'success')
        not_found = sum(1 for log in self.download_log if log['status'] == 'not_found')
        
        print("\n" + "="*70)
        print("DOWNLOAD SUMMARY")
        print("="*70)
        print(f"[SUCCESS] {successful} files downloaded")
        print(f"[NOT FOUND] {not_found} files not found")
        print(f"[LOCATION] {self.root_dir}")

if __name__ == "__main__":
    downloader = FloridaFTPDownloader()
    downloader.run()