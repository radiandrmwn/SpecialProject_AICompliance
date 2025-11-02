#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check GPU availability for training.
"""

import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("GPU Compatibility Check for YOLOv8 Training")
print("=" * 60)
print()

# Check PyTorch
try:
    import torch
    print("✅ PyTorch installed")
    print(f"   Version: {torch.__version__}")

    # Check CUDA
    cuda_available = torch.cuda.is_available()
    print(f"\n🔍 CUDA Available: {cuda_available}")

    if cuda_available:
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   GPU Device Count: {torch.cuda.device_count()}")
        print(f"\n💻 GPU Details:")
        for i in range(torch.cuda.device_count()):
            print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"      Memory: {props.total_memory / 1024**3:.2f} GB")
            print(f"      Compute Capability: {props.major}.{props.minor}")

        # Test GPU
        print(f"\n🧪 Testing GPU computation...")
        x = torch.rand(1000, 1000).cuda()
        y = torch.rand(1000, 1000).cuda()
        z = x @ y
        print("   ✅ GPU computation successful!")

        print(f"\n✅ **You can train YOLOv8 locally with GPU acceleration!**")
        print(f"   Estimated training speed: FAST (GPU)")

    else:
        print(f"\n⚠️  No CUDA GPU detected")
        print(f"   You can still train on CPU, but it will be much slower.")
        print(f"   Estimated training speed: SLOW (CPU - 10-20x slower)")
        print(f"\n💡 Recommendations:")
        print(f"   - Use Google Colab (free GPU)")
        print(f"   - Or train locally overnight on CPU")

except ImportError:
    print("❌ PyTorch not installed yet")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Check Ultralytics
print(f"\n{'=' * 60}")
try:
    import ultralytics
    print(f"✅ Ultralytics YOLOv8 installed")
    print(f"   Version: {ultralytics.__version__}")
except ImportError:
    print(f"❌ Ultralytics not installed yet")
    print(f"   Run: pip install -r requirements.txt")

# Memory recommendation
print(f"\n{'=' * 60}")
print(f"📊 Training Recommendations:")
print(f"{'=' * 60}")

if cuda_available and torch.cuda.device_count() > 0:
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    if gpu_mem >= 8:
        print(f"✅ GPU Memory: {gpu_mem:.1f}GB - Excellent for training")
        print(f"   Recommended batch size: 16-32")
        print(f"   Recommended image size: 640-960")
    elif gpu_mem >= 4:
        print(f"⚠️  GPU Memory: {gpu_mem:.1f}GB - Can train with smaller batches")
        print(f"   Recommended batch size: 8-16")
        print(f"   Recommended image size: 640")
    else:
        print(f"⚠️  GPU Memory: {gpu_mem:.1f}GB - Limited, consider Colab")
        print(f"   Recommended batch size: 4-8")
        print(f"   Recommended image size: 416-640")
else:
    print(f"💻 CPU Training:")
    print(f"   Recommended batch size: 4-8")
    print(f"   Recommended image size: 416-640")
    print(f"   Expected time for 50 epochs: 6-12 hours (depends on dataset size)")
    print(f"\n💡 Consider using Google Colab for faster training (free GPU)")

print(f"\n{'=' * 60}")
print(f"Next Steps:")
print(f"{'=' * 60}")
print(f"1. If GPU available: You're ready to train locally!")
print(f"2. If no GPU: Consider Google Colab or train on CPU overnight")
print(f"3. Prepare your dataset in data/ folder")
print(f"4. Run: bash scripts/train_yolo.sh")
print()
