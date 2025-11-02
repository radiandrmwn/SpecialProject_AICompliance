#!/usr/bin/env bash
# Training script for helmet detection model
set -e

echo "=================================="
echo "PPE-Watch Helmet Detection Training"
echo "=================================="

# Configuration
DATA_YAML="${DATA_YAML:-data/helmet.yaml}"
MODEL="${MODEL:-yolov8s.pt}"
IMGSZ="${IMGSZ:-640}"
EPOCHS="${EPOCHS:-50}"
BATCH="${BATCH:-16}"
PROJECT="${PROJECT:-runs/helmet}"
DEVICE="${DEVICE:-0}"  # 0 for GPU, cpu for CPU

echo ""
echo "Configuration:"
echo "  Data config: $DATA_YAML"
echo "  Base model: $MODEL"
echo "  Image size: $IMGSZ"
echo "  Epochs: $EPOCHS"
echo "  Batch size: $BATCH"
echo "  Output project: $PROJECT"
echo "  Device: $DEVICE"
echo ""

# Check if data config exists
if [ ! -f "$DATA_YAML" ]; then
    echo "❌ Error: Data config not found: $DATA_YAML"
    exit 1
fi

# Create output directory
mkdir -p "$PROJECT"

echo "Starting training..."
echo ""

# Train
yolo detect train \
    data="$DATA_YAML" \
    model="$MODEL" \
    imgsz="$IMGSZ" \
    epochs="$EPOCHS" \
    batch="$BATCH" \
    project="$PROJECT" \
    device="$DEVICE" \
    patience=10 \
    save=true \
    plots=true \
    verbose=true

echo ""
echo "=================================="
echo "Training completed!"
echo "Model saved to: $PROJECT/train/weights/best.pt"
echo "=================================="
echo ""

# Validate
echo "Running validation..."
yolo detect val \
    data="$DATA_YAML" \
    model="$PROJECT/train/weights/best.pt" \
    imgsz="$IMGSZ" \
    device="$DEVICE"

echo ""
echo "=================================="
echo "Validation completed!"
echo "=================================="
echo ""

# Print metrics summary
echo "Training Summary:"
if [ -f "$PROJECT/train/results.csv" ]; then
    echo "  Results saved to: $PROJECT/train/results.csv"
    echo ""
    echo "  Final metrics (last epoch):"
    tail -1 "$PROJECT/train/results.csv" | awk -F',' '{
        printf "    mAP50: %.4f\n", $9
        printf "    mAP50-95: %.4f\n", $10
    }'
else
    echo "  ⚠️  Results file not found"
fi

echo ""
echo "✅ Training pipeline completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Review training plots in: $PROJECT/train/"
echo "  2. Test model: yolo predict model=$PROJECT/train/weights/best.pt source=<image_or_video>"
echo "  3. Export model: bash scripts/export_model.sh"
echo ""
