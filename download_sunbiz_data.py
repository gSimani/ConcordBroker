"""
Download Sunbiz corporate data from Florida Department of State SFTP
"""

import os
import sys
import paramiko
import time
from datetime import datetime

# Sunbiz SFTP credentials
SFTP_HOST = "sftp.floridados.gov"
SFTP_USER = "Public"
SFTP_PASS = "PubAccess1845!"

def connect_sftp():
    """Connect to Sunbiz SFTP server"""
    print("Connecting to Sunbiz SFTP...")
    
    try:
        transport = paramiko.Transport((SFTP_HOST, 22))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("Connected successfully!")
        return sftp, transport
    except Exception as e:
        print(f"Connection failed: {e}")
        return None, None

def explore_sftp_structure(sftp):
    """Explore the SFTP directory structure"""
    print("\nExploring SFTP directory structure...")
    
    try:
        # List root directory
        print("\nRoot directory contents:")
        root_files = sftp.listdir('.')
        for item in root_files[:20]:  # Show first 20 items
            try:
                stat = sftp.stat(item)
                size = stat.st_size
                if size > 0:
                    print(f"  {item} - {size:,} bytes")
            except:
                print(f"  {item}")
        
        # Look for data directories
        data_dirs = ['data', 'Data', 'DATA', 'corporate', 'Corporate', 'CORPORATE']
        for dir_name in data_dirs:
            try:
                files = sftp.listdir(dir_name)
                print(f"\n{dir_name}/ directory found! Contents:")
                for f in files[:10]:
                    print(f"  {f}")
                break
            except:
                continue
                
    except Exception as e:
        print(f"Error exploring: {e}")

def download_file_with_retry(sftp, remote_path, local_path, max_retries=3):
    """Download a file with retries"""
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}: Downloading {remote_path}...")
            
            # Get file size first
            stat = sftp.stat(remote_path)
            file_size = stat.st_size
            print(f"    File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
            
            if file_size == 0:
                print(f"    Skipping - file is empty")
                return False
            
            # Download the file
            sftp.get(remote_path, local_path)
            
            # Verify download
            local_size = os.path.getsize(local_path)
            if local_size == file_size:
                print(f"    Success! Downloaded {local_size:,} bytes")
                return True
            else:
                print(f"    Size mismatch: expected {file_size}, got {local_size}")
                os.remove(local_path)
                
        except Exception as e:
            print(f"    Error: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            
        if attempt < max_retries - 1:
            print("    Retrying in 5 seconds...")
            time.sleep(5)
    
    return False

def find_and_download_files(sftp):
    """Find and download Sunbiz data files"""
    print("\nSearching for Sunbiz data files...")
    
    # Create download directory
    os.makedirs('sunbiz_data', exist_ok=True)
    
    # Files we're looking for
    target_files = {
        'cordata.zip': 'Corporate entities data',
        'corevent.zip': 'Corporate events',
        'ficdata.zip': 'Fictitious names (DBAs)',
        'ficevt.zip': 'Fictitious name events',
        'genfile.zip': 'General partnerships',
        'genevt.zip': 'Partnership events',
        'TMData.zip': 'Trademarks'
    }
    
    downloaded = []
    
    # Search in root and common subdirectories
    search_paths = ['.', 'data', 'Data', 'public', 'Public']
    
    for search_dir in search_paths:
        print(f"\nSearching in {search_dir}/...")
        try:
            if search_dir == '.':
                files = sftp.listdir()
            else:
                files = sftp.listdir(search_dir)
            
            for filename in files:
                # Check if it's one of our target files
                for target, description in target_files.items():
                    if filename.lower() == target.lower():
                        if search_dir == '.':
                            remote_path = filename
                        else:
                            remote_path = f"{search_dir}/{filename}"
                        
                        local_path = f"sunbiz_data/{target}"
                        
                        print(f"\nFound {description}: {remote_path}")
                        if download_file_with_retry(sftp, remote_path, local_path):
                            downloaded.append((target, local_path))
                        break
                        
        except Exception as e:
            if "No such file" not in str(e):
                print(f"  Could not access {search_dir}: {e}")
    
    return downloaded

def main():
    print("SUNBIZ DATA DOWNLOADER")
    print("=" * 60)
    
    # Connect to SFTP
    sftp, transport = connect_sftp()
    
    if not sftp:
        print("Failed to connect to SFTP server")
        return
    
    try:
        # Explore structure
        explore_sftp_structure(sftp)
        
        # Download files
        downloaded_files = find_and_download_files(sftp)
        
        print("\n" + "=" * 60)
        if downloaded_files:
            print(f"Successfully downloaded {len(downloaded_files)} files:")
            for filename, path in downloaded_files:
                size = os.path.getsize(path)
                print(f"  - {filename}: {size:,} bytes")
        else:
            print("No files were downloaded successfully")
            print("\nNote: The files might require special access or be in a different location.")
            print("You may need to:")
            print("1. Check if files are available only during certain times")
            print("2. Use a different SFTP account with more permissions")
            print("3. Download files manually from the Florida DOS website")
            
    finally:
        sftp.close()
        transport.close()
        print("\nConnection closed")

if __name__ == "__main__":
    # Install paramiko if needed
    try:
        import paramiko
    except ImportError:
        print("Installing paramiko...")
        os.system("pip install paramiko")
        import paramiko
    
    main()