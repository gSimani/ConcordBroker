"""
Comprehensive exploration of ALL data on Florida DOS SFTP server
Find and download complete officer/email datasets
"""

import sys
import io
import paramiko
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class ComprehensiveSFTPExplorer:
    def __init__(self):
        self.sftp_host = "sftp.floridados.gov"
        self.sftp_username = "Public"
        self.sftp_password = "PubAccess1845!"
        
    def explore_all_directories(self):
        """Comprehensive exploration of all directories"""
        print("=" * 70)
        print("COMPREHENSIVE SFTP DATA EXPLORATION")
        print("=" * 70)
        
        try:
            # Connect
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=self.sftp_host,
                port=22,
                username=self.sftp_username,
                password=self.sftp_password,
                timeout=30
            )
            
            sftp = ssh.open_sftp()
            print("✅ Connected to SFTP\n")
            
            # Start comprehensive exploration
            all_files = {}
            
            def explore_directory(path="/", level=0, max_depth=4):
                """Recursively explore with focus on officer data"""
                if level > max_depth:
                    return
                
                try:
                    items = sftp.listdir_attr(path)
                    indent = "  " * level
                    
                    print(f"{indent}📁 {path} ({len(items)} items)")
                    
                    # Track files by type
                    officer_files = []
                    annual_files = []
                    corporate_files = []
                    quarterly_files = []
                    other_files = []
                    
                    for item in items:
                        try:
                            full_path = f"{path.rstrip('/')}/{item.filename}"
                            is_dir = item.st_mode & 0o040000 != 0
                            
                            if is_dir:
                                print(f"{indent}  📂 {item.filename}/")
                                # Recursively explore important directories
                                if any(keyword in item.filename.lower() for keyword in 
                                      ['off', 'officer', 'annual', 'cor', 'quarterly', 'ag', 'principal']):
                                    print(f"{indent}     ⭐ Contains potential officer data!")
                                    explore_directory(full_path, level + 1, max_depth)
                                elif level < 2:  # Explore first 2 levels of everything
                                    explore_directory(full_path, level + 1, max_depth)
                            else:
                                size_mb = item.st_size / (1024 * 1024)
                                filename_lower = item.filename.lower()
                                
                                # Categorize files
                                file_info = {
                                    'path': full_path,
                                    'size_mb': size_mb,
                                    'filename': item.filename
                                }
                                
                                if 'off' in filename_lower or 'officer' in filename_lower:
                                    officer_files.append(file_info)
                                    print(f"{indent}  📄 {item.filename} ({size_mb:.1f} MB) ⭐ OFFICER DATA!")
                                elif 'annual' in filename_lower:
                                    annual_files.append(file_info)
                                    print(f"{indent}  📄 {item.filename} ({size_mb:.1f} MB) ⭐ ANNUAL DATA!")
                                elif 'corp' in filename_lower and size_mb > 50:
                                    corporate_files.append(file_info)
                                    print(f"{indent}  📄 {item.filename} ({size_mb:.1f} MB) ⭐ CORPORATE DATA!")
                                elif 'quarterly' in path.lower() or 'quarter' in filename_lower:
                                    quarterly_files.append(file_info)
                                    print(f"{indent}  📄 {item.filename} ({size_mb:.1f} MB) ⭐ QUARTERLY DATA!")
                                elif size_mb > 10:  # Show large files
                                    other_files.append(file_info)
                                    print(f"{indent}  📄 {item.filename} ({size_mb:.1f} MB)")
                            
                        except Exception as e:
                            print(f"{indent}  ❌ Error with {item.filename}: {e}")
                    
                    # Store categorized files
                    if officer_files or annual_files or corporate_files or quarterly_files:
                        all_files[path] = {
                            'officer': officer_files,
                            'annual': annual_files,
                            'corporate': corporate_files,
                            'quarterly': quarterly_files,
                            'other': other_files
                        }
                        
                except Exception as e:
                    print(f"{indent}❌ Cannot access {path}: {e}")
            
            # Start exploration
            explore_directory("/", max_depth=4)
            
            # Summary of findings
            print("\n" + "=" * 70)
            print("SUMMARY OF OFFICER/EMAIL DATA SOURCES")
            print("=" * 70)
            
            total_officer_files = 0
            total_annual_files = 0
            total_corporate_files = 0
            total_quarterly_files = 0
            
            priority_downloads = []
            
            for path, files in all_files.items():
                if files['officer'] or files['annual'] or files['corporate'] or files['quarterly']:
                    print(f"\n📁 {path}:")
                    
                    if files['officer']:
                        total_officer_files += len(files['officer'])
                        print(f"  ⭐ {len(files['officer'])} OFFICER files (likely has emails!)")
                        priority_downloads.extend(files['officer'])
                        
                    if files['annual']:
                        total_annual_files += len(files['annual'])
                        print(f"  📋 {len(files['annual'])} Annual report files")
                        priority_downloads.extend(files['annual'])
                        
                    if files['corporate']:
                        total_corporate_files += len(files['corporate'])
                        print(f"  🏢 {len(files['corporate'])} Corporate files")
                        priority_downloads.extend(files['corporate'])
                        
                    if files['quarterly']:
                        total_quarterly_files += len(files['quarterly'])
                        print(f"  📊 {len(files['quarterly'])} Quarterly files")
                        priority_downloads.extend(files['quarterly'])
            
            print(f"\n🎯 TOTAL PRIORITY DATA FILES FOUND:")
            print(f"   ⭐ Officer files: {total_officer_files}")
            print(f"   📋 Annual files: {total_annual_files}")
            print(f"   🏢 Corporate files: {total_corporate_files}")
            print(f"   📊 Quarterly files: {total_quarterly_files}")
            print(f"   📦 Total files with potential emails: {len(priority_downloads)}")
            
            # Calculate total size
            total_size_gb = sum(f['size_mb'] for f in priority_downloads) / 1024
            print(f"   💾 Total data size: {total_size_gb:.1f} GB")
            
            # Show top priority files
            print(f"\n🔥 TOP PRIORITY FILES FOR EMAIL EXTRACTION:")
            print("-" * 70)
            
            # Sort by importance: officer files first, then by size
            def file_priority(f):
                filename = f['filename'].lower()
                if 'off' in filename or 'officer' in filename:
                    return (0, -f['size_mb'])  # Highest priority
                elif 'annual' in filename:
                    return (1, -f['size_mb'])
                elif 'corp' in filename and f['size_mb'] > 100:
                    return (2, -f['size_mb'])
                else:
                    return (3, -f['size_mb'])
            
            priority_downloads.sort(key=file_priority)
            
            for i, file_info in enumerate(priority_downloads[:20]):
                priority_num = i + 1
                filename = file_info['filename']
                size_mb = file_info['size_mb']
                path = file_info['path']
                
                # Mark file type
                if 'off' in filename.lower():
                    marker = "⭐ OFFICER"
                elif 'annual' in filename.lower():
                    marker = "📋 ANNUAL"
                elif 'corp' in filename.lower():
                    marker = "🏢 CORPORATE"
                else:
                    marker = "📊 DATA"
                
                print(f"{priority_num:2d}. {marker} - {filename} ({size_mb:.1f} MB)")
                print(f"    Path: {path}")
                
                if i == 19 and len(priority_downloads) > 20:
                    print(f"\n... and {len(priority_downloads) - 20} more files!")
                    break
            
            sftp.close()
            ssh.close()
            
            return priority_downloads
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

def main():
    explorer = ComprehensiveSFTPExplorer()
    priority_files = explorer.explore_all_directories()
    
    if priority_files:
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("📧 Found comprehensive data sources for email extraction!")
        print(f"🎯 {len(priority_files)} priority files identified")
        print("\n💡 Recommendations:")
        print("1. Download officer files first (highest email probability)")
        print("2. Process quarterly/annual data for comprehensive coverage")
        print("3. Use the parallel pipeline for fast processing")
        print("\nRun: python download_all_officer_data.py")
        print("This will download and extract emails from ALL sources!")
    else:
        print("\n❌ No priority data files found")

if __name__ == "__main__":
    main()