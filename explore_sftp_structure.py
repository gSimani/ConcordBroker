"""
Explore the actual SFTP directory structure to find the data files
"""

import sys
import io
import paramiko
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def explore_sftp():
    """Deep exploration of SFTP structure"""
    
    print("=" * 60)
    print("EXPLORING SFTP DIRECTORY STRUCTURE")
    print("=" * 60)
    
    # SFTP Credentials
    sftp_host = "sftp.floridados.gov"
    sftp_username = "Public"
    sftp_password = "PubAccess1845!"
    
    try:
        # Connect
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            hostname=sftp_host,
            port=22,
            username=sftp_username,
            password=sftp_password,
            timeout=30,
            look_for_keys=False,
            allow_agent=False
        )
        
        sftp = ssh.open_sftp()
        print("✅ Connected to SFTP\n")
        
        def explore_directory(path="/", level=0, max_depth=3):
            """Recursively explore directories"""
            if level > max_depth:
                return
            
            try:
                items = sftp.listdir_attr(path)
                indent = "  " * level
                
                print(f"{indent}📁 {path} ({len(items)} items)")
                
                for item in items:
                    try:
                        # Get full path
                        if path.endswith('/'):
                            full_path = f"{path}{item.filename}"
                        else:
                            full_path = f"{path}/{item.filename}"
                        
                        # Check if directory (S_ISDIR bit)
                        is_dir = item.st_mode & 0o040000 != 0
                        
                        if is_dir:
                            print(f"{indent}  📂 {item.filename}/")
                            # Explore subdirectory
                            if level < max_depth:
                                explore_directory(full_path, level + 1, max_depth)
                        else:
                            # Show file with size
                            size_mb = item.st_size / (1024 * 1024)
                            
                            # Highlight important files
                            if any(ext in item.filename.lower() for ext in ['.zip', '.txt', '.csv']):
                                if size_mb > 0.1:  # Only show files > 100KB
                                    print(f"{indent}  📄 {item.filename} ({size_mb:.1f} MB)")
                                    
                                    # Mark important files
                                    if 'cor' in item.filename.lower():
                                        print(f"{indent}     ⭐ Corporate data!")
                                    if 'off' in item.filename.lower():
                                        print(f"{indent}     ⭐ Officer data!")
                                    if 'annual' in item.filename.lower():
                                        print(f"{indent}     ⭐ Annual reports!")
                                    if 'event' in item.filename.lower():
                                        print(f"{indent}     ⭐ Event data!")
                            
                    except Exception as e:
                        print(f"{indent}  ❌ Error with {item.filename}: {e}")
                        
            except Exception as e:
                print(f"{indent}❌ Cannot access {path}: {e}")
        
        # Start exploration from root
        print("\n🔍 EXPLORING ROOT DIRECTORY:")
        print("-" * 40)
        explore_directory("/", max_depth=4)
        
        # Try to read the WELCOME.TXT file
        print("\n📄 READING WELCOME.TXT FOR INSTRUCTIONS:")
        print("-" * 40)
        try:
            with sftp.open('/Public/WELCOME.TXT', 'r') as f:
                welcome_content = f.read().decode('utf-8')
                print(welcome_content)
        except Exception as e:
            print(f"Cannot read WELCOME.TXT: {e}")
        
        # List specific paths mentioned in documentation
        print("\n🎯 CHECKING DOCUMENTED PATHS:")
        print("-" * 40)
        
        documented_paths = [
            "/Public",
            "/public", 
            "/Public/Daily",
            "/Public/Quarterly",
            "/Public/doc",
            "/Public/doc/cor",
            "/downloads",
            "/data"
        ]
        
        for path in documented_paths:
            try:
                items = sftp.listdir(path)
                print(f"✅ {path}: {len(items)} items")
                
                # Show first 5 files/folders
                for item in items[:5]:
                    print(f"   - {item}")
                    
                if len(items) > 5:
                    print(f"   ... and {len(items) - 5} more")
                    
            except Exception as e:
                print(f"❌ {path}: Not accessible")
        
        sftp.close()
        ssh.close()
        print("\n✅ Exploration complete!")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    explore_sftp()