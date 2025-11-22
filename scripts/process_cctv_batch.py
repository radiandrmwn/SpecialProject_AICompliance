"""
Batch process CCTV recordings for daily PPE compliance report.

Usage:
    # Process all recordings from today
    python scripts/process_cctv_batch.py

    # Process specific date
    python scripts/process_cctv_batch.py --date 2025-11-20

    # Process specific folder
    python scripts/process_cctv_batch.py --input cctv_recordings/cam1/

Setup:
    1. Configure CCTV to save recordings to a folder
    2. Update CCTV_RECORDINGS_PATH below
    3. Run manually or schedule with Task Scheduler/cron
"""

import sys
import glob
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.inference.video_processor import process_video_for_violations
from src.reporting.aggregate_day import aggregate_daily_events, generate_charts
from src.delivery.whatsapp import send_daily_report

# Configuration
CCTV_RECORDINGS_PATH = Path("cctv_recordings")  # Change this to your CCTV folder
OUTPUT_BASE = Path("temp/batch_processing")
SAMPLE_RATE = 4  # Process every 4th frame for speed
RESIZE_WIDTH = 960  # Resize for speed

def process_cctv_batch(recordings_folder: Path, date: str = None):
    """
    Process all CCTV recordings from a folder.

    Args:
        recordings_folder: Path to folder containing recordings
        date: Date string (YYYY-MM-DD), defaults to today
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    print("=" * 80)
    print(f"PPE-Watch CCTV Batch Processor")
    print("=" * 80)
    print(f"Date: {date}")
    print(f"Input: {recordings_folder}")
    print(f"Sample Rate: {SAMPLE_RATE} (every {SAMPLE_RATE}th frame)")
    print(f"Resize: {RESIZE_WIDTH}px width")
    print("=" * 80)

    # Find all video files
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(recordings_folder.glob(ext))

    if not video_files:
        print(f"❌ No video files found in {recordings_folder}")
        return

    print(f"\n📹 Found {len(video_files)} video files")

    # Process each video
    total_violations = 0
    total_compliant = 0
    processed_count = 0

    for i, video_path in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Processing: {video_path.name}")

        # Create output directory for this video
        output_dir = OUTPUT_BASE / date / video_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Process video
            results = process_video_for_violations(
                video_path=video_path,
                output_dir=output_dir,
                sample_rate=SAMPLE_RATE,
                resize_width=RESIZE_WIDTH,
                save_annotated=False,  # Don't save annotated videos to save space
                camera_id=video_path.stem  # Use filename as camera ID
            )

            if results:
                total_violations += results['unique_violators']
                total_compliant += results['compliant_persons']
                processed_count += 1

                print(f"   ✅ Violations: {results['unique_violators']}, "
                      f"Compliant: {results['compliant_persons']}")
            else:
                print(f"   ⚠️ Processing failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    print("\n" + "=" * 80)
    print(f"📊 Batch Processing Complete")
    print("=" * 80)
    print(f"Videos processed: {processed_count}/{len(video_files)}")
    print(f"Total violations: {total_violations}")
    print(f"Total compliant: {total_compliant}")

    # Generate daily report from aggregated events
    try:
        print(f"\n📊 Generating daily report for {date}...")
        from src.reporting.aggregate_day import main as generate_report
        generate_report(date)

        # Send WhatsApp report
        print(f"\n📱 Sending WhatsApp report...")
        send_daily_report(date)

        print("\n✅ Daily report generated and sent!")

    except Exception as e:
        print(f"\n⚠️ Could not generate/send report: {e}")

    print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(description='Batch process CCTV recordings for PPE compliance')
    parser.add_argument('--date', type=str, help='Date to process (YYYY-MM-DD), defaults to today')
    parser.add_argument('--input', type=str, help='Input folder path, defaults to CCTV_RECORDINGS_PATH')

    args = parser.parse_args()

    # Determine input folder
    if args.input:
        recordings_folder = Path(args.input)
    else:
        # Default: use date-based folder structure
        date = args.date or datetime.now().strftime('%Y-%m-%d')
        recordings_folder = CCTV_RECORDINGS_PATH / date

    if not recordings_folder.exists():
        print(f"❌ Folder not found: {recordings_folder}")
        print(f"\n💡 Create folder structure:")
        print(f"   {CCTV_RECORDINGS_PATH}/")
        print(f"   ├── 2025-11-20/")
        print(f"   │   ├── cam1_recording1.mp4")
        print(f"   │   ├── cam1_recording2.mp4")
        print(f"   │   └── ...")
        print(f"   ├── 2025-11-21/")
        print(f"   └── ...")
        sys.exit(1)

    process_cctv_batch(recordings_folder, args.date)

if __name__ == '__main__':
    main()
