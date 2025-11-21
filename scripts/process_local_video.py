#!/usr/bin/env python3
"""
Process Local Video for PPE Violations

Bypass Telegram download by processing video file directly from disk.
Useful for testing, demo, and processing large videos.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.inference.video_processor import process_video_for_violations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Process local video for PPE violations')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--model', default='runs/helmet/train4/weights/best.pt',
                       help='Path to model weights')
    parser.add_argument('--sample-rate', type=int, default=4,
                       help='Process every Nth frame (default: 4)')
    parser.add_argument('--resize-width', type=int, default=960,
                       help='Resize width for faster processing (default: 960)')
    parser.add_argument('--no-resize', action='store_true',
                       help='Process at original resolution (slower)')

    args = parser.parse_args()

    # Validate input
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ Error: Video not found at {video_path}")
        sys.exit(1)

    # Resolve model path
    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = project_root / model_path

    if not model_path.exists():
        print(f"❌ Error: Model not found at {model_path}")
        print(f"\n💡 Tips:")
        print(f"   - Train model first: python -m src.models.train")
        print(f"   - Or specify path with --model")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("PPE-Watch Local Video Processing")
    print("=" * 70)
    print(f"\n📹 Input:  {video_path}")
    print(f"📁 Output: {output_dir}")
    print(f"🤖 Model:  {model_path}")
    print(f"⚙️  Settings:")
    print(f"   - Sample rate: Every {args.sample_rate} frames")

    resize_width = None if args.no_resize else args.resize_width
    if resize_width:
        print(f"   - Resize width: {resize_width}px")
    else:
        print(f"   - Resize: None (original resolution)")

    print("\n" + "=" * 70)

    # Process video
    results = process_video_for_violations(
        video_path,
        output_dir,
        model_path=str(model_path),
        sample_rate=args.sample_rate,
        resize_width=resize_width,
        save_events=False  # Don't save to events log (testing mode)
    )

    if results is None:
        print("\n❌ Processing failed!")
        sys.exit(1)

    # Print results
    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE")
    print("=" * 70)

    print(f"\n📊 Results:")
    print(f"   - Duration: {results['duration']:.1f}s")
    print(f"   - Total frames: {results['total_frames']}")
    print(f"   - Unique violators: {results['unique_violators']}")
    print(f"   - Compliant persons: {results['compliant']}")

    if results.get('zones'):
        print(f"\n📍 Violations by Zone:")
        for zone_name, count in results['zones'].items():
            print(f"   - {zone_name}: {count}")

    # Output files
    annotated_video = output_dir / "output_annotated.avi"
    if not annotated_video.exists():
        annotated_video = output_dir / "output_annotated.mp4"

    if annotated_video.exists():
        print(f"\n📹 Annotated Video:")
        print(f"   {annotated_video}")
        print(f"   Size: {annotated_video.stat().st_size / (1024*1024):.1f}MB")

    print("\n" + "=" * 70)
    print("💡 Next Steps:")
    print("   - Review annotated video")
    print("   - Adjust sample_rate or resize_width if needed")
    print("   - Use this for testing without Telegram delay!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
