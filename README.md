# PPE-Watch: Helmet Compliance Detection System

Computer-vision pipeline to detect workers without safety helmets inside important zones, aggregate daily stats, and send WhatsApp reports to supervisors.

## Features

- Real-time helmet and reflective jacket detection using YOLOv8
- Zone-based compliance monitoring with configurable polygon regions
- Person tracking to prevent double counting
- Daily automated reporting with CSV/PNG/PDF summaries
- WhatsApp integration for automated supervisor notifications

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -U pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your WhatsApp API credentials and settings
```

### 3. Prepare Dataset

Place your dataset in YOLO format:
- Images: `data/images/train/`, `data/images/val/`, `data/images/test/`
- Labels: `data/labels/train/`, `data/labels/val/`, `data/labels/test/`

Verify dataset integrity:
```bash
python scripts/verify_dataset.py
```

### 4. Train Model

```bash
bash scripts/train_yolo.sh
```

### 5. Run Inference

```bash
python -m src.inference.service --source <video_path> --camera-id cam_1
```

## Project Structure

```
ppe-watch/
├─ data/              # Dataset and annotations
├─ configs/           # Zone definitions and reporting config
├─ src/               # Source code
│  ├─ models/         # Training and validation
│  ├─ inference/      # Detection and tracking
│  ├─ rules/          # Violation detection logic
│  ├─ storage/        # Event logging
│  ├─ reporting/      # Report generation
│  └─ delivery/       # WhatsApp integration
├─ scripts/           # Automation scripts
├─ tests/             # Unit and integration tests
└─ reports/           # Generated daily reports
```

## Dataset

This project uses the [Safety Helmet and Reflective Jacket dataset](https://datasetninja.com/safety-helmet-and-reflective-jacket).

Classes:
- `safety_helmet`: Safety helmet detection
- `reflective_jacket`: Reflective jacket detection

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_rules.py -v

# Run with coverage
pytest --cov=src tests/
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guide and architecture.

## License

[Your License Here]
