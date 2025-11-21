#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Processor for Telegram Bot
Processes uploaded videos to detect PPE violations.
"""

import sys
import cv2
import time
from pathlib import Path
from typing import Optional, Dict
from collections import defaultdict
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from ultralytics import YOLO
except ImportError:
    print("❌ Error: ultralytics not installed")
    print("Install with: pip install ultralytics")
    sys.exit(1)

# Import project modules
from src.inference.trackers import TrackState
from src.rules.violations import is_violation, head_region, iou
from src.storage.events_writer import EventsWriter


def process_video_for_violations(
    video_path: Path,
    output_dir: Path,
    model_path: str = "runs/helmet/train4/weights/best.pt",
    person_model_path: str = "yolov8s.pt",
    conf_thresh: float = 0.3,
    save_annotated: bool = True,
    sample_rate: int = 4,  # Process every Nth frame for speed (increased from 2 to 4)
    camera_id: str = "telegram_upload",  # Camera ID for logging
    save_events: bool = True,  # Whether to save to events log
    events_dir: str = "events",  # Events directory
    resize_width: int = 960  # Resize width for faster processing (None = no resize)
) -> Optional[Dict]:
    """
    Process video to detect PPE violations.

    Args:
        video_path: Path to input video
        output_dir: Directory for outputs
        model_path: Path to helmet detection model
        person_model_path: Path to person detection model
        conf_thresh: Confidence threshold
        save_annotated: Whether to save annotated video
        sample_rate: Process every Nth frame (1=all frames, 4=every 4th frame for 4x speed)
        resize_width: Target width for resizing (proportional height). None = no resize

    Returns:
        Dictionary with results or None if failed
    """
    print(f"📹 Processing video: {video_path}")

    # Load models
    try:
        helmet_model = YOLO(model_path)
        person_model = YOLO(person_model_path)
        print(f"✅ Models loaded")
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return None

    # Open video
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        # Calculate resize dimensions if resize_width is specified
        if resize_width and resize_width < orig_width:
            width = resize_width
            height = int(orig_height * (resize_width / orig_width))
            print(f"   Original: {orig_width}x{orig_height}")
            print(f"   Resized:  {width}x{height} (for faster processing)")
            print(f"   Video: {fps:.1f}fps, {total_frames} frames, {duration:.1f}s")
        else:
            width = orig_width
            height = orig_height
            print(f"   Video: {width}x{height} @ {fps:.1f}fps, {total_frames} frames, {duration:.1f}s")

    except Exception as e:
        print(f"❌ Error opening video: {e}")
        return None

    # Setup output video writer
    output_video_path = None
    writer = None

    if save_annotated:
        # Use AVI with XVID codec (most compatible, no external library)
        output_video_path = output_dir / "output_annotated.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer = cv2.VideoWriter(
            str(output_video_path),
            fourcc,
            fps,
            (width, height)
        )

        # Verify writer opened successfully
        if not writer.isOpened():
            print("⚠️ Warning: Could not create video writer, trying MP4V fallback...")
            # Fallback to MP4 with mp4v codec
            output_video_path = output_dir / "output_annotated.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                str(output_video_path),
                fourcc,
                fps,
                (width, height)
            )

    # Initialize tracking
    track_state = TrackState()

    # Initialize events writer
    events_writer = None
    if save_events:
        events_writer = EventsWriter(events_dir)
        print(f"   📝 Events will be saved to: {events_dir}/")

    # Statistics
    stats = {
        'total_violations': 0,
        'unique_violators': set(),
        'compliant_persons': set(),
        'zones': defaultdict(int),
        'total_frames': 0,
        'duration': duration
    }

    frame_idx = 0
    processed_frames = 0

    # Get current timestamp for events
    process_start_time = time.time()

    print(f"   🔍 Processing frames (sampling every {sample_rate} frames)...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            # Resize frame if specified (for faster processing)
            if resize_width and resize_width < orig_width:
                frame = cv2.resize(frame, (width, height))

            # Run detections
            try:
                # IMPORTANT: Always run person tracking on every frame for stable IDs
                # Try BoT-SORT tracker (more stable than ByteTrack)
                person_results = person_model.track(
                    frame,
                    classes=[0],  # Person class
                    conf=conf_thresh,
                    persist=True,
                    tracker="botsort.yaml",  # Use BoT-SORT instead of ByteTrack
                    verbose=False,
                    imgsz=640  # Smaller input size for faster inference
                )

                # Determine if this is a sampled frame for PPE detection
                is_sampled_frame = (frame_idx % sample_rate == 0)

                # Only detect helmets/vests on sampled frames (speed optimization)
                helmet_boxes = []
                vest_boxes = []

                if is_sampled_frame:
                    processed_frames += 1

                    # Detect helmets and vests (only on sampled frames)
                    helmet_results = helmet_model.track(
                        frame,
                        conf=conf_thresh,
                        persist=False,
                        verbose=False,
                        imgsz=640  # Smaller input size for faster inference
                    )

                    # Extract detections with confidence filtering
                    if helmet_results[0].boxes is not None:
                        for box in helmet_results[0].boxes:
                            cls_id = int(box.cls[0])
                            confidence = float(box.conf[0])

                            # Only use detections with confidence > 0.25
                            if confidence > 0.25:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                bbox = (int(x1), int(y1), int(x2), int(y2))

                                if cls_id == 0:  # Helmet class
                                    helmet_boxes.append(bbox)
                                elif cls_id == 1:  # Vest/reflective jacket class
                                    vest_boxes.append(bbox)

                # Process persons on EVERY frame (maintains track IDs)
                if person_results[0].boxes is not None:
                    for box in person_results[0].boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        person_box = (int(x1), int(y1), int(x2), int(y2))

                        # Get track ID (extracted every frame for stability)
                        track_id = None
                        if box.id is not None:
                            track_id = int(box.id[0])

                        # Only check violations on sampled frames (speed optimization)
                        if is_sampled_frame:
                            # Check for helmet (head region overlap)
                            # Lower threshold for better detection sensitivity
                            head = head_region(person_box)
                            has_helmet = any(iou(helmet_box, head) > 0.10 for helmet_box in helmet_boxes)

                            # Check for vest (body overlap)
                            has_vest = any(iou(vest_box, person_box) > 0.15 for vest_box in vest_boxes)

                            # Violation if missing EITHER helmet OR vest (both required for compliance)
                            is_violator = not has_helmet or not has_vest

                            # Build violation label
                            missing_items = []
                            if not has_helmet:
                                missing_items.append("NO HELMET")
                            if not has_vest:
                                missing_items.append("NO VEST")

                            if missing_items:
                                violation_label = " & ".join(missing_items)
                            else:
                                violation_label = "COMPLIANT"

                            # Track unique persons (only count on sampled frames)
                            if track_id is not None:
                                should_count = track_state.should_count(
                                    track_id,
                                    "main_zone",
                                    is_violation=is_violator
                                )

                                if should_count:
                                    if is_violator:
                                        stats['unique_violators'].add(track_id)
                                        stats['zones']['main_zone'] += 1
                                        stats['total_violations'] += 1
                                    else:
                                        stats['compliant_persons'].add(track_id)

                                    # Write event to log
                                    if events_writer:
                                        event_timestamp = process_start_time + (frame_idx / fps)
                                        event_row = {
                                            'timestamp': event_timestamp,
                                            'camera_id': camera_id,
                                            'track_id': track_id,
                                            'zone': 'main_zone',
                                            'has_helmet': not is_violator,
                                            'frame_idx': frame_idx
                                        }
                                        events_writer.append(event_row)

                            # Draw on frame (only on sampled frames)
                            if writer:
                                color = (0, 0, 255) if is_violator else (0, 255, 0)
                                label = f"ID:{track_id} {violation_label}"

                                # Draw box
                                cv2.rectangle(frame, (person_box[0], person_box[1]),
                                             (person_box[2], person_box[3]), color, 2)

                                # Draw label background
                                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                                cv2.rectangle(frame,
                                             (person_box[0], person_box[1] - label_size[1] - 10),
                                             (person_box[0] + label_size[0], person_box[1]),
                                             color, -1)

                                # Draw label text
                                cv2.putText(frame, label,
                                           (person_box[0], person_box[1] - 5),
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Draw stats on frame
                if writer:
                    stats_text = f"Frame: {frame_idx}/{total_frames} | Violators: {len(stats['unique_violators'])} | Compliant: {len(stats['compliant_persons'])}"
                    cv2.putText(frame, stats_text, (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            except Exception as e:
                print(f"⚠️ Error processing frame {frame_idx}: {e}")

            # Write frame
            if writer:
                writer.write(frame)

            # Progress indicator
            if processed_frames % 30 == 0:
                progress = (frame_idx / total_frames) * 100
                print(f"      Progress: {progress:.1f}% ({frame_idx}/{total_frames} frames)")

    finally:
        cap.release()
        if writer:
            writer.release()

    stats['total_frames'] = frame_idx

    # Convert sets to counts
    result = {
        'total_violations': stats['total_violations'],
        'unique_violators': len(stats['unique_violators']),
        'compliant_persons': len(stats['compliant_persons']),
        'zones': dict(stats['zones']),
        'total_frames': stats['total_frames'],
        'duration': stats['duration']
    }

    print(f"✅ Processing complete:")
    print(f"   Frames processed: {stats['total_frames']}")
    print(f"   Unique violators: {result['unique_violators']}")
    print(f"   Compliant persons: {result['compliant_persons']}")

    if save_annotated and output_video_path:
        print(f"   Annotated video: {output_video_path}")

    if save_events:
        # Get the date of the events log
        event_date = datetime.fromtimestamp(process_start_time).strftime('%Y-%m-%d')
        print(f"   📝 Events saved to: events/events_{event_date}.csv")

    return result


if __name__ == '__main__':
    # Test standalone
    import argparse

    parser = argparse.ArgumentParser(description='Process video for violations')
    parser.add_argument('--video', required=True, help='Path to video file')
    parser.add_argument('--output', default='temp/test_output', help='Output directory')
    parser.add_argument('--model', default='runs/helmet/train4/weights/best.pt', help='Helmet model path')
    parser.add_argument('--conf', type=float, default=0.3, help='Confidence threshold')

    args = parser.parse_args()

    video_path = Path(args.video)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = process_video_for_violations(
        video_path,
        output_dir,
        model_path=args.model,
        conf_thresh=args.conf
    )

    if results:
        print(f"\n✅ Results:")
        print(f"   Unique violators: {results['unique_violators']}")
        print(f"   Compliant persons: {results['compliant_persons']}")
        print(f"   Total frames: {results['total_frames']}")
        print(f"   Duration: {results['duration']:.1f}s")
    else:
        print("\n❌ Processing failed")
