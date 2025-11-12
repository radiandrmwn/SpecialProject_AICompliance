#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPE-Watch Live Webcam Demo

Real-time helmet and vest detection demo using webcam.
Perfect for testing and demonstrations.

Usage:
    python scripts/demo_webcam.py
"""

import sys
import os
import cv2
import time
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ultralytics import YOLO
except ImportError:
    print("\n❌ Error: ultralytics not installed")
    print("📦 Install with: pip install ultralytics")
    sys.exit(1)

from src.inference.zoning import bbox_centroid, head_region, bbox_iou
from src.rules.violations import is_violation
from src.inference.trackers import TrackState


class LiveDemo:
    """Live webcam demo for PPE detection."""

    def __init__(self, ppe_model_path: str, person_model_path: str = "yolov8n.pt"):
        """
        Initialize demo.

        Args:
            ppe_model_path: Path to trained PPE model
            person_model_path: Path to person detection model
        """
        print("\n" + "=" * 70)
        print("PPE-Watch Live Webcam Demo (with Unique Person Tracking)")
        print("=" * 70)

        print("\n📦 Loading models...")
        self.person_model = YOLO(person_model_path)
        self.ppe_model = YOLO(ppe_model_path)
        print("   ✅ Models loaded!")

        # Track state for unique person counting
        self.track_state = TrackState()

        # Statistics - separated per-frame vs unique
        self.stats = {
            'frames': 0,
            'persons_detected_frames': 0,  # Total detections across all frames
            'unique_violators': set(),      # Unique track IDs without helmet
            'unique_compliant': set(),      # Unique track IDs with helmet
            'current_frame_violations': 0,  # Current frame violations (for display)
            'current_frame_compliant': 0    # Current frame compliant (for display)
        }

        # FPS calculation
        self.fps_start = time.time()
        self.fps = 0

    def detect_persons(self, frame):
        """Detect persons with tracking."""
        results = self.person_model.track(
            frame,
            conf=0.5,
            classes=[0],  # person class
            persist=True,
            verbose=False
        )

        persons = []
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None

                persons.append({
                    'bbox': tuple(box),
                    'confidence': conf,
                    'track_id': track_id
                })

        return persons

    def detect_ppe(self, frame):
        """Detect helmets and vests."""
        results = self.ppe_model(frame, conf=0.5, verbose=False)

        helmets = []
        vests = []

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls = int(boxes.cls[i].cpu().numpy())

                item = {
                    'bbox': tuple(box),
                    'confidence': conf,
                    'class': cls
                }

                if cls == 0:  # safety_helmet
                    helmets.append(item)
                elif cls == 1:  # reflective_jacket
                    vests.append(item)

        return helmets, vests

    def check_helmet_on_person(self, person_bbox, helmets):
        """Check if person has helmet on head."""
        head = head_region(person_bbox, top_ratio=0.35)

        for helmet in helmets:
            iou = bbox_iou(helmet['bbox'], head)
            if iou > 0.05:
                return True, helmet['confidence']

        return False, 0.0

    def draw_detection(self, frame, person, has_helmet, helmet_conf):
        """Draw detection boxes and labels."""
        x1, y1, x2, y2 = map(int, person['bbox'])
        track_id = person['track_id']

        # Color: Green if helmet, Red if no helmet
        color = (0, 255, 0) if has_helmet else (0, 0, 255)
        thickness = 3 if not has_helmet else 2

        # Draw person box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # Label
        label = f"Person"
        if track_id is not None:
            label += f" #{track_id}"

        if has_helmet:
            label += " ✓ HELMET"
            status = "COMPLIANT"
        else:
            label += " ✗ NO HELMET"
            status = "VIOLATION"

        # Draw label background
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - 30), (x1 + label_w + 10, y1), color, -1)
        cv2.putText(frame, label, (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw violation warning
        if not has_helmet:
            cv2.putText(frame, "⚠ VIOLATION", (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return status

    def draw_stats_overlay(self, frame):
        """Draw statistics overlay on frame."""
        height, width = frame.shape[:2]

        # Semi-transparent overlay (larger for more stats)
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Stats text
        y_offset = 35
        cv2.putText(frame, "PPE-Watch Live Demo", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        y_offset += 30
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        y_offset += 25
        cv2.putText(frame, f"Current Frame: {self.stats['current_frame_violations']} violations, {self.stats['current_frame_compliant']} compliant",
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        y_offset += 25
        cv2.putText(frame, "--- UNIQUE PERSONS ---", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        y_offset += 25
        cv2.putText(frame, f"Unique Violators: {len(self.stats['unique_violators'])}",
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        y_offset += 25
        cv2.putText(frame, f"Unique Compliant: {len(self.stats['unique_compliant'])}",
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Instructions
        cv2.putText(frame, "Press 'q' to quit", (width - 200, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def run(self, camera_id: int = 0):
        """
        Run live demo.

        Args:
            camera_id: Webcam ID (0 for default webcam)
        """
        print(f"\n🎥 Opening webcam {camera_id}...")
        cap = cv2.VideoCapture(camera_id)

        if not cap.isOpened():
            print(f"❌ Error: Cannot open webcam {camera_id}")
            print("💡 Tips:")
            print("   - Make sure no other app is using the webcam")
            print("   - Try camera_id=1 or 2 if you have multiple cameras")
            return

        # Get webcam properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"   Resolution: {width}x{height}")

        print("\n" + "=" * 70)
        print("🚀 DEMO STARTED - Stand in front of camera!")
        print("=" * 70)
        print("\n💡 Tips:")
        print("   - Stand 1-2 meters from camera")
        print("   - Try with and without helmet/hard hat")
        print("   - Green box = Helmet detected (Compliant)")
        print("   - Red box = No helmet (Violation)")
        print("   - Press 'q' to quit\n")

        cv2.namedWindow('PPE-Watch Live Demo', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('PPE-Watch Live Demo', 1280, 720)

        frame_count = 0
        fps_start = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error reading frame")
                    break

                frame_count += 1
                self.stats['frames'] = frame_count

                # Calculate FPS
                if frame_count % 10 == 0:
                    elapsed = time.time() - fps_start
                    self.fps = 10 / elapsed if elapsed > 0 else 0
                    fps_start = time.time()

                # Reset current frame counters
                self.stats['current_frame_violations'] = 0
                self.stats['current_frame_compliant'] = 0

                # Detect persons
                persons = self.detect_persons(frame)

                # Detect PPE
                helmets, vests = self.detect_ppe(frame)

                # Process each person
                for person in persons:
                    self.stats['persons_detected_frames'] += 1
                    track_id = person['track_id']

                    # Check helmet
                    has_helmet, helmet_conf = self.check_helmet_on_person(person['bbox'], helmets)

                    # Draw detection
                    status = self.draw_detection(frame, person, has_helmet, helmet_conf)

                    # Update current frame stats (for display)
                    if status == "VIOLATION":
                        self.stats['current_frame_violations'] += 1
                    else:
                        self.stats['current_frame_compliant'] += 1

                    # Track unique persons using TrackState (like production)
                    if track_id is not None:
                        # Use "demo_zone" as dummy zone for webcam demo
                        is_violation = (status == "VIOLATION")

                        # Check if should count this person (first time seeing this track_id + status)
                        should_count = self.track_state.should_count(
                            track_id,
                            "demo_zone",
                            is_violation=is_violation
                        )

                        if should_count:
                            if is_violation:
                                self.stats['unique_violators'].add(track_id)
                            else:
                                self.stats['unique_compliant'].add(track_id)

                # Draw helmets (cyan boxes)
                for helmet in helmets:
                    x1, y1, x2, y2 = map(int, helmet['bbox'])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.putText(frame, "Helmet", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

                # Draw vests (yellow boxes)
                for vest in vests:
                    x1, y1, x2, y2 = map(int, vest['bbox'])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    cv2.putText(frame, "Vest", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

                # Draw stats overlay
                self.draw_stats_overlay(frame)

                # Show frame
                cv2.imshow('PPE-Watch Live Demo', frame)

                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n👋 Demo stopped by user")
                    break

        except KeyboardInterrupt:
            print("\n👋 Demo interrupted")

        finally:
            cap.release()
            cv2.destroyAllWindows()

            # Print final stats
            print("\n" + "=" * 70)
            print("Demo Statistics")
            print("=" * 70)
            print(f"Total frames processed: {self.stats['frames']}")
            print(f"Total detections (all frames): {self.stats['persons_detected_frames']}")
            print(f"\n--- UNIQUE PERSONS (Production-like) ---")
            print(f"Unique Violators (no helmet): {len(self.stats['unique_violators'])}")
            if self.stats['unique_violators']:
                print(f"   Track IDs: {sorted(self.stats['unique_violators'])}")
            print(f"Unique Compliant (with helmet): {len(self.stats['unique_compliant'])}")
            if self.stats['unique_compliant']:
                print(f"   Track IDs: {sorted(self.stats['unique_compliant'])}")
            print("\n✅ Demo completed!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='PPE-Watch Live Webcam Demo')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID (default: 0)')
    parser.add_argument('--model', default='runs/helmet/train4/weights/best.pt', help='Path to PPE model')
    parser.add_argument('--person-model', default='yolov8n.pt', help='Person detector model')

    args = parser.parse_args()

    # Check if model exists
    if not Path(args.model).exists():
        print(f"\n❌ Error: Model not found at {args.model}")
        print("\n💡 Tips:")
        print("   - Make sure you've trained the model first")
        print("   - Check the path to best.pt")
        sys.exit(1)

    try:
        demo = LiveDemo(
            ppe_model_path=args.model,
            person_model_path=args.person_model
        )
        demo.run(camera_id=args.camera)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
