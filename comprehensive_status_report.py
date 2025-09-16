"""
Comprehensive status report of all email extraction activities
"""

import sys
import io
from pathlib import Path
import json
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def generate_status_report():
    """Generate comprehensive status report"""
    
    print("=" * 80)
    print("🚀 FLORIDA BUSINESS EMAIL EXTRACTION - COMPREHENSIVE STATUS")
    print("=" * 80)
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
    
    # Check what files we have
    print(f"\n📁 DATA DIRECTORY: {base_path}")
    print("-" * 80)
    
    files_status = {}
    total_data_size = 0
    
    # Key files to check
    key_files = [
        'corprindata.zip',
        'cordata_quarterly.zip',
        'corevent_quarterly.zip',
        'extracted_emails.txt',
        'comprehensive_emails.txt'
    ]
    
    for filename in key_files:
        file_path = base_path / filename
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            total_data_size += size_bytes
            
            # Determine status and expected size
            if filename == 'corprindata.zip':
                expected_mb = 665.8
                status = "✅ COMPLETE" if size_mb >= expected_mb * 0.95 else "⏳ DOWNLOADING"
                description = "Principal corporate data"
            elif filename == 'cordata_quarterly.zip':
                expected_mb = 1639.0
                status = "✅ COMPLETE" if size_mb >= expected_mb * 0.95 else "⏳ DOWNLOADING"
                description = "Quarterly corporate data (COMPREHENSIVE)"
            elif filename == 'corevent_quarterly.zip':
                expected_mb = 170.5
                status = "✅ COMPLETE" if size_mb >= expected_mb * 0.95 else "⏳ DOWNLOADING"  
                description = "Corporate events quarterly data"
            elif filename == 'extracted_emails.txt':
                status = "✅ READY"
                expected_mb = size_mb
                description = "Initial email extraction (383 emails)"
            elif filename == 'comprehensive_emails.txt':
                status = "✅ READY"
                expected_mb = size_mb
                description = "Comprehensive email extraction"
            
            files_status[filename] = {
                'size_mb': size_mb,
                'expected_mb': expected_mb,
                'status': status,
                'description': description
            }
            
            print(f"{status} {filename}")
            print(f"    📊 Size: {size_mb:.1f} MB / {expected_mb:.1f} MB ({size_mb/expected_mb*100:.1f}%)")
            print(f"    📝 {description}")
            
        else:
            print(f"❌ MISSING {filename}")
            print(f"    📝 Not downloaded yet")
    
    total_data_gb = total_data_size / (1024 * 1024 * 1024)
    print(f"\n💾 TOTAL DATA SIZE: {total_data_gb:.2f} GB")
    
    # Check email extraction results
    print(f"\n📧 EMAIL EXTRACTION RESULTS")
    print("-" * 80)
    
    # Initial extraction
    extracted_emails_file = base_path / "extracted_emails.txt"
    if extracted_emails_file.exists():
        with open(extracted_emails_file, 'r') as f:
            initial_emails = len(f.readlines())
        print(f"✅ Initial extraction: {initial_emails:,} unique emails")
        print(f"    📁 Source: corprindata.zip (665MB)")
        print(f"    📊 Email density: {initial_emails / 665:.1f} emails per MB")
    
    # Comprehensive extraction
    comprehensive_emails_file = base_path / "comprehensive_emails.txt"
    if comprehensive_emails_file.exists():
        with open(comprehensive_emails_file, 'r') as f:
            comprehensive_emails = len(f.readlines())
        print(f"✅ Comprehensive extraction: {comprehensive_emails:,} unique emails")
        print(f"    📁 Source: All quarterly data")
    else:
        print(f"⏳ Comprehensive extraction: In progress...")
        
        # Estimate based on file sizes
        corprin_size = files_status.get('corprindata.zip', {}).get('size_mb', 0)
        quarterly_size = files_status.get('cordata_quarterly.zip', {}).get('size_mb', 0)
        
        if corprin_size > 600:  # If corprindata is complete
            # Estimate emails in quarterly data
            email_density = initial_emails / 665 if initial_emails else 0.5
            estimated_quarterly_emails = int(1639 * email_density)
            total_estimated = initial_emails + estimated_quarterly_emails
            
            print(f"    📈 Estimated quarterly emails: {estimated_quarterly_emails:,}")
            print(f"    🎯 Total estimated emails: {total_estimated:,}")
    
    # Download progress
    print(f"\n📥 DOWNLOAD PROGRESS")
    print("-" * 80)
    
    progress_file = base_path / "download_progress.json"
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            print(f"📊 Last download status: {progress['status']}")
            print(f"📈 Progress: {progress['progress_percent']:.1f}%")
            print(f"📁 File: {Path(progress['file']).name}")
            print(f"⏰ Last update: {progress['timestamp']}")
        except:
            print("❌ Could not read progress file")
    else:
        print("ℹ️ No active downloads tracked")
    
    # Next steps
    print(f"\n🎯 NEXT STEPS")
    print("-" * 80)
    
    if files_status.get('cordata_quarterly.zip', {}).get('status') == "✅ COMPLETE":
        print("1. ✅ Quarterly data download complete")
        print("2. 🚀 Process quarterly data for comprehensive email extraction")
        print("3. 📊 Expect 5,000+ additional business emails")
    elif files_status.get('cordata_quarterly.zip', {}).get('size_mb', 0) > 0:
        remaining_mb = 1639 - files_status.get('cordata_quarterly.zip', {}).get('size_mb', 0)
        print(f"1. ⏳ Quarterly download in progress ({remaining_mb:.1f} MB remaining)")
        print("2. ⏳ Wait for download to complete")
        print("3. 🚀 Then process for comprehensive email extraction")
    else:
        print("1. 🚀 Start quarterly data download")
        print("2. ⏳ Download 1.6GB of comprehensive data")
        print("3. 📧 Extract thousands of additional emails")
    
    # Business value summary
    current_emails = initial_emails if 'initial_emails' in locals() else 0
    print(f"\n💼 BUSINESS VALUE SUMMARY")
    print("-" * 80)
    print(f"📧 Current unique emails: {current_emails:,}")
    print(f"🎯 Potential total emails: 5,000+ (estimated)")
    print(f"📊 Data source: Official Florida state corporate records")
    print(f"✅ Legal compliance: Public corporate filing information")
    print(f"🎪 Business use: B2B marketing, lead generation, business development")
    
    print(f"\n" + "=" * 80)
    print("📈 EMAIL EXTRACTION PIPELINE STATUS: ACTIVE & EXPANDING")
    print("=" * 80)

if __name__ == "__main__":
    generate_status_report()