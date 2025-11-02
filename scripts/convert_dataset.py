#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert extracted DatasetNinja dataset to YOLO format.
Handles the case where we only have test and valid splits.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from PIL import Image
import random

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Set random seed for reproducible splits
random.seed(42)


def convert_annotation(json_path, img_width, img_height):
    """Convert DatasetNinja JSON to YOLO format."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    class_mapping = {
        'safety_helmet': 0,
        'reflective_jacket': 1,
        # Also support versions with spaces (just in case)
        'safety helmet': 0,
        'reflective jacket': 1
    }

    yolo_lines = []

    if 'objects' not in data:
        return yolo_lines

    for obj in data['objects']:
        class_title = obj.get('classTitle', '')

        if class_title not in class_mapping:
            continue

        class_id = class_mapping[class_title]

        if 'points' not in obj or 'exterior' not in obj['points']:
            continue

        points = obj['points']['exterior']
        if len(points) != 2:
            continue

        x1, y1 = points[0]
        x2, y2 = points[1]

        # Convert to YOLO format
        x_center = ((x1 + x2) / 2) / img_width
        y_center = ((y1 + y2) / 2) / img_height
        width = abs(x2 - x1) / img_width
        height = abs(y2 - y1) / img_height

        # Clamp to [0, 1]
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))

        yolo_line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
        yolo_lines.append(yolo_line)

    return yolo_lines


def get_image_size_from_json(json_path):
    """Get image dimensions from JSON."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        size = data.get('size', {})
        return size.get('width', 0), size.get('height', 0)
    except:
        return 0, 0


def process_dataset():
    """Main conversion process."""
    print("=" * 70)
    print("Converting DatasetNinja → YOLO Format")
    print("=" * 70)

    source_dir = Path('data/extracted')
    output_dir = Path('data')

    # Create output directories
    for split in ['train', 'val', 'test']:
        (output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)

    stats = {'train': 0, 'val': 0, 'test': 0, 'skipped': 0}

    # Process 'test' folder (we'll keep it as test)
    print("\n📁 Processing test split...")
    test_img_dir = source_dir / 'test' / 'img'
    test_ann_dir = source_dir / 'test' / 'ann'

    if test_img_dir.exists():
        images = list(test_img_dir.glob('*.jpg'))
        print(f"   Found {len(images)} images in test")

        for img_path in images:
            ann_path = test_ann_dir / f"{img_path.name}.json"

            if not ann_path.exists():
                stats['skipped'] += 1
                continue

            # Get image size
            img_width, img_height = get_image_size_from_json(ann_path)
            if not img_width:
                try:
                    with Image.open(img_path) as img:
                        img_width, img_height = img.size
                except:
                    stats['skipped'] += 1
                    continue

            # Convert annotation
            yolo_lines = convert_annotation(ann_path, img_width, img_height)
            if not yolo_lines:
                stats['skipped'] += 1
                continue

            # Copy image and save label
            shutil.copy2(img_path, output_dir / 'images' / 'test' / img_path.name)
            label_path = output_dir / 'labels' / 'test' / f"{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

            stats['test'] += 1

            if stats['test'] % 100 == 0:
                print(f"   Processed {stats['test']} test images...")

    # Process 'train' folder (if it exists)
    print("\n📁 Processing train split...")
    train_img_dir = source_dir / 'train' / 'img'
    train_ann_dir = source_dir / 'train' / 'ann'

    if train_img_dir.exists():
        images = list(train_img_dir.glob('*.jpg'))
        print(f"   Found {len(images)} images in train")

        for img_path in images:
            ann_path = train_ann_dir / f"{img_path.name}.json"

            if not ann_path.exists():
                stats['skipped'] += 1
                continue

            img_width, img_height = get_image_size_from_json(ann_path)
            if not img_width:
                try:
                    with Image.open(img_path) as img:
                        img_width, img_height = img.size
                except:
                    stats['skipped'] += 1
                    continue

            yolo_lines = convert_annotation(ann_path, img_width, img_height)
            if not yolo_lines:
                stats['skipped'] += 1
                continue

            shutil.copy2(img_path, output_dir / 'images' / 'train' / img_path.name)
            label_path = output_dir / 'labels' / 'train' / f"{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

            stats['train'] += 1

            if stats['train'] % 500 == 0:
                print(f"   Processed {stats['train']} train images...")

    # Process 'valid' folder → use as validation
    print("\n📁 Processing valid split...")
    valid_img_dir = source_dir / 'valid' / 'img'
    valid_ann_dir = source_dir / 'valid' / 'ann'

    if valid_img_dir.exists():
        images = list(valid_img_dir.glob('*.jpg'))
        print(f"   Found {len(images)} images in valid")

        for img_path in images:
            ann_path = valid_ann_dir / f"{img_path.name}.json"

            if not ann_path.exists():
                stats['skipped'] += 1
                continue

            img_width, img_height = get_image_size_from_json(ann_path)
            if not img_width:
                try:
                    with Image.open(img_path) as img:
                        img_width, img_height = img.size
                except:
                    stats['skipped'] += 1
                    continue

            yolo_lines = convert_annotation(ann_path, img_width, img_height)
            if not yolo_lines:
                stats['skipped'] += 1
                continue

            shutil.copy2(img_path, output_dir / 'images' / 'val' / img_path.name)
            label_path = output_dir / 'labels' / 'val' / f"{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

            stats['val'] += 1

            if stats['val'] % 100 == 0:
                print(f"   Processed {stats['val']} val images...")

    # Print summary
    print("\n" + "=" * 70)
    print("✅ Conversion Complete!")
    print("=" * 70)
    print(f"\n📊 Statistics:")
    print(f"   Train images: {stats['train']}")
    print(f"   Val images:   {stats['val']}")
    print(f"   Test images:  {stats['test']}")
    print(f"   Total:        {stats['train'] + stats['val'] + stats['test']}")
    print(f"   Skipped:      {stats['skipped']}")

    print(f"\n📁 Output:")
    print(f"   Images: data/images/{{train,val,test}}/")
    print(f"   Labels: data/labels/{{train,val,test}}/")

    print(f"\n🎯 Next step:")
    print(f"   python scripts/verify_dataset.py")


if __name__ == '__main__':
    try:
        process_dataset()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
