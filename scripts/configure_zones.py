#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Zone Configuration Tool

Helps you define zone polygons by clicking points on a video frame.
Saves the zones to configs/zones.json
"""

import sys
import json
import cv2
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class ZoneConfigurator:
    """Interactive tool to define zones on video frames."""

    def __init__(self, video_path: str, camera_id: str = "cam_1"):
        self.video_path = Path(video_path)
        self.camera_id = camera_id
        self.zones = []
        self.current_points = []
        self.frame = None
        self.display_frame = None

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks to define polygon points."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Add point to current polygon
            self.current_points.append([x, y])
            print(f"   Point {len(self.current_points)}: ({x}, {y})")

            # Redraw
            self.draw_zones()

    def draw_zones(self):
        """Draw all zones and current polygon on the frame."""
        self.display_frame = self.frame.copy()

        # Draw completed zones
        for zone in self.zones:
            pts = zone['points']
            if len(pts) >= 3:
                pts_array = np.array(pts, np.int32)
                cv2.polylines(self.display_frame, [pts_array], True, (0, 255, 0), 2)
                # Add label
                centroid_x = int(sum(p[0] for p in pts) / len(pts))
                centroid_y = int(sum(p[1] for p in pts) / len(pts))
                cv2.putText(self.display_frame, zone['name'],
                           (centroid_x, centroid_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw current polygon being created
        if len(self.current_points) > 0:
            for pt in self.current_points:
                cv2.circle(self.display_frame, tuple(pt), 5, (0, 0, 255), -1)

            if len(self.current_points) >= 2:
                pts_array = np.array(self.current_points, np.int32)
                cv2.polylines(self.display_frame, [pts_array], False, (0, 165, 255), 2)

        # Add instructions
        instructions = [
            "Left click: Add point",
            "Enter: Finish polygon",
            "C: Clear current polygon",
            "S: Save all zones",
            "Q: Quit without saving"
        ]

        y_offset = 30
        for instruction in instructions:
            cv2.putText(self.display_frame, instruction, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 25

        cv2.imshow('Zone Configuration', self.display_frame)

    def run(self):
        """Run the interactive configuration tool."""
        print("=" * 70)
        print("Interactive Zone Configuration")
        print("=" * 70)
        print(f"\nVideo: {self.video_path}")
        print(f"Camera ID: {self.camera_id}")

        # Load first frame from video
        cap = cv2.VideoCapture(str(self.video_path))
        ret, self.frame = cap.read()
        cap.release()

        if not ret:
            print("Error: Could not read video frame")
            return

        print(f"\nFrame size: {self.frame.shape[1]}x{self.frame.shape[0]}")
        print("\nInstructions:")
        print("1. Click points to define a polygon zone (clockwise order recommended)")
        print("2. Press ENTER to finish the current polygon")
        print("3. Press 'C' to clear the current polygon")
        print("4. Press 'S' to save all zones to configs/zones.json")
        print("5. Press 'Q' to quit without saving")
        print("\n" + "=" * 70)

        # Create window and set mouse callback
        cv2.namedWindow('Zone Configuration', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Zone Configuration', 1280, 720)
        cv2.setMouseCallback('Zone Configuration', self.mouse_callback)

        self.draw_zones()

        while True:
            key = cv2.waitKey(1) & 0xFF

            # Enter - finish current polygon
            if key == 13 or key == ord('\r'):
                if len(self.current_points) >= 3:
                    zone_name = input("\nEnter zone name (e.g., LoadingDock, MachineryArea): ").strip()
                    if zone_name:
                        mandatory = input("Is helmet mandatory in this zone? (y/n): ").strip().lower() == 'y'

                        zone = {
                            'name': zone_name,
                            'points': self.current_points.copy(),
                            'mandatory_helmet': mandatory
                        }
                        self.zones.append(zone)
                        print(f"\n✅ Zone '{zone_name}' saved with {len(self.current_points)} points")
                        print(f"   Helmet mandatory: {mandatory}")

                        self.current_points = []
                        self.draw_zones()
                else:
                    print("\n⚠️  Need at least 3 points to define a polygon")

            # C - clear current polygon
            elif key == ord('c') or key == ord('C'):
                if self.current_points:
                    print("\n🗑️  Current polygon cleared")
                    self.current_points = []
                    self.draw_zones()

            # S - save zones
            elif key == ord('s') or key == ord('S'):
                if self.zones:
                    self.save_zones()
                    break
                else:
                    print("\n⚠️  No zones to save. Define at least one zone first.")

            # Q - quit
            elif key == ord('q') or key == ord('Q'):
                print("\n👋 Exiting without saving")
                break

        cv2.destroyAllWindows()

    def save_zones(self):
        """Save zones to configs/zones.json"""
        config_file = Path("configs/zones.json")

        # Load existing config if it exists
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # Update or create camera config
        config[self.camera_id] = {
            'name': f'Camera {self.camera_id}',
            'polygons': self.zones
        }

        # Save to file
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print("\n" + "=" * 70)
        print("✅ Zones saved successfully!")
        print("=" * 70)
        print(f"\nConfiguration file: {config_file}")
        print(f"Camera ID: {self.camera_id}")
        print(f"Total zones: {len(self.zones)}")
        print("\nZones:")
        for i, zone in enumerate(self.zones, 1):
            print(f"  {i}. {zone['name']} ({len(zone['points'])} points, helmet={'required' if zone['mandatory_helmet'] else 'optional'})")

        print("\n💡 Next steps:")
        print(f"  1. Run inference again: python -m src.inference.service --source {self.video_path} --camera-id {self.camera_id}")
        print("  2. Generate new report with your custom zones")


def main():
    """Main entry point."""
    import argparse
    import numpy as np  # Import here for the tool
    globals()['np'] = np  # Make available to class

    parser = argparse.ArgumentParser(description='Configure zones interactively')
    parser.add_argument('--video', required=True, help='Path to video file')
    parser.add_argument('--camera-id', default='cam_1', help='Camera identifier')

    args = parser.parse_args()

    try:
        configurator = ZoneConfigurator(args.video, args.camera_id)
        configurator.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
