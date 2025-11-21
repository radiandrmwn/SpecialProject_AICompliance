#!/usr/bin/env python3
"""
Detection Error Analysis Tool

Analyze false positives and false negatives in PPE detection.
Helps identify patterns in detection errors to improve model accuracy.
"""

import sys
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DetectionAnalyzer:
    """Analyze detection results and identify error patterns."""

    def __init__(self, model_path: str):
        """Initialize analyzer with model."""
        self.model = YOLO(model_path)
        self.stats = {
            'total_frames': 0,
            'helmet_detections': [],
            'vest_detections': [],
            'person_detections': [],
            'low_confidence_helmets': [],
            'low_confidence_vests': [],
            'detection_sizes': []
        }

    def analyze_video(self, video_path: str, conf_threshold: float = 0.25):
        """
        Analyze a video and collect detection statistics.

        Args:
            video_path: Path to video file
            conf_threshold: Confidence threshold for detections
        """
        print(f"\n📹 Analyzing video: {video_path}")
        print(f"⚙️  Confidence threshold: {conf_threshold}")
        print("=" * 70)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: Cannot open video {video_path}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📊 Video Info:")
        print(f"   - FPS: {fps:.1f}")
        print(f"   - Total frames: {total_frames}")
        print(f"   - Duration: {total_frames/fps:.1f}s")
        print()

        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Run detection
            results = self.model(frame, conf=conf_threshold, verbose=False)

            # Collect statistics
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                    bbox_width = x2 - x1
                    bbox_height = y2 - y1
                    bbox_area = bbox_width * bbox_height

                    detection_info = {
                        'frame': frame_idx,
                        'confidence': confidence,
                        'width': bbox_width,
                        'height': bbox_height,
                        'area': bbox_area,
                        'bbox': (x1, y1, x2, y2)
                    }

                    if cls_id == 0:  # Helmet
                        self.stats['helmet_detections'].append(detection_info)
                        if confidence < 0.5:
                            self.stats['low_confidence_helmets'].append(detection_info)

                    elif cls_id == 1:  # Vest
                        self.stats['vest_detections'].append(detection_info)
                        if confidence < 0.5:
                            self.stats['low_confidence_vests'].append(detection_info)

            frame_idx += 1

            # Progress indicator
            if frame_idx % 30 == 0:
                progress = (frame_idx / total_frames) * 100
                print(f"\r⏳ Processing: {progress:.1f}% ({frame_idx}/{total_frames})", end='')

        print(f"\n\n✅ Analysis complete!")

        cap.release()
        self.stats['total_frames'] = frame_idx

        self.print_statistics()

    def print_statistics(self):
        """Print analysis statistics."""
        print("\n" + "=" * 70)
        print("📊 DETECTION STATISTICS")
        print("=" * 70)

        print(f"\n🔍 Total frames analyzed: {self.stats['total_frames']}")

        # Helmet stats
        helmet_count = len(self.stats['helmet_detections'])
        print(f"\n⛑️  HELMET DETECTIONS: {helmet_count}")
        if helmet_count > 0:
            confidences = [d['confidence'] for d in self.stats['helmet_detections']]
            print(f"   - Avg confidence: {np.mean(confidences):.3f}")
            print(f"   - Min confidence: {np.min(confidences):.3f}")
            print(f"   - Max confidence: {np.max(confidences):.3f}")

            sizes = [d['area'] for d in self.stats['helmet_detections']]
            print(f"   - Avg bbox area: {np.mean(sizes):.1f} px²")
            print(f"   - Min bbox area: {np.min(sizes):.1f} px²")
            print(f"   - Max bbox area: {np.max(sizes):.1f} px²")

            low_conf_count = len(self.stats['low_confidence_helmets'])
            print(f"   - Low confidence (<0.5): {low_conf_count} ({low_conf_count/helmet_count*100:.1f}%)")

        # Vest stats
        vest_count = len(self.stats['vest_detections'])
        print(f"\n🦺 VEST DETECTIONS: {vest_count}")
        if vest_count > 0:
            confidences = [d['confidence'] for d in self.stats['vest_detections']]
            print(f"   - Avg confidence: {np.mean(confidences):.3f}")
            print(f"   - Min confidence: {np.min(confidences):.3f}")
            print(f"   - Max confidence: {np.max(confidences):.3f}")

            sizes = [d['area'] for d in self.stats['vest_detections']]
            print(f"   - Avg bbox area: {np.mean(sizes):.1f} px²")
            print(f"   - Min bbox area: {np.min(sizes):.1f} px²")
            print(f"   - Max bbox area: {np.max(sizes):.1f} px²")

            low_conf_count = len(self.stats['low_confidence_vests'])
            print(f"   - Low confidence (<0.5): {low_conf_count} ({low_conf_count/vest_count*100:.1f}%)")

        print("\n" + "=" * 70)
        print("💡 RECOMMENDATIONS")
        print("=" * 70)

        # Recommendations based on statistics
        if helmet_count > 0:
            avg_helmet_conf = np.mean([d['confidence'] for d in self.stats['helmet_detections']])
            if avg_helmet_conf < 0.6:
                print("\n⚠️  Helmet detection confidence is low (<0.6)")
                print("   Suggestions:")
                print("   - Increase training data with similar helmets")
                print("   - Check if helmet colors in video match training data")
                print("   - Consider lowering confidence threshold")

        if vest_count > 0:
            avg_vest_conf = np.mean([d['confidence'] for d in self.stats['vest_detections']])
            if avg_vest_conf < 0.6:
                print("\n⚠️  Vest detection confidence is low (<0.6)")
                print("   Suggestions:")
                print("   - Increase training data with similar vests")
                print("   - Check if vest colors in video match training data")
                print("   - Consider lowering confidence threshold")

        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze detection errors in videos')
    parser.add_argument('--video', required=True, help='Path to video file')
    parser.add_argument('--model', default='runs/helmet/train4/weights/best.pt',
                       help='Path to model weights')
    parser.add_argument('--conf', type=float, default=0.25,
                       help='Confidence threshold (default: 0.25)')

    args = parser.parse_args()

    # Resolve paths
    video_path = Path(args.video)
    model_path = Path(args.model)

    if not model_path.is_absolute():
        model_path = project_root / model_path

    if not video_path.exists():
        print(f"❌ Error: Video not found at {video_path}")
        sys.exit(1)

    if not model_path.exists():
        print(f"❌ Error: Model not found at {model_path}")
        sys.exit(1)

    # Run analysis
    analyzer = DetectionAnalyzer(str(model_path))
    analyzer.analyze_video(str(video_path), conf_threshold=args.conf)

    print("\n💡 Next steps:")
    print("   1. Review the statistics above")
    print("   2. Test with different confidence thresholds")
    print("   3. Collect more training data for low-confidence cases")
    print("   4. Re-train model with improved dataset")


if __name__ == '__main__':
    main()
