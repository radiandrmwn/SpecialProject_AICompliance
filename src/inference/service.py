#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPE-Watch Inference Service

Main inference pipeline that:
1. Detects persons using YOLO
2. Detects helmets and jackets using trained model
3. Matches PPE to persons
4. Checks zone violations
5. Logs events to CSV
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np
from ultralytics import YOLO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.inference.zoning import bbox_centroid, head_region, bbox_iou
from src.inference.trackers import TrackState
from src.storage.events_writer import EventsWriter
from src.storage.schema import create_event_record


class PPEWatchInference:
    """PPE-Watch inference service for violation detection."""

    def __init__(
        self,
        ppe_model_path: str,
        zones_config_path: str,
        camera_id: str = "cam_1",
        person_model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        head_iou_threshold: float = 0.05,
        head_ratio: float = 0.35,
        events_dir: str = "./events",
        save_video: bool = True,
        output_dir: str = "./runs/inference"
    ):
        """
        Initialize PPE-Watch inference service.

        Args:
            ppe_model_path: Path to trained PPE detection model (helmets/jackets)
            zones_config_path: Path to zones configuration JSON
            camera_id: Camera identifier
            person_model_path: Path to person detection model (default: yolov8n.pt)
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
            head_iou_threshold: IoU threshold for helmet-head matching
            head_ratio: Ratio of person bbox to consider as head region
            events_dir: Directory to save event logs
            save_video: Whether to save annotated video
            output_dir: Directory for output videos
        """
        print("=" * 70)
        print("PPE-Watch Inference Service")
        print("=" * 70)

        # Load models
        print(f"\n📦 Loading models...")
        print(f"   Person detector: {person_model_path}")
        self.person_model = YOLO(person_model_path)

        print(f"   PPE detector: {ppe_model_path}")
        self.ppe_model = YOLO(ppe_model_path)

        # Load zones configuration
        print(f"\n🗺️  Loading zones: {zones_config_path}")
        with open(zones_config_path, 'r') as f:
            zones_config = json.load(f)

        self.camera_id = camera_id
        self.zones = zones_config.get(camera_id, {}).get('polygons', [])
        print(f"   Camera: {camera_id}")
        print(f"   Zones loaded: {len(self.zones)}")
        for zone in self.zones:
            print(f"     - {zone['name']}: mandatory_helmet={zone.get('mandatory_helmet', True)}")

        # Parameters
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.head_iou_threshold = head_iou_threshold
        self.head_ratio = head_ratio

        # Tracking and logging
        self.track_state = TrackState()
        self.events_writer = EventsWriter(events_dir)

        # Output settings
        self.save_video = save_video
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'frames_processed': 0,
            'persons_detected': 0,
            'helmets_detected': 0,
            'jackets_detected': 0,
            'violations_detected': 0,
            'violations_logged': 0
        }

        print("\n✅ Initialization complete!")

    def detect_persons(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect persons in frame using person detector.

        Args:
            frame: Input frame

        Returns:
            List of person detections with tracking IDs
        """
        # Run person detection with tracking
        results = self.person_model.track(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            classes=[0],  # Person class in COCO
            persist=True,
            verbose=False
        )

        persons = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes

            for i in range(len(boxes)):
                # Get box coordinates
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i])

                # Get track ID
                track_id = None
                if boxes.id is not None:
                    track_id = int(boxes.id[i])

                persons.append({
                    'bbox': tuple(xyxy),
                    'confidence': conf,
                    'track_id': track_id
                })

        return persons

    def detect_ppe(self, frame: np.ndarray) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect helmets and jackets using PPE model.

        Args:
            frame: Input frame

        Returns:
            Tuple of (helmets, jackets) detections
        """
        results = self.ppe_model(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )

        helmets = []
        jackets = []

        if results and results[0].boxes is not None:
            boxes = results[0].boxes

            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i])
                cls = int(boxes.cls[i])

                detection = {
                    'bbox': tuple(xyxy),
                    'confidence': conf,
                    'class': cls
                }

                # Class 0: safety_helmet, Class 1: reflective_jacket
                if cls == 0:
                    helmets.append(detection)
                elif cls == 1:
                    jackets.append(detection)

        return helmets, jackets

    def check_helmet_on_person(
        self,
        person_bbox: Tuple,
        helmets: List[Dict]
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if person has helmet on their head.

        Args:
            person_bbox: Person bounding box (x1, y1, x2, y2)
            helmets: List of helmet detections

        Returns:
            Tuple of (has_helmet, best_confidence)
        """
        head_bbox = head_region(person_bbox, top_ratio=self.head_ratio)

        best_iou = 0
        best_conf = None

        for helmet in helmets:
            helmet_bbox = helmet['bbox']
            iou = bbox_iou(helmet_bbox, head_bbox)

            if iou > self.head_iou_threshold and iou > best_iou:
                best_iou = iou
                best_conf = helmet['confidence']

        has_helmet = best_iou > self.head_iou_threshold
        return has_helmet, best_conf

    def check_zone_violation(
        self,
        person_bbox: Tuple,
        has_helmet: bool
    ) -> Tuple[bool, str]:
        """
        Check if person is violating zone rules.

        Args:
            person_bbox: Person bounding box
            has_helmet: Whether person has helmet

        Returns:
            Tuple of (is_violation, zone_name)
        """
        # Get person centroid
        centroid = bbox_centroid(person_bbox)

        # Check if in any zone
        from src.inference.zoning import point_in_polygons
        in_zone, zone_name = point_in_polygons(centroid, self.zones)

        if not in_zone:
            return False, ""

        # Check if zone requires helmet
        zone_dict = next((z for z in self.zones if z.get('name') == zone_name), None)
        if zone_dict and not zone_dict.get('mandatory_helmet', True):
            return False, zone_name

        # Violation if in mandatory zone without helmet
        is_violation = not has_helmet
        return is_violation, zone_name

    def process_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        timestamp: float
    ) -> np.ndarray:
        """
        Process a single frame.

        Args:
            frame: Input frame
            frame_idx: Frame index
            timestamp: Frame timestamp

        Returns:
            Annotated frame
        """
        # Detect persons
        persons = self.detect_persons(frame)
        self.stats['persons_detected'] += len(persons)

        # Detect PPE
        helmets, jackets = self.detect_ppe(frame)
        self.stats['helmets_detected'] += len(helmets)
        self.stats['jackets_detected'] += len(jackets)

        # Process each person
        for person in persons:
            person_bbox = person['bbox']
            track_id = person['track_id']
            person_conf = person['confidence']

            # Check if helmet on head
            has_helmet, helmet_conf = self.check_helmet_on_person(person_bbox, helmets)

            # Check zone violation
            is_violation, zone_name = self.check_zone_violation(person_bbox, has_helmet)

            # Draw person box
            color = (0, 255, 0) if has_helmet else (0, 0, 255)  # Green if helmet, red if not
            thickness = 3 if is_violation else 2

            x1, y1, x2, y2 = map(int, person_bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            # Draw label
            label = f"Person"
            if track_id is not None:
                label += f" #{track_id}"
            if has_helmet:
                label += f" ✓ Helmet"
            else:
                label += f" ✗ NO HELMET"

            if zone_name:
                label += f" | {zone_name}"

            label_bg_color = (0, 255, 0) if has_helmet else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1 - 25), (x1 + len(label) * 10, y1), label_bg_color, -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Log violation if detected
            if is_violation and track_id is not None:
                self.stats['violations_detected'] += 1

                # Check if should count (prevent double counting)
                if self.track_state.should_count(track_id, zone_name, is_violation=True):
                    self.stats['violations_logged'] += 1

                    # Create event record
                    event = create_event_record(
                        timestamp=timestamp,
                        camera_id=self.camera_id,
                        track_id=track_id,
                        zone=zone_name,
                        has_helmet=has_helmet,
                        frame_idx=frame_idx,
                        confidence=person_conf,
                        person_bbox=person_bbox
                    )

                    # Write to CSV
                    self.events_writer.append(event)

                    # Draw violation warning
                    cv2.putText(
                        frame,
                        "⚠️ VIOLATION",
                        (x1, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

        # Draw helmets (cyan boxes)
        for helmet in helmets:
            x1, y1, x2, y2 = map(int, helmet['bbox'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 1)
            cv2.putText(frame, f"Helmet {helmet['confidence']:.2f}", (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        # Draw jackets (yellow boxes)
        for jacket in jackets:
            x1, y1, x2, y2 = map(int, jacket['bbox'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 1)
            cv2.putText(frame, f"Jacket {jacket['confidence']:.2f}", (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        # Draw zone boundaries
        for zone in self.zones:
            points = np.array(zone['points'], dtype=np.int32)
            cv2.polylines(frame, [points], True, (255, 0, 255), 2)
            # Zone label
            cv2.putText(frame, zone['name'], tuple(points[0]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

        # Draw stats overlay
        stats_text = [
            f"Frame: {frame_idx}",
            f"Persons: {len(persons)}",
            f"Helmets: {len(helmets)}",
            f"Violations: {self.stats['violations_logged']}"
        ]

        y_offset = 30
        for text in stats_text:
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, (255, 255, 255), 2)
            y_offset += 25

        return frame

    def run(self, source: str, output_name: Optional[str] = None):
        """
        Run inference on video source.

        Args:
            source: Video file path, RTSP URL, or webcam index
            output_name: Output video filename (optional)
        """
        print(f"\n▶️  Starting inference...")
        print(f"   Source: {source}")

        # Open video
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {source}")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n📹 Video info:")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Total frames: {total_frames}")

        # Setup video writer
        video_writer = None
        if self.save_video:
            if output_name is None:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"inference_{self.camera_id}_{timestamp_str}.avi"

            output_path = self.output_dir / output_name
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            print(f"\n💾 Saving output to: {output_path}")

        # Processing loop
        frame_idx = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Calculate timestamp
                timestamp = time.time()

                # Process frame
                annotated_frame = self.process_frame(frame, frame_idx, timestamp)

                # Save frame
                if video_writer is not None:
                    video_writer.write(annotated_frame)

                # Update stats
                self.stats['frames_processed'] += 1
                frame_idx += 1

                # Progress update every 30 frames
                if frame_idx % 30 == 0:
                    elapsed = time.time() - start_time
                    fps_actual = frame_idx / elapsed if elapsed > 0 else 0
                    progress = (frame_idx / total_frames * 100) if total_frames > 0 else 0
                    print(f"   Progress: {frame_idx}/{total_frames} ({progress:.1f}%) | "
                          f"FPS: {fps_actual:.1f} | Violations: {self.stats['violations_logged']}")

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")

        finally:
            # Cleanup
            cap.release()
            if video_writer is not None:
                video_writer.release()
            cv2.destroyAllWindows()

            # Print final statistics
            self.print_statistics(start_time)

    def print_statistics(self, start_time: float):
        """Print final processing statistics."""
        elapsed = time.time() - start_time

        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        print(f"\n⏱️  Time: {elapsed:.2f}s")
        print(f"📊 Statistics:")
        print(f"   Frames processed: {self.stats['frames_processed']}")
        print(f"   Avg FPS: {self.stats['frames_processed'] / elapsed:.2f}")
        print(f"   Persons detected: {self.stats['persons_detected']}")
        print(f"   Helmets detected: {self.stats['helmets_detected']}")
        print(f"   Jackets detected: {self.stats['jackets_detected']}")
        print(f"   Violations detected: {self.stats['violations_detected']}")
        print(f"   Violations logged: {self.stats['violations_logged']}")

        print(f"\n📁 Output:")
        print(f"   Video: {self.output_dir}")
        print(f"   Events: {self.events_writer.out_dir}")
        print("\n✅ Done!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='PPE-Watch Inference Service')
    parser.add_argument('--source', required=True, help='Video file, RTSP URL, or webcam index')
    parser.add_argument('--camera-id', default='cam_1', help='Camera identifier')
    parser.add_argument('--model', required=True, help='Path to trained PPE model')
    parser.add_argument('--zones', required=True, help='Path to zones config JSON')
    parser.add_argument('--person-model', default='yolov8n.pt', help='Person detector model')
    parser.add_argument('--conf', type=float, default=0.5, help='Confidence threshold')
    parser.add_argument('--output', help='Output video filename')
    parser.add_argument('--no-save', action='store_true', help='Disable video saving')

    args = parser.parse_args()

    # Create inference service
    service = PPEWatchInference(
        ppe_model_path=args.model,
        zones_config_path=args.zones,
        camera_id=args.camera_id,
        person_model_path=args.person_model,
        conf_threshold=args.conf,
        save_video=not args.no_save
    )

    # Run inference
    service.run(args.source, output_name=args.output)


if __name__ == '__main__':
    main()
