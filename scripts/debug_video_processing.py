"""
Debug script to understand why tracking is broken.

Processes a video and logs detailed information about:
- How many people detected per frame
- Track IDs and their persistence
- Helmet/vest detections
"""

import cv2
from pathlib import Path
from ultralytics import YOLO
import sys

def debug_process_video(video_path: str):
    """Process video with detailed logging."""

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return

    print(f"🔍 DEBUG: Processing {video_path.name}\n")

    # Load models
    helmet_model = YOLO("runs/helmet/train4/weights/best.pt")
    person_model = YOLO("yolov8s.pt")

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"📹 Video: {fps:.1f}fps, {total_frames} frames\n")
    print("=" * 80)

    frame_idx = 0
    sample_rate = 4

    # Track what IDs we've seen
    all_track_ids = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Run person tracking on EVERY frame
        person_results = person_model.track(
            frame,
            classes=[0],
            conf=0.25,
            persist=True,
            verbose=False
        )

        # Check if we should process this frame
        is_sampled = (frame_idx % sample_rate == 0)

        if is_sampled:
            print(f"\n📍 FRAME {frame_idx} (sampled)")
            print("-" * 80)

            # Check person detections
            if person_results[0].boxes is not None and len(person_results[0].boxes) > 0:
                print(f"   👥 Persons detected: {len(person_results[0].boxes)}")

                for i, box in enumerate(person_results[0].boxes):
                    track_id = None
                    if box.id is not None:
                        track_id = int(box.id[0])
                        all_track_ids.add(track_id)

                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                    print(f"      Person {i+1}: Track ID={track_id}, Confidence={conf:.2f}, "
                          f"Box=[{int(x1)},{int(y1)},{int(x2)},{int(y2)}]")

                # Detect helmets/vests
                helmet_results = helmet_model.track(
                    frame,
                    conf=0.25,
                    persist=False,
                    verbose=False
                )

                if helmet_results[0].boxes is not None and len(helmet_results[0].boxes) > 0:
                    helmets = 0
                    vests = 0
                    for box in helmet_results[0].boxes:
                        cls_id = int(box.cls[0])
                        if cls_id == 0:
                            helmets += 1
                        elif cls_id == 1:
                            vests += 1

                    print(f"   🎩 PPE detected: {helmets} helmets, {vests} vests")
                else:
                    print(f"   ⚠️  NO helmets or vests detected!")
            else:
                print(f"   ⚠️  NO persons detected!")
        else:
            # Non-sampled frame - just track quietly
            if person_results[0].boxes is not None:
                track_ids_this_frame = []
                for box in person_results[0].boxes:
                    if box.id is not None:
                        track_id = int(box.id[0])
                        track_ids_this_frame.append(track_id)
                        all_track_ids.add(track_id)

                if frame_idx % 20 == 0:  # Print every 20 frames
                    print(f"Frame {frame_idx}: Tracking {len(track_ids_this_frame)} persons, "
                          f"IDs={track_ids_this_frame}")

    cap.release()

    print("\n" + "=" * 80)
    print(f"📊 SUMMARY")
    print("=" * 80)
    print(f"Total frames processed: {frame_idx}")
    print(f"Sampled frames: {frame_idx // sample_rate}")
    print(f"All track IDs seen: {sorted(all_track_ids)}")
    print(f"Total unique IDs: {len(all_track_ids)}")

    if len(all_track_ids) > 3:
        print(f"\n⚠️  WARNING: More than 3 unique track IDs detected!")
        print(f"   This indicates tracking instability.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_video_processing.py <video_path>")
        print("\nExample:")
        print("  python scripts/debug_video_processing.py samples/Sample_Video1SP.mp4")
        sys.exit(1)

    debug_process_video(sys.argv[1])
