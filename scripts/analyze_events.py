"""
Analyze events CSV to understand why violation count is higher than expected.

Shows:
- Which track IDs were detected
- When each ID first appeared
- Timeline of ID changes
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


def analyze_events(events_csv_path: Path):
    """Analyze events to understand track ID behavior."""

    if not events_csv_path.exists():
        print(f"❌ Events file not found: {events_csv_path}")
        return

    # Read events
    df = pd.read_csv(events_csv_path)

    print("=" * 70)
    print(f"📊 Events Analysis: {events_csv_path.name}")
    print("=" * 70)

    print(f"\n📈 Total Events: {len(df)}")
    print(f"   Violations: {len(df[df['has_helmet'] == False])}")

    # Analyze track IDs
    unique_track_ids = df['track_id'].unique()
    print(f"\n🆔 Unique Track IDs Detected: {len(unique_track_ids)}")
    print(f"   Track IDs: {sorted(unique_track_ids)}")

    # Violation vs compliant by track ID
    print(f"\n📋 Track ID Breakdown:")
    print("-" * 70)
    for track_id in sorted(unique_track_ids):
        track_df = df[df['track_id'] == track_id]
        violations = len(track_df[track_df['has_helmet'] == False])
        compliant = len(track_df[track_df['has_helmet'] == True])
        first_frame = track_df['frame_idx'].min()
        last_frame = track_df['frame_idx'].max()
        duration_frames = last_frame - first_frame + 1

        status = "VIOLATOR" if violations > 0 else "COMPLIANT"
        print(f"   Track ID {track_id:2d}: {status:10s} | "
              f"Frames {first_frame:4d}-{last_frame:4d} ({duration_frames:3d} frames) | "
              f"Violations: {violations:3d}, Compliant: {compliant:3d}")

    # Timeline analysis - show when IDs appear/disappear
    print(f"\n⏱️  Timeline of Track ID Changes:")
    print("-" * 70)

    # Group by frame and show which IDs are present
    frames_with_changes = []
    prev_ids = set()

    for frame_idx in sorted(df['frame_idx'].unique()):
        frame_df = df[df['frame_idx'] == frame_idx]
        current_ids = set(frame_df['track_id'].unique())

        # Check for new IDs or disappeared IDs
        new_ids = current_ids - prev_ids
        disappeared_ids = prev_ids - current_ids

        if new_ids or disappeared_ids:
            frames_with_changes.append({
                'frame': frame_idx,
                'new': new_ids,
                'disappeared': disappeared_ids,
                'present': current_ids
            })

        prev_ids = current_ids

    if frames_with_changes:
        print("\n   Frame | Event | Track IDs")
        print("   " + "-" * 50)
        for change in frames_with_changes[:20]:  # Show first 20 changes
            frame = change['frame']
            if change['new']:
                print(f"   {frame:5d} | NEW:  {sorted(change['new'])}")
            if change['disappeared']:
                print(f"   {frame:5d} | LOST: {sorted(change['disappeared'])}")
            print(f"         | Present: {sorted(change['present'])}")

        if len(frames_with_changes) > 20:
            print(f"   ... and {len(frames_with_changes) - 20} more changes")

    # Summary
    print(f"\n" + "=" * 70)
    print(f"📊 SUMMARY")
    print("=" * 70)

    violator_ids = df[df['has_helmet'] == False]['track_id'].unique()
    compliant_ids = df[df['has_helmet'] == True]['track_id'].unique()

    print(f"Violator Track IDs: {sorted(violator_ids)}")
    print(f"Compliant Track IDs: {sorted(compliant_ids)}")
    print(f"\nTotal unique violator IDs: {len(violator_ids)}")
    print(f"Total unique compliant IDs: {len(compliant_ids)}")

    if len(violator_ids) > 2:
        print(f"\n⚠️  WARNING: {len(violator_ids)} violator IDs detected!")
        print(f"   This suggests track ID reassignment is occurring.")
        print(f"   Check the timeline above to see when IDs changed.")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        events_path = Path(sys.argv[1])
    else:
        # Use today's events by default
        today = datetime.now().strftime('%Y-%m-%d')
        events_path = Path(f"events/events_{today}.csv")

    analyze_events(events_path)
