"""
Cleanup script to remove old temporary files from temp/ folder.

Run this periodically to clean up any temp files that weren't deleted
due to errors or interruptions.
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_old_temp_files(temp_dir: Path, max_age_hours: int = 24):
    """
    Remove temporary video folders older than max_age_hours.

    Args:
        temp_dir: Path to temp directory
        max_age_hours: Maximum age in hours before deletion (default: 24)
    """
    if not temp_dir.exists():
        print(f"Temp directory does not exist: {temp_dir}")
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    deleted_count = 0
    total_size = 0

    print(f"🔍 Scanning temp directory: {temp_dir}")
    print(f"   Removing folders older than {max_age_hours} hours")

    for folder in temp_dir.iterdir():
        if not folder.is_dir():
            continue

        # Check folder age
        folder_age = current_time - folder.stat().st_mtime

        if folder_age > max_age_seconds:
            # Calculate folder size
            folder_size = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())

            folder_age_hours = folder_age / 3600
            print(f"   🗑️  Deleting: {folder.name}")
            print(f"      Age: {folder_age_hours:.1f} hours")
            print(f"      Size: {folder_size / (1024*1024):.1f}MB")

            try:
                shutil.rmtree(folder)
                deleted_count += 1
                total_size += folder_size
            except Exception as e:
                print(f"      ⚠️  Error deleting: {e}")

    if deleted_count > 0:
        print(f"\n✅ Cleanup complete:")
        print(f"   Folders deleted: {deleted_count}")
        print(f"   Space freed: {total_size / (1024*1024):.1f}MB")
    else:
        print(f"\n✅ No old temp files to clean")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Cleanup old temporary video files')
    parser.add_argument('--max-age', type=int, default=24,
                       help='Maximum age in hours (default: 24)')
    parser.add_argument('--temp-dir', type=str, default='temp',
                       help='Temp directory path (default: temp)')

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    temp_path = project_root / args.temp_dir

    cleanup_old_temp_files(temp_path, args.max_age)
