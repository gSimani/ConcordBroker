"""
Comprehensive attempt to download full Sunbiz officer dataset
Tries multiple methods and reports findings
"""

import sys
import io
import os
import requests
import subprocess
import ftplib
import socket
import time
import json
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class ComprehensiveDataDownloader:
    """Try every possible method to get officer data"""
    
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.findings = []
        self.successful_downloads = []
        
    def log_finding(self, method: str, success: bool, details: str):
        """Log findings for report"""
        self.findings.append({
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'success': success,
            'details': details
        })
        
    def method1_direct_ftp(self) -> bool:
        """Try direct FTP connection"""
        print("\n" + "=" * 60)
        print("METHOD 1: DIRECT FTP CONNECTION")
        print("=" * 60)
        
        try:
            print("Attempting FTP connection to ftp.dos.state.fl.us...")
            
            # Set timeout
            socket.setdefaulttimeout(10)
            
            # Try connection
            ftp = ftplib.FTP()
            ftp.connect('ftp.dos.state.fl.us', 21, timeout=10)
            ftp.login()  # Anonymous login
            
            # Navigate to officer directory
            ftp.cwd('/public/doc/off/')
            
            # List files
            files = []
            ftp.retrlines('LIST', lambda x: files.append(x))
            
            print(f"✅ SUCCESS! Found {len(files)} files in /off/ directory")
            
            # Download first file
            if files:
                first_file = files[0].split()[-1]
                local_file = self.base_path / first_file
                
                with open(local_file, 'wb') as f:
                    ftp.retrbinary(f'RETR {first_file}', f.write)
                
                self.successful_downloads.append(local_file)
                self.log_finding("Direct FTP", True, f"Downloaded {len(files)} files available")
                
            ftp.quit()
            return True
            
        except socket.timeout:
            print("❌ Connection timeout - likely blocked by firewall")
            self.log_finding("Direct FTP", False, "Connection timeout - firewall blocking")
        except Exception as e:
            print(f"❌ FTP failed: {e}")
            self.log_finding("Direct FTP", False, str(e))
        
        return False
    
    def method2_http_mirrors(self) -> bool:
        """Try HTTP mirrors of FTP site"""
        print("\n" + "=" * 60)
        print("METHOD 2: HTTP MIRRORS")
        print("=" * 60)
        
        mirrors = [
            "http://ftp.dos.state.fl.us/public/doc/off/",
            "http://199.242.69.68/public/doc/off/",  # Direct IP
            "https://ftp.dos.state.fl.us/public/doc/off/",
            "http://floridasunbiz.gov/data/off/",
            "http://dos.myflorida.com/sunbiz/data/off/",
            "http://search.sunbiz.org/data/off/"
        ]
        
        for mirror in mirrors:
            try:
                print(f"Trying: {mirror}")
                response = requests.get(mirror, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check if it's a directory listing
                    if 'Index of' in content or '<a href=' in content.lower():
                        print(f"✅ SUCCESS! Found directory listing at {mirror}")
                        
                        # Parse for .txt files
                        import re
                        file_pattern = r'href="([^"]+\.(txt|zip))"'
                        matches = re.findall(file_pattern, content, re.IGNORECASE)
                        
                        if matches:
                            print(f"Found {len(matches)} data files")
                            
                            # Try to download first file
                            first_file = matches[0][0]
                            file_url = mirror + first_file
                            
                            print(f"Downloading {first_file}...")
                            file_response = requests.get(file_url, timeout=30)
                            
                            if file_response.status_code == 200:
                                local_file = self.base_path / first_file
                                with open(local_file, 'wb') as f:
                                    f.write(file_response.content)
                                
                                self.successful_downloads.append(local_file)
                                self.log_finding("HTTP Mirror", True, f"Working mirror: {mirror}")
                                return True
                        
                    self.log_finding("HTTP Mirror", False, f"{mirror} - No directory listing")
                    
                elif response.status_code == 403:
                    print(f"  ❌ Access forbidden")
                    self.log_finding("HTTP Mirror", False, f"{mirror} - Access forbidden")
                else:
                    print(f"  ❌ Status {response.status_code}")
                    self.log_finding("HTTP Mirror", False, f"{mirror} - Status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  ❌ Timeout")
                self.log_finding("HTTP Mirror", False, f"{mirror} - Timeout")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.log_finding("HTTP Mirror", False, f"{mirror} - {str(e)}")
        
        return False
    
    def method3_wget_powershell(self) -> bool:
        """Use PowerShell's Invoke-WebRequest"""
        print("\n" + "=" * 60)
        print("METHOD 3: POWERSHELL INVOKE-WEBREQUEST")
        print("=" * 60)
        
        try:
            # Test with PowerShell
            ps_command = """
            $url = 'ftp://ftp.dos.state.fl.us/public/doc/off/'
            try {
                $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 10
                $response.Content
            } catch {
                Write-Host "Error: $_"
            }
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout:
                print("✅ PowerShell connected!")
                self.log_finding("PowerShell", True, "Can connect via PowerShell")
                
                # Try to download a specific file
                download_ps = """
                $url = 'ftp://ftp.dos.state.fl.us/public/doc/off/OFFP0001.txt'
                $output = 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE\\doc\\OFFP0001.txt'
                Invoke-WebRequest -Uri $url -OutFile $output -TimeoutSec 30
                """
                
                dl_result = subprocess.run(
                    ['powershell', '-Command', download_ps],
                    capture_output=True,
                    text=True,
                    timeout=35
                )
                
                if dl_result.returncode == 0:
                    test_file = self.base_path / "OFFP0001.txt"
                    if test_file.exists():
                        self.successful_downloads.append(test_file)
                        print(f"✅ Downloaded test file: {test_file}")
                        return True
            else:
                print(f"❌ PowerShell failed: {result.stderr}")
                self.log_finding("PowerShell", False, "Cannot connect via PowerShell")
                
        except Exception as e:
            print(f"❌ PowerShell error: {e}")
            self.log_finding("PowerShell", False, str(e))
        
        return False
    
    def method4_python_urllib(self) -> bool:
        """Use Python's urllib with different user agents"""
        print("\n" + "=" * 60)
        print("METHOD 4: PYTHON URLLIB WITH USER AGENTS")
        print("=" * 60)
        
        urls_to_try = [
            'ftp://ftp.dos.state.fl.us/public/doc/off/',
            'http://ftp.dos.state.fl.us/public/doc/off/',
            'ftp://199.242.69.68/public/doc/off/'
        ]
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Wget/1.21.3',
            'curl/7.68.0',
            None  # No user agent
        ]
        
        for url in urls_to_try:
            for ua in user_agents:
                try:
                    print(f"Trying {url} with UA: {ua or 'default'}")
                    
                    req = urllib.request.Request(url)
                    if ua:
                        req.add_header('User-Agent', ua)
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        content = response.read()
                        
                        if content:
                            print(f"✅ SUCCESS with {url}")
                            
                            # Save directory listing
                            listing_file = self.base_path / "directory_listing.html"
                            with open(listing_file, 'wb') as f:
                                f.write(content)
                            
                            self.log_finding("urllib", True, f"Got listing from {url}")
                            return True
                            
                except urllib.error.URLError as e:
                    print(f"  ❌ URL Error: {e.reason}")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
        
        self.log_finding("urllib", False, "All attempts failed")
        return False
    
    def method5_third_party_apis(self) -> bool:
        """Try third-party data sources"""
        print("\n" + "=" * 60)
        print("METHOD 5: THIRD-PARTY APIS")
        print("=" * 60)
        
        # OpenCorporates
        print("\n1. OpenCorporates API...")
        try:
            url = "https://api.opencorporates.com/v0.4/companies/search"
            params = {
                "q": "LLC",
                "jurisdiction_code": "us_fl",
                "per_page": 5,
                "order": "created_at"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('results', {}).get('total_count', 0)
                
                if total > 0:
                    print(f"✅ OpenCorporates has {total:,} Florida companies")
                    
                    # Check if officers are available
                    companies = data.get('results', {}).get('companies', [])
                    if companies:
                        first_company = companies[0]['company']
                        company_num = first_company.get('company_number')
                        
                        # Try to get officers
                        officer_url = f"https://api.opencorporates.com/v0.4/companies/us_fl/{company_num}"
                        officer_resp = requests.get(officer_url, timeout=10)
                        
                        if officer_resp.status_code == 200:
                            company_data = officer_resp.json()
                            officers = company_data.get('results', {}).get('company', {}).get('officers', [])
                            
                            if officers:
                                print(f"  ✅ Officer data available!")
                                self.log_finding("OpenCorporates", True, f"Has {total} companies with officer data")
                                return True
                            else:
                                print(f"  ⚠️ No officer data in free tier")
                                self.log_finding("OpenCorporates", False, "Officer data requires paid plan")
                                
        except Exception as e:
            print(f"  ❌ OpenCorporates error: {e}")
            self.log_finding("OpenCorporates", False, str(e))
        
        # Data.gov
        print("\n2. Data.gov datasets...")
        try:
            catalog_url = "https://catalog.data.gov/api/3/action/package_search"
            params = {
                "q": "florida business corporations officers",
                "rows": 10
            }
            
            response = requests.get(catalog_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    count = data.get('result', {}).get('count', 0)
                    print(f"  Found {count} related datasets on Data.gov")
                    
                    if count > 0:
                        self.log_finding("Data.gov", True, f"Found {count} related datasets")
                        
        except Exception as e:
            print(f"  ❌ Data.gov error: {e}")
        
        return False
    
    def method6_check_cache_locations(self) -> bool:
        """Check common cache and download locations"""
        print("\n" + "=" * 60)
        print("METHOD 6: CHECK LOCAL CACHE/DOWNLOADS")
        print("=" * 60)
        
        # Common locations where data might be cached
        locations = [
            Path(os.path.expanduser("~/Downloads")),
            Path(os.path.expanduser("~/Documents")),
            Path("C:/Data"),
            Path("C:/Temp"),
            Path("D:/Data"),
            self.base_path.parent,
            Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\florida_data"),
            Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\sunbiz_data")
        ]
        
        found_files = []
        
        for location in locations:
            if location.exists():
                # Look for officer files
                patterns = ['*off*.txt', '*OFF*.txt', '*officer*.txt', '*OFFICER*.txt', 
                           '*director*.txt', '*DIRECTOR*.txt', 'annual*.txt', 'ANNUAL*.txt']
                
                for pattern in patterns:
                    matches = list(location.glob(pattern))
                    if matches:
                        found_files.extend(matches)
        
        if found_files:
            print(f"✅ Found {len(found_files)} potential officer files locally!")
            for f in found_files[:5]:
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  - {f.name} ({size_mb:.1f} MB) in {f.parent}")
            
            self.successful_downloads.extend(found_files)
            self.log_finding("Local Cache", True, f"Found {len(found_files)} existing files")
            return True
        else:
            print("❌ No cached officer data found locally")
            self.log_finding("Local Cache", False, "No existing files found")
        
        return False
    
    def method7_curl_with_options(self) -> bool:
        """Try curl with various options"""
        print("\n" + "=" * 60)
        print("METHOD 7: CURL WITH ADVANCED OPTIONS")
        print("=" * 60)
        
        curl_commands = [
            # Try passive mode
            ['curl', '--ftp-pasv', '-l', 'ftp://ftp.dos.state.fl.us/public/doc/off/'],
            # Try with specific port
            ['curl', '--ftp-port', '-', 'ftp://ftp.dos.state.fl.us/public/doc/off/'],
            # Try HTTP version
            ['curl', '-L', 'http://ftp.dos.state.fl.us/public/doc/off/'],
            # Try with proxy settings
            ['curl', '--noproxy', '*', 'ftp://ftp.dos.state.fl.us/public/doc/off/']
        ]
        
        for cmd in curl_commands:
            try:
                print(f"Trying: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0 and result.stdout:
                    # Check if we got a listing
                    if '.txt' in result.stdout or '.zip' in result.stdout:
                        print("✅ Got file listing!")
                        
                        # Save the listing
                        listing_file = self.base_path / "curl_listing.txt"
                        with open(listing_file, 'w') as f:
                            f.write(result.stdout)
                        
                        self.log_finding("curl", True, f"Command worked: {' '.join(cmd)}")
                        
                        # Parse files and try to download one
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if '.txt' in line:
                                parts = line.split()
                                if parts:
                                    filename = parts[-1]
                                    if '.txt' in filename:
                                        # Try to download this file
                                        dl_cmd = ['curl', '-o', str(self.base_path / filename),
                                                 f'ftp://ftp.dos.state.fl.us/public/doc/off/{filename}']
                                        
                                        dl_result = subprocess.run(dl_cmd, capture_output=True, timeout=30)
                                        if dl_result.returncode == 0:
                                            self.successful_downloads.append(self.base_path / filename)
                                            print(f"✅ Downloaded {filename}")
                                            return True
                                        break
                        
                else:
                    print(f"  ❌ Failed or no output")
                    
            except subprocess.TimeoutExpired:
                print(f"  ❌ Timeout")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        self.log_finding("curl advanced", False, "All curl attempts failed")
        return False
    
    def generate_report(self):
        """Generate comprehensive report of findings"""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE DOWNLOAD ATTEMPT REPORT")
        print("=" * 60)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # Summary
        successful = [f for f in self.findings if f['success']]
        failed = [f for f in self.findings if not f['success']]
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total methods tried: {len(self.findings)}")
        print(f"  ✅ Successful: {len(successful)}")
        print(f"  ❌ Failed: {len(failed)}")
        print(f"  📁 Files downloaded: {len(self.successful_downloads)}")
        
        # Successful methods
        if successful:
            print(f"\n✅ SUCCESSFUL METHODS:")
            for finding in successful:
                print(f"  - {finding['method']}: {finding['details']}")
        
        # Failed methods
        print(f"\n❌ FAILED METHODS:")
        for finding in failed:
            print(f"  - {finding['method']}: {finding['details']}")
        
        # Downloaded files
        if self.successful_downloads:
            print(f"\n📁 DOWNLOADED FILES:")
            for file in self.successful_downloads:
                if file.exists():
                    size = file.stat().st_size
                    print(f"  - {file.name} ({size:,} bytes)")
        
        # Network diagnostics
        print(f"\n🔍 NETWORK DIAGNOSTICS:")
        
        # Check DNS resolution
        try:
            import socket
            ip = socket.gethostbyname('ftp.dos.state.fl.us')
            print(f"  ✅ DNS resolves to: {ip}")
        except:
            print(f"  ❌ DNS resolution failed")
        
        # Check if port 21 is blocked
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('ftp.dos.state.fl.us', 21))
            if result == 0:
                print(f"  ✅ Port 21 (FTP) is open")
            else:
                print(f"  ❌ Port 21 (FTP) is blocked (error code: {result})")
            sock.close()
        except:
            print(f"  ❌ Cannot test port 21")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if not successful:
            print("  1. FTP access is blocked by firewall/network policy")
            print("  2. HTTP mirrors are not publicly accessible")
            print("  3. Consider these alternatives:")
            print("     - Use a VPN service to bypass network restrictions")
            print("     - Deploy to a cloud server (AWS EC2, Google Cloud, Azure)")
            print("     - Contact sunbiz@dos.myflorida.com for bulk data access")
            print("     - Use Supabase Edge Functions with proper deployment")
            print("     - Try downloading from a different network/location")
        else:
            print("  ✅ Some methods worked! Use these for full download:")
            for finding in successful:
                print(f"     - {finding['method']}")
        
        # Save report
        report_file = self.base_path / f"download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_attempts': len(self.findings),
                    'successful': len(successful),
                    'failed': len(failed),
                    'files_downloaded': len(self.successful_downloads)
                },
                'findings': self.findings,
                'downloaded_files': [str(f) for f in self.successful_downloads]
            }, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")
    
    def run_all_methods(self):
        """Run all download methods and generate report"""
        print("=" * 60)
        print("ATTEMPTING TO DOWNLOAD FULL OFFICER DATASET")
        print("=" * 60)
        print("Testing all available methods...")
        
        # Run methods in order of likelihood
        methods = [
            self.method6_check_cache_locations,  # Check local first
            self.method2_http_mirrors,           # Try HTTP
            self.method3_wget_powershell,        # PowerShell
            self.method7_curl_with_options,      # Curl variants
            self.method1_direct_ftp,              # Direct FTP
            self.method4_python_urllib,           # urllib
            self.method5_third_party_apis         # APIs
        ]
        
        for method in methods:
            try:
                if method():
                    print(f"✅ Method successful!")
                    # Don't break - try all methods for comprehensive report
            except Exception as e:
                print(f"❌ Method failed with error: {e}")
        
        # Generate final report
        self.generate_report()

if __name__ == "__main__":
    downloader = ComprehensiveDataDownloader()
    downloader.run_all_methods()