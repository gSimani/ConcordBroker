"""
Explore Sunbiz SFTP to find the actual data location
"""

import paramiko

SFTP_HOST = "sftp.floridados.gov"
SFTP_USER = "Public"
SFTP_PASS = "PubAccess1845!"

def main():
    print("Exploring Sunbiz SFTP in detail...")
    
    transport = paramiko.Transport((SFTP_HOST, 22))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    try:
        # Read the WELCOME.TXT file
        print("\n=== WELCOME.TXT Contents ===")
        with sftp.open('WELCOME.TXT', 'r') as f:
            content = f.read()
            try:
                print(content.decode('utf-8'))
            except:
                print(content.decode('latin-1'))
        
        # Explore doc directory
        print("\n=== /doc Directory Contents ===")
        doc_files = sftp.listdir('doc')
        for f in doc_files:
            try:
                stat = sftp.stat(f'doc/{f}')
                print(f"  {f} - {stat.st_size:,} bytes")
            except:
                print(f"  {f}")
        
        # Try to read any README or info files
        for filename in ['README', 'README.txt', 'README.TXT', 'info.txt', 'INFO.TXT']:
            try:
                with sftp.open(f'doc/{filename}', 'r') as f:
                    print(f"\n=== doc/{filename} Contents ===")
                    content = f.read().decode('utf-8')
                    print(content[:1000])  # First 1000 chars
                    break
            except:
                continue
                
    finally:
        sftp.close()
        transport.close()

if __name__ == "__main__":
    main()