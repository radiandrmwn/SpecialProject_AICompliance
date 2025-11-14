# PPE-Watch Quick Start Guide

Get started with the PPE-Watch helmet compliance detection system in minutes.

## Prerequisites

- Python 3.10 or higher
- NVIDIA GPU with CUDA (recommended) or CPU
- Git
- 4GB+ RAM
- 10GB+ disk space for dataset and models

## Installation

### 1. Clone and Setup Virtual Environment

```bash
# Navigate to project directory
cd "SpecialProject"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (CMD):
.venv\Scripts\activate.bat

# Linux/Mac:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

This will install:
- YOLOv8 (Ultralytics)
- OpenCV
- PyTorch
- And all other dependencies

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (use notepad, nano, or VS Code)
notepad .env  # Windows
nano .env     # Linux/Mac
```

Key settings to configure:
- `WHATSAPP_TOKEN`: Your WhatsApp Business API token
- `WHATSAPP_PHONE_NUMBER_ID`: Your phone number ID
- `WHATSAPP_TO`: Recipient phone number
- `TIMEZONE`: Your timezone (default: Asia/Taipei)

## Prepare Dataset

### Option 1: Download Sample Dataset

Visit [Safety Helmet and Reflective Jacket Dataset](https://datasetninja.com/safety-helmet-and-reflective-jacket) and download the dataset.

### Option 2: Use Your Own Data

Organize your dataset in YOLO format:

```
data/
├── images/
│   ├── train/
│   │   ├── image1.jpg
│   │   └── image2.jpg
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    │   ├── image1.txt
    │   └── image2.txt
    ├── val/
    └── test/
```

Label format (YOLO):
```
class_id x_center y_center width height
0 0.5 0.3 0.2 0.4
```

Where:
- `class_id`: 0 = safety_helmet, 1 = reflective_jacket
- Coordinates are normalized (0-1)

### Verify Dataset

```bash
python scripts/verify_dataset.py
```

This will check for:
- Missing image/label pairs
- Invalid class IDs
- Malformed annotations
- Empty label files

## Train Model

### Quick Training (50 epochs, default settings)

```bash
# Linux/Mac:
bash scripts/train_yolo.sh

# Windows (Git Bash):
bash scripts/train_yolo.sh

# Windows (PowerShell/CMD):
yolo detect train data=data/helmet.yaml model=yolov8s.pt imgsz=640 epochs=50 batch=16 project=runs/helmet
```

### Custom Training

```bash
# Set custom parameters
export EPOCHS=100
export BATCH=32
export IMGSZ=960

bash scripts/train_yolo.sh
```

Training will output:
- Model weights: `runs/helmet/train/weights/best.pt`
- Training plots: `runs/helmet/train/`
- Results CSV: `runs/helmet/train/results.csv`

Target metrics:
- mAP50 ≥ 0.85
- mAP50-95 ≥ 0.65

## Test Inference

### On Images

```bash
yolo predict model=runs/helmet/train/weights/best.pt source=path/to/test/image.jpg
```

### On Video

```bash
python -m src.inference.service \
  --source path/to/video.mp4 \
  --camera-id cam_1 \
  --model runs/helmet/train/weights/best.pt \
  --zones configs/zones.json \
  --conf 0.5
```

### On Webcam (Live)

```bash
python -m src.inference.service \
  --source 0 \
  --camera-id webcam \
  --model runs/helmet/train/weights/best.pt \
  --zones configs/zones.json
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rules.py -v

# Run with coverage
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/
```

## Configure Zones

Edit [configs/zones.json](configs/zones.json) to define monitoring zones:

```json
{
  "cam_1": {
    "name": "Construction Site Camera 1",
    "polygons": [
      {
        "name": "CraneBay",
        "points": [[120, 80], [900, 80], [900, 600], [120, 600]],
        "mandatory_helmet": true
      }
    ]
  }
}
```

To find polygon coordinates:
1. Open a sample frame from your video in an image editor
2. Note the pixel coordinates of the zone corners
3. Add them to the config in clockwise or counter-clockwise order

## Generate Reports

```bash
# Generate report for specific date
python -m src.reporting.aggregate_day --date 2025-11-01

# Output:
# - reports/report_2025-11-01.csv
# - reports/report_2025-11-01.png
# - reports/report_2025-11-01.pdf (if configured)
```

## VS Code Integration

If using VS Code:

1. Open project folder in VS Code
2. Select Python interpreter: `.venv/Scripts/python.exe`
3. Use configured tasks:
   - `Ctrl+Shift+B` → "train:helmet" to train
   - `Ctrl+Shift+P` → "Run Task" → "verify:dataset"
   - `F5` to run inference with debugger

## Troubleshooting

### CUDA/GPU Issues

If you get CUDA errors:

```bash
# Test PyTorch GPU
python -c "import torch; print(torch.cuda.is_available())"

# If False, install CPU version:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows CMD
```

### WhatsApp API Errors

- Verify token and phone number ID in `.env`
- Check WhatsApp Business API quota limits
- Ensure recipient number is in E.164 format (+country_code + number)

## Next Steps

1. **Improve Model**: Collect more training data, increase epochs, try larger models (yolov8m, yolov8l)
2. **Tune Zones**: Adjust polygon coordinates to match your camera views
3. **Deploy**: Set up cron job for daily reports
4. **Monitor**: Review violation trends and adjust thresholds

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/your-repo/issues)
- Documentation: See [CLAUDE.md](CLAUDE.md) for detailed architecture
- Dataset: [Safety Helmet Dataset](https://datasetninja.com/safety-helmet-and-reflective-jacket)

## License

[Your License]
