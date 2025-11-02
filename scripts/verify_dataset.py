#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Verification Script for YOLO Format
Checks for:
- Missing pairs (image without label, label without image)
- Empty label files
- Invalid class IDs
- Malformed annotation lines
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Set
import yaml

# Fix Windows encoding for emoji output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class DatasetVerifier:
    def __init__(self, data_yaml_path: str):
        """Initialize verifier with dataset config."""
        self.data_yaml_path = Path(data_yaml_path)
        self.config = self._load_config()
        self.base_path = self.data_yaml_path.parent / self.config['path']
        self.valid_classes = set(range(self.config['nc']))

        # Image extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}

        # Results tracking
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_images': 0,
            'total_labels': 0,
            'missing_labels': 0,
            'missing_images': 0,
            'empty_labels': 0,
            'invalid_class_ids': 0,
            'malformed_lines': 0
        }

    def _load_config(self) -> dict:
        """Load and validate YAML config."""
        if not self.data_yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.data_yaml_path}")

        with open(self.data_yaml_path, 'r') as f:
            config = yaml.safe_load(f)

        required_keys = ['path', 'train', 'val', 'nc', 'names']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required key in config: {key}")

        return config

    def _get_image_label_pairs(self, split: str) -> Tuple[Set[str], Set[str]]:
        """Get sets of image and label file stems for a split."""
        images_dir = self.base_path / self.config[split]
        labels_dir = self.base_path / 'labels' / split

        # Get image files
        image_stems = set()
        if images_dir.exists():
            for img_path in images_dir.iterdir():
                if img_path.suffix.lower() in self.image_extensions:
                    image_stems.add(img_path.stem)

        # Get label files
        label_stems = set()
        if labels_dir.exists():
            for lbl_path in labels_dir.iterdir():
                if lbl_path.suffix == '.txt':
                    label_stems.add(lbl_path.stem)

        return image_stems, label_stems

    def _verify_label_content(self, label_path: Path) -> List[str]:
        """Verify label file content and return errors."""
        errors = []

        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()

            if len(lines) == 0:
                self.stats['empty_labels'] += 1
                self.warnings.append(f"Empty label file: {label_path}")
                return errors

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) != 5:
                    self.stats['malformed_lines'] += 1
                    errors.append(
                        f"{label_path}:{line_num} - Expected 5 values (class x y w h), "
                        f"got {len(parts)}"
                    )
                    continue

                try:
                    class_id = int(parts[0])
                    x_center, y_center, width, height = map(float, parts[1:5])

                    # Validate class ID
                    if class_id not in self.valid_classes:
                        self.stats['invalid_class_ids'] += 1
                        errors.append(
                            f"{label_path}:{line_num} - Invalid class ID {class_id}. "
                            f"Valid range: 0-{self.config['nc']-1}"
                        )

                    # Validate bbox coordinates (YOLO format: normalized 0-1)
                    if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and
                            0 <= width <= 1 and 0 <= height <= 1):
                        errors.append(
                            f"{label_path}:{line_num} - Bbox coordinates out of range [0,1]: "
                            f"x={x_center}, y={y_center}, w={width}, h={height}"
                        )

                    # Check for zero-area boxes
                    if width == 0 or height == 0:
                        self.warnings.append(
                            f"{label_path}:{line_num} - Zero-area bbox: w={width}, h={height}"
                        )

                except ValueError as e:
                    self.stats['malformed_lines'] += 1
                    errors.append(f"{label_path}:{line_num} - Cannot parse values: {e}")

        except Exception as e:
            errors.append(f"Error reading {label_path}: {e}")

        return errors

    def verify_split(self, split: str) -> None:
        """Verify a single data split (train/val/test)."""
        print(f"\n{'='*60}")
        print(f"Verifying {split.upper()} split...")
        print(f"{'='*60}")

        if split not in self.config:
            print(f"⚠️  Split '{split}' not defined in config, skipping.")
            return

        image_stems, label_stems = self._get_image_label_pairs(split)

        self.stats['total_images'] += len(image_stems)
        self.stats['total_labels'] += len(label_stems)

        # Check for missing labels
        missing_labels = image_stems - label_stems
        if missing_labels:
            self.stats['missing_labels'] += len(missing_labels)
            for stem in sorted(missing_labels):
                self.errors.append(f"{split}: Image without label - {stem}")

        # Check for missing images
        missing_images = label_stems - image_stems
        if missing_images:
            self.stats['missing_images'] += len(missing_images)
            for stem in sorted(missing_images):
                self.errors.append(f"{split}: Label without image - {stem}")

        # Verify label contents
        labels_dir = self.base_path / 'labels' / split
        if labels_dir.exists():
            for label_path in labels_dir.glob('*.txt'):
                if label_path.stem in image_stems:  # Only check if image exists
                    label_errors = self._verify_label_content(label_path)
                    self.errors.extend(label_errors)

        # Print split summary
        print(f"\n📊 {split.upper()} Summary:")
        print(f"   Images: {len(image_stems)}")
        print(f"   Labels: {len(label_stems)}")
        print(f"   Missing labels: {len(missing_labels)}")
        print(f"   Missing images: {len(missing_images)}")

    def verify_all(self) -> bool:
        """Verify all splits and print report."""
        print(f"\n{'*'*60}")
        print(f"YOLO Dataset Verification")
        print(f"Config: {self.data_yaml_path}")
        print(f"Base path: {self.base_path}")
        print(f"Classes ({self.config['nc']}): {', '.join(self.config['names'].values())}")
        print(f"{'*'*60}")

        # Verify each split
        for split in ['train', 'val', 'test']:
            self.verify_split(split)

        # Print final report
        print(f"\n{'='*60}")
        print("FINAL REPORT")
        print(f"{'='*60}")
        print(f"\n📈 Statistics:")
        print(f"   Total images: {self.stats['total_images']}")
        print(f"   Total labels: {self.stats['total_labels']}")
        print(f"   Missing labels: {self.stats['missing_labels']}")
        print(f"   Missing images: {self.stats['missing_images']}")
        print(f"   Empty labels: {self.stats['empty_labels']}")
        print(f"   Invalid class IDs: {self.stats['invalid_class_ids']}")
        print(f"   Malformed lines: {self.stats['malformed_lines']}")

        # Print errors
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:50], 1):  # Limit to first 50
                print(f"   {i}. {error}")
            if len(self.errors) > 50:
                print(f"   ... and {len(self.errors) - 50} more errors")

        # Print warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings[:20], 1):  # Limit to first 20
                print(f"   {i}. {warning}")
            if len(self.warnings) > 20:
                print(f"   ... and {len(self.warnings) - 20} more warnings")

        # Final verdict
        print(f"\n{'='*60}")
        if not self.errors:
            print("✅ Dataset verification PASSED!")
            print(f"{'='*60}\n")
            return True
        else:
            print(f"❌ Dataset verification FAILED with {len(self.errors)} errors!")
            print(f"{'='*60}\n")
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Verify YOLO dataset integrity')
    parser.add_argument(
        '--data',
        type=str,
        default='data/helmet.yaml',
        help='Path to dataset YAML config (default: data/helmet.yaml)'
    )

    args = parser.parse_args()

    try:
        verifier = DatasetVerifier(args.data)
        success = verifier.verify_all()
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
