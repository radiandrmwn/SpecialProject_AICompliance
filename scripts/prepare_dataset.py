#!/usr/bin/env python3
"""
Dataset preparation script for Safety Helmet and Reflective Jacket dataset.

This script:
1. Extracts the downloaded dataset
2. Converts JSON annotations to YOLO format
3. Organizes files into train/val/test splits
4. Validates the conversion
"""

import os
import json
import shutil
import tarfile
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class DatasetConverter:
    """Convert DatasetNinja format to YOLO format."""

    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)

        # Class mapping from dataset
        self.class_mapping = {
            'safety helmet': 0,
            'reflective jacket': 1
        }

        self.stats = {
            'total_images': 0,
            'total_annotations': 0,
            'skipped': 0,
            'errors': []
        }

    def extract_tar(self, tar_path: str) -> bool:
        """Extract tar archive."""
        print(f"Extracting {tar_path}...")

        try:
            with tarfile.open(tar_path, 'r') as tar:
                tar.extractall(path=self.source_dir)
            print(f"✅ Extraction complete")
            return True
        except Exception as e:
            print(f"❌ Error extracting tar file: {e}")
            print(f"\n⚠️  The tar file might be corrupted or incomplete.")
            print(f"Please try re-downloading from:")
            print(f"https://datasetninja.com/safety-helmet-and-reflective-jacket")
            return False

    def convert_annotation(
        self,
        json_path: Path,
        img_width: int,
        img_height: int
    ) -> List[str]:
        """
        Convert JSON annotation to YOLO format.

        Returns list of YOLO annotation lines.
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            yolo_lines = []

            # Check if objects exist
            if 'objects' not in data:
                return yolo_lines

            for obj in data['objects']:
                # Get class name and ID
                class_title = obj.get('classTitle', '').lower()

                if class_title not in self.class_mapping:
                    continue

                class_id = self.class_mapping[class_title]

                # Get bounding box points
                if 'points' not in obj or 'exterior' not in obj['points']:
                    continue

                points = obj['points']['exterior']
                if len(points) != 2:
                    continue

                # Extract coordinates
                x1, y1 = points[0]
                x2, y2 = points[1]

                # Convert to YOLO format (normalized center x, center y, width, height)
                x_center = ((x1 + x2) / 2) / img_width
                y_center = ((y1 + y2) / 2) / img_height
                width = abs(x2 - x1) / img_width
                height = abs(y2 - y1) / img_height

                # Ensure values are in [0, 1]
                x_center = max(0, min(1, x_center))
                y_center = max(0, min(1, y_center))
                width = max(0, min(1, width))
                height = max(0, min(1, height))

                # Create YOLO line
                yolo_line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                yolo_lines.append(yolo_line)

            return yolo_lines

        except Exception as e:
            self.stats['errors'].append(f"Error processing {json_path}: {e}")
            return []

    def get_image_size(self, json_path: Path) -> Tuple[int, int]:
        """Get image dimensions from JSON metadata."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            size = data.get('size', {})
            width = size.get('width', 0)
            height = size.get('height', 0)

            return width, height

        except Exception as e:
            print(f"Warning: Could not read image size from {json_path}: {e}")
            return 0, 0

    def process_split(self, split_name: str):
        """Process a single split (train/val/test)."""
        print(f"\nProcessing {split_name} split...")

        # Paths
        split_dir = self.source_dir / split_name
        img_source = split_dir / 'img'
        ann_source = split_dir / 'ann'

        img_dest = self.output_dir / 'images' / split_name
        lbl_dest = self.output_dir / 'labels' / split_name

        # Create output directories
        img_dest.mkdir(parents=True, exist_ok=True)
        lbl_dest.mkdir(parents=True, exist_ok=True)

        # Check if source exists
        if not img_source.exists():
            print(f"⚠️  Warning: {img_source} does not exist, skipping...")
            return

        # Get all image files
        image_files = list(img_source.glob('*.jpg')) + list(img_source.glob('*.png'))
        print(f"Found {len(image_files)} images")

        converted = 0
        for img_path in image_files:
            # Find corresponding annotation
            ann_path = ann_source / f"{img_path.name}.json"

            if not ann_path.exists():
                print(f"⚠️  No annotation for {img_path.name}, skipping")
                self.stats['skipped'] += 1
                continue

            # Get image size
            img_width, img_height = self.get_image_size(ann_path)

            if img_width == 0 or img_height == 0:
                # Try to get size from actual image
                try:
                    from PIL import Image
                    with Image.open(img_path) as img:
                        img_width, img_height = img.size
                except:
                    print(f"⚠️  Could not determine size for {img_path.name}, skipping")
                    self.stats['skipped'] += 1
                    continue

            # Convert annotation
            yolo_lines = self.convert_annotation(ann_path, img_width, img_height)

            if not yolo_lines:
                print(f"⚠️  No valid annotations for {img_path.name}, skipping")
                self.stats['skipped'] += 1
                continue

            # Copy image
            shutil.copy2(img_path, img_dest / img_path.name)

            # Write YOLO label
            label_path = lbl_dest / f"{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

            converted += 1
            self.stats['total_images'] += 1
            self.stats['total_annotations'] += len(yolo_lines)

            if converted % 100 == 0:
                print(f"  Converted {converted} images...")

        print(f"✅ Converted {converted} images for {split_name}")

    def convert_all(self):
        """Convert entire dataset."""
        print("=" * 60)
        print("Dataset Conversion: DatasetNinja → YOLO Format")
        print("=" * 60)

        # Process each split
        for split in ['train', 'val', 'test']:
            self.process_split(split)

        # Print statistics
        print("\n" + "=" * 60)
        print("Conversion Complete!")
        print("=" * 60)
        print(f"\nStatistics:")
        print(f"  Total images converted: {self.stats['total_images']}")
        print(f"  Total annotations: {self.stats['total_annotations']}")
        print(f"  Skipped: {self.stats['skipped']}")

        if self.stats['errors']:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:10]:
                print(f"  - {err}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print(f"\n✅ Dataset ready for training!")
        print(f"   Images: {self.output_dir / 'images'}")
        print(f"   Labels: {self.output_dir / 'labels'}")


def main():
    parser = argparse.ArgumentParser(description='Prepare helmet dataset for YOLO training')
    parser.add_argument(
        '--tar',
        type=str,
        default='data/safety-helmet-and-reflective-jacket-DatasetNinja.tar',
        help='Path to tar archive'
    )
    parser.add_argument(
        '--extract-dir',
        type=str,
        default='data/extracted',
        help='Directory to extract archive to'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for YOLO format dataset'
    )
    parser.add_argument(
        '--skip-extract',
        action='store_true',
        help='Skip extraction (if already extracted)'
    )

    args = parser.parse_args()

    # Create converter
    converter = DatasetConverter(
        source_dir=args.extract_dir,
        output_dir=args.output_dir
    )

    # Extract if needed
    if not args.skip_extract and os.path.exists(args.tar):
        success = converter.extract_tar(args.tar)
        if not success:
            print("\n" + "=" * 60)
            print("ALTERNATIVE: Manual Extraction")
            print("=" * 60)
            print(f"1. Extract the tar file manually using WinRAR or 7-Zip")
            print(f"2. Extract to: {args.extract_dir}")
            print(f"3. Re-run this script with --skip-extract flag:")
            print(f"   python scripts/prepare_dataset.py --skip-extract")
            return

    # Convert dataset
    if os.path.exists(args.extract_dir):
        converter.convert_all()

        # Verify
        print("\n" + "=" * 60)
        print("Running verification...")
        print("=" * 60)
        os.system(f"python scripts/verify_dataset.py --data {args.output_dir}/helmet.yaml")
    else:
        print(f"❌ Error: Extract directory not found: {args.extract_dir}")
        print(f"Please extract the dataset first or check the path.")


if __name__ == '__main__':
    main()
