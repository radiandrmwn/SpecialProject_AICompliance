# PPE-Watch: AI-Powered Safety Compliance System

An intelligent computer vision system for real-time Personal Protective Equipment (PPE) compliance monitoring in construction and industrial environments. The system detects missing safety helmets and reflective vests, tracks violations, and delivers automated daily reports via Telegram.

![System Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-detection-orange)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Methodology & Approach](#methodology--approach)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Workflow](#workflow)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

PPE-Watch is a special project developed to enhance workplace safety through automated PPE compliance monitoring. Traditional manual supervision is time-consuming and prone to human error. This system leverages state-of-the-art computer vision and object detection to:

1. **Detect** workers and their PPE (helmets and reflective vests) in real-time
2. **Track** individuals across video frames to prevent double counting
3. **Identify** violations when workers are missing BOTH helmet AND vest
4. **Log** all detection events with timestamps and unique identifiers
5. **Generate** comprehensive daily reports with statistics and visualizations
6. **Deliver** automated reports to supervisors via Telegram bot

**Use Cases:**
- Construction site safety monitoring
- Industrial facility compliance tracking
- Warehouse safety audits
- Mining operation supervision
- Educational safety demonstrations

---

## Key Features

### 1. Multi-Attribute PPE Detection
- **YOLOv8-based** object detection for high accuracy
- Simultaneous detection of **safety helmets** and **reflective vests**
- Confidence filtering (threshold: 0.25) to reduce false positives
- Multi-class labeling showing all missing PPE items

### 2. Intelligent Violation Logic
- **Violation triggered only when BOTH helmet AND vest are missing**
- Individual missing items labeled but not counted as violations
- Examples:
  - Missing helmet only → "NO HELMET" (informational)
  - Missing vest only → "NO VEST" (informational)
  - Missing both → "NO HELMET & NO VEST" (VIOLATION)

### 3. Person Tracking & Identity Management
- **ByteTrack** integration for multi-object tracking
- Unique track IDs prevent double counting
- Track state management across video frames
- Violation counted once per person per zone per day

### 4. Video Processing Pipeline
- Upload videos directly via Telegram bot
- Real-time frame-by-frame detection and tracking
- Annotated video output with bounding boxes and labels
- Video codec: XVID with AVI container (universal compatibility)
- Processing statistics displayed on each frame

### 5. Automated Reporting System
- **Daily aggregation** of violation events
- CSV reports with detailed event logs
- PNG charts visualizing violations by zone
- PDF summary reports with KPIs and statistics
- Automatic report generation after video processing

### 6. Telegram Bot Integration
- **Interactive bot** for on-demand video processing
- Commands: `/start`, `/help`, `/latest`
- Video upload support (up to 20MB)
- Automatic delivery of annotated videos and reports
- Plain text messaging for reliable delivery

### 7. Zone-Based Monitoring
- Configurable polygon zones per camera
- Point-in-polygon detection for zone filtering
- Zone-specific violation statistics
- Support for multiple zones per video

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│  • Video Upload (Telegram)  • Live Camera Feed  • Video Files   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DETECTION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Person     │  │   Helmet     │  │     Vest     │          │
│  │  Detection   │  │  Detection   │  │  Detection   │          │
│  │  (YOLOv8)    │  │  (YOLOv8)    │  │  (YOLOv8)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRACKING LAYER                               │
│  • ByteTrack Multi-Object Tracking                              │
│  • Unique Track ID Assignment                                   │
│  • Track State Management                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Head       │  │   Zone       │  │  Violation   │          │
│  │   Region     │  │   Filtering  │  │   Logic      │          │
│  │   Detection  │  │   (Polygon)  │  │   (Rules)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
│  • CSV Event Logging (events_YYYY-MM-DD.csv)                    │
│  • Daily Aggregation & Statistics                               │
│  • Annotated Video Output                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REPORTING LAYER                              │
│  • Aggregate Statistics Calculation                             │
│  • Chart Generation (Matplotlib)                                │
│  • PDF Report Creation (ReportLab)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DELIVERY LAYER                               │
│  • Telegram Bot API Integration                                 │
│  • Automated Report Delivery                                    │
│  • Interactive Commands & Responses                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Methodology & Approach

### 1. Object Detection Approach

**Model Selection: YOLOv8**
- **Why YOLOv8?** State-of-the-art real-time object detection with excellent balance between speed and accuracy
- **Architecture:** Single-stage detector with anchor-free design
- **Input Size:** 640x640 (configurable)
- **Classes:** 2 classes (safety_helmet, reflective_jacket)

**Detection Pipeline:**
```
Frame Input → Preprocessing → YOLOv8 Inference → NMS → Bounding Boxes
```

**Dual Detection Strategy:**
1. **Person Detection:** Pre-trained YOLOv8 on COCO dataset (person class)
2. **PPE Detection:** Custom-trained YOLOv8 on Safety Helmet & Reflective Jacket dataset

### 2. PPE Verification Methodology

**Head Region Detection:**
```python
# Extract top 35% of person bounding box as head region
head_region = (x1, y1, x2, y1 + 0.35 * height)
```

**Helmet Verification:**
- Calculate **IoU (Intersection over Union)** between detected helmet and head region
- Threshold: IoU > 0.10 (10% overlap)
- Lower threshold ensures sensitivity to partially visible helmets

**Vest Verification:**
- Calculate IoU between detected vest and full person bounding box
- Threshold: IoU > 0.15 (15% overlap)
- Accounts for vest covering torso area

**Confidence Filtering:**
- Only accept detections with confidence > 0.25 (25%)
- Balances between false positives and false negatives

### 3. Violation Detection Logic

**Rule-Based System:**
```python
has_helmet = any(IoU(helmet, head_region) > 0.10 for helmet in helmet_boxes)
has_vest = any(IoU(vest, person_box) > 0.15 for vest in vest_boxes)

# Violation only if BOTH are missing
is_violation = not has_helmet and not has_vest

# But label shows all missing items
if not has_helmet:
    label += "NO HELMET"
if not has_vest:
    label += "NO VEST"
```

**Why BOTH must be missing?**
- Reduces false alarms
- Focuses on critical safety violations
- Prevents over-reporting during transition periods (e.g., putting on vest)

### 4. Multi-Object Tracking Approach

**ByteTrack Algorithm:**
- **Track Association:** Kalman filter for motion prediction
- **Data Association:** Hungarian algorithm for matching
- **Track Management:** Birth, update, deletion of tracks
- **ID Consistency:** Maintains unique IDs across frames

**Track State Management:**
```python
class TrackState:
    - track_id → set of zones where violation occurred
    - Prevents counting same person multiple times
    - Resets daily for fresh statistics
```

### 5. Zone-Based Filtering

**Point-in-Polygon Algorithm:**
```python
# Use person's centroid for zone checking
centroid = ((x1+x2)/2, (y1+y2)/2)

# Shapely library for polygon operations
polygon = Polygon(zone_coordinates)
is_inside = polygon.contains(Point(centroid))
```

**Why centroid?**
- More stable than using full bounding box
- Less affected by person's pose or partial occlusion
- Accurate representation of person's location

### 6. Event Logging Strategy

**CSV-Based Storage:**
```csv
timestamp,camera_id,track_id,zone,has_helmet,has_vest,frame_idx
1731398400.123,cam_1,42,main_zone,false,false,671
```

**Why CSV?**
- Simple, human-readable format
- Easy to import into Excel/Pandas for analysis
- No database setup required
- Lightweight for edge devices

**Daily Partitioning:**
- One CSV file per day (`events_YYYY-MM-DD.csv`)
- Automatic date-based partitioning
- Efficient for daily reporting
- Easy archival and cleanup

### 7. Report Generation Pipeline

**Aggregation Stage:**
```python
1. Read events CSV for target date
2. Group by track_id to get unique violators
3. Group by zone for zone-specific statistics
4. Calculate metrics: total events, unique violators, violation rate
5. Identify top violators (track IDs with most violations)
```

**Visualization Stage:**
```python
1. Bar chart: Violations per zone (Matplotlib)
2. Pie chart: Compliant vs Violators (optional)
3. Timeline chart: Violations over time (optional)
```

**PDF Generation:**
```python
1. Use ReportLab for professional PDF layout
2. Include: Date, summary statistics, zone breakdown, top violators
3. Embed charts as images
4. Add footer with generation timestamp
```

### 8. Telegram Bot Architecture

**Long Polling Approach:**
```python
while running:
    updates = get_updates(offset=last_update_id + 1)
    for update in updates:
        handle_message(update)
        last_update_id = update.update_id
    time.sleep(1)
```

**Command Handler Pattern:**
```python
if message.startswith('/start'):
    handle_start()
elif message.startswith('/help'):
    handle_help()
elif message.startswith('/latest'):
    handle_latest_report()
elif message.has_video():
    handle_video_upload()
```

**Video Processing Workflow:**
```
1. Receive video from Telegram
2. Download to temporary directory
3. Process with video_processor.py
4. Generate annotated video
5. Save events to CSV
6. Regenerate daily report
7. Send annotated video back
8. Send updated report (CSV, PNG, PDF)
9. Cleanup temporary files
```

---

## Installation

### Prerequisites

- **Python 3.10+**
- **NVIDIA GPU** (recommended) with CUDA 11.8+ or CPU fallback
- **Windows/Linux/MacOS**
- **Git**
- **Telegram Bot Token** (get from [@BotFather](https://t.me/botfather))

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/ppe-watch.git
cd ppe-watch
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -U pip
pip install -r requirements.txt
```

**Key Dependencies:**
- `ultralytics>=8.3.0` - YOLOv8 framework
- `opencv-python` - Video processing
- `numpy`, `pandas` - Data manipulation
- `shapely` - Polygon operations
- `matplotlib` - Chart generation
- `reportlab` - PDF creation
- `requests` - Telegram API calls

### Step 4: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Required Environment Variables:**
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE

# Reporting
DAILY_REPORT_HOUR=18
TIMEZONE=Asia/Taipei

# Paths (defaults are fine)
DATA_DIR=./data
EVENTS_DIR=./events
REPORTS_DIR=./reports
```

### Step 5: Download/Train Model

**Option A: Use Pre-trained Model**
```bash
# Download trained model (if available)
# Place best.pt in runs/helmet/train/weights/
```

**Option B: Train Your Own**
```bash
# Prepare dataset in data/ directory
# See "Dataset Preparation" section below
bash scripts/train_yolo.sh
```

---

## Usage

### 1. Run Telegram Bot (Recommended)

**Interactive bot for on-demand video processing:**

```bash
python -m src.delivery.telegram_bot_interactive
```

**Available Commands:**
- `/start` - Initialize bot and see welcome message
- `/help` - Show available commands
- `/latest` - Get today's report (CSV, charts, PDF)
- **Send video** - Upload video for violation detection

**Video Upload Workflow:**
1. Send video to bot (max 20MB)
2. Bot processes video for violations
3. Bot sends back annotated video
4. Bot sends updated daily report

### 2. Test with Webcam

**Live testing with your webcam:**

```bash
python scripts/demo_webcam.py
```

- Press `q` to quit
- Shows real-time detections with bounding boxes
- Displays statistics (violators, compliant)

### 3. Process Video File Directly

**CLI inference on video file:**

```bash
python -m src.inference.video_processor \
    --source samples/construction.mp4 \
    --output output/ \
    --model runs/helmet/train/weights/best.pt
```

### 4. Generate Daily Report Manually

**For a specific date:**

```bash
python -m src.reporting.aggregate_day --date 2025-11-12
```

**Output:**
- `reports/report_2025-11-12.csv`
- `reports/report_2025-11-12.png`
- `reports/report_2025-11-12.pdf`

### 5. Automated Daily Reporting

**Setup Windows Task Scheduler:**

```bash
# Run daily automation script
python scripts/daily_report_automation.py
```

**Schedule in Task Scheduler:**
- Trigger: Daily at 18:00
- Action: Run `scripts/run_daily_automation.bat`
- See `SCHEDULER_SETUP.md` for detailed instructions

---

## Project Structure

```
ppe-watch/
├── README.md                          # This file
├── CLAUDE.md                          # Development guide
├── COMPLETE_WORKFLOW.md               # End-to-end workflow
├── TELEGRAM_BOT_VIDEO_GUIDE.md        # Bot usage guide
├── SCHEDULER_SETUP.md                 # Scheduling guide
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── .env                              # Your credentials (gitignored)
│
├── data/                             # Dataset
│   ├── images/                       # Training images
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── labels/                       # YOLO annotations
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── helmet.yaml                   # Dataset config
│
├── configs/                          # Configuration files
│   ├── zones.json                    # Zone polygons
│   └── reporter.yaml                 # Report settings
│
├── src/                              # Source code
│   ├── models/                       # Training & validation
│   │   ├── train.py
│   │   ├── val.py
│   │   └── export.py
│   │
│   ├── inference/                    # Detection & tracking
│   │   ├── service.py               # CLI inference
│   │   ├── video_processor.py       # Video processing pipeline
│   │   └── zoning.py                # Zone utilities
│   │
│   ├── rules/                        # Business logic
│   │   └── violations.py            # Violation detection
│   │
│   ├── storage/                      # Data persistence
│   │   ├── events_writer.py         # CSV event logging
│   │   └── schema.py                # Data schemas
│   │
│   ├── reporting/                    # Report generation
│   │   ├── aggregate_day.py         # Daily aggregation
│   │   ├── charts.py                # Chart generation
│   │   └── make_pdf.py              # PDF creation
│   │
│   ├── delivery/                     # Communication
│   │   ├── telegram_bot.py          # Daily report bot
│   │   └── telegram_bot_interactive.py  # Interactive bot
│   │
│   └── utils/                        # Utilities
│       ├── viz.py                   # Visualization helpers
│       └── timers.py                # Performance timing
│
├── scripts/                          # Automation & tools
│   ├── demo_webcam.py               # Webcam testing
│   ├── setup_telegram.py            # Bot setup wizard
│   ├── configure_zones.py           # Zone configuration tool
│   ├── daily_report_automation.py   # Scheduled reporting
│   └── run_daily_automation.bat     # Windows batch file
│
├── tests/                            # Unit tests
│   ├── test_rules.py
│   ├── test_zoning.py
│   └── test_reporting.py
│
├── events/                           # Event logs (gitignored)
│   └── events_YYYY-MM-DD.csv
│
├── reports/                          # Generated reports (gitignored)
│   ├── report_YYYY-MM-DD.csv
│   ├── report_YYYY-MM-DD.png
│   └── report_YYYY-MM-DD.pdf
│
├── runs/                             # Training runs (gitignored)
│   └── helmet/
│       └── train/
│           └── weights/
│               └── best.pt          # Trained model
│
└── temp/                             # Temporary files (gitignored)
    └── video_*/                      # Video processing temp
```

---

## Workflow

### Complete End-to-End Workflow

```
┌─────────────────┐
│  Supervisor     │
│  uploads video  │
│  to Telegram    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Telegram Bot receives video            │
│  Downloads to temp/ directory           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Video Processor Pipeline               │
│  ├─ Load YOLOv8 models (person + PPE)   │
│  ├─ Process frame by frame              │
│  │  ├─ Detect persons                   │
│  │  ├─ Detect helmets & vests           │
│  │  ├─ Track persons (ByteTrack)        │
│  │  ├─ Check head region for helmet     │
│  │  ├─ Check body for vest              │
│  │  ├─ Determine violation status       │
│  │  └─ Draw annotations on frame        │
│  ├─ Save annotated video (AVI)          │
│  └─ Log events to CSV                   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Report Generation Triggered            │
│  ├─ Aggregate events from today's CSV   │
│  ├─ Calculate statistics                │
│  │  ├─ Total events                     │
│  │  ├─ Unique violators (by track ID)   │
│  │  ├─ Violations per zone              │
│  │  └─ Top violators                    │
│  ├─ Generate bar chart (violations)     │
│  └─ Create PDF report with summary      │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Telegram Bot sends results             │
│  ├─ Annotated video with detections     │
│  ├─ CSV report (events_YYYY-MM-DD.csv)  │
│  ├─ PNG chart (report_YYYY-MM-DD.png)   │
│  └─ PDF summary (report_YYYY-MM-DD.pdf) │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Supervisor     │
│  reviews report │
│  and video      │
└─────────────────┘
```

**Key Workflow Features:**
1. **Asynchronous Processing:** Bot responds immediately while processing in background
2. **Event Persistence:** All detections saved to CSV for historical analysis
3. **Automatic Aggregation:** Reports regenerated automatically after each video
4. **Multi-Format Output:** CSV (raw data), PNG (visualization), PDF (summary)
5. **Cleanup:** Temporary files deleted after processing

---

## Configuration

### Zone Configuration

**File:** `configs/zones.json`

```json
{
  "cam_1": {
    "polygons": [
      {
        "name": "main_zone",
        "points": [[0, 0], [1920, 0], [1920, 1080], [0, 1080]]
      },
      {
        "name": "restricted_area",
        "points": [[500, 300], [1400, 300], [1400, 800], [500, 800]]
      }
    ]
  }
}
```

**Interactive Zone Setup:**
```bash
python scripts/configure_zones.py --video samples/construction.mp4
```

- Click on video to draw polygon
- Press `s` to save zone
- Press `r` to reset
- Press `q` to quit

### Reporter Configuration

**File:** `configs/reporter.yaml`

```yaml
report:
  title: "Daily PPE Compliance Report"
  timezone: "Asia/Taipei"
  delivery_time: "18:00"

thresholds:
  violation_rate_warning: 0.20  # 20% violation rate triggers warning

charts:
  dpi: 300
  figsize: [12, 6]
  colors:
    violation: "#FF4444"
    compliant: "#44FF44"
```

### Detection Thresholds

**File:** `src/inference/video_processor.py`

```python
# Confidence threshold for PPE detection
CONFIDENCE_THRESHOLD = 0.25

# IoU thresholds for PPE verification
HELMET_IOU_THRESHOLD = 0.10
VEST_IOU_THRESHOLD = 0.15

# Head region ratio (top % of person bbox)
HEAD_REGION_RATIO = 0.35
```

**Tuning Guide:**
- **Decrease confidence threshold** → More detections, more false positives
- **Increase confidence threshold** → Fewer detections, more false negatives
- **Decrease IoU threshold** → More lenient, detects partial overlap
- **Increase IoU threshold** → More strict, requires better overlap

---

## Development

### Dataset Preparation

**1. Download Dataset:**
- [Safety Helmet and Reflective Jacket Dataset](https://datasetninja.com/safety-helmet-and-reflective-jacket)
- Extract to `data/` directory

**2. Verify Dataset:**
```bash
python scripts/verify_dataset.py
```

**3. Dataset Format (YOLO):**
```
data/
├── images/
│   ├── train/
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    │   ├── img001.txt
    │   ├── img002.txt
    │   └── ...
    ├── val/
    └── test/
```

**Label Format (YOLO):**
```
# class x_center y_center width height (normalized 0-1)
0 0.5 0.3 0.1 0.15    # Helmet
1 0.5 0.6 0.2 0.3     # Vest
```

### Training

**Train YOLOv8 Model:**
```bash
bash scripts/train_yolo.sh
```

**Custom Training:**
```bash
yolo detect train \
    data=data/helmet.yaml \
    model=yolov8s.pt \
    imgsz=640 \
    epochs=50 \
    batch=16 \
    patience=10 \
    project=runs/helmet
```

**Training Parameters:**
- `imgsz`: Input image size (640, 960, 1280)
- `epochs`: Training epochs (50-100)
- `batch`: Batch size (adjust based on GPU memory)
- `patience`: Early stopping patience

**Validation:**
```bash
yolo detect val \
    data=data/helmet.yaml \
    model=runs/helmet/train/weights/best.pt \
    imgsz=640
```

### Code Style

**Follow PEP 8:**
```bash
# Install linter
pip install flake8 black

# Check code
flake8 src/

# Auto-format
black src/
```

### Adding New Features

**Example: Add new violation rule**

1. **Update violation logic** (`src/rules/violations.py`):
```python
def is_violation(person_box, helmet_boxes, vest_boxes, **kwargs):
    # Your custom logic here
    pass
```

2. **Update event schema** (`src/storage/schema.py`):
```python
EVENT_COLUMNS = [
    "timestamp", "camera_id", "track_id",
    "zone", "has_helmet", "has_vest",
    "new_attribute",  # Add your new field
    "frame_idx"
]
```

3. **Update report aggregation** (`src/reporting/aggregate_day.py`)

4. **Write tests** (`tests/test_rules.py`)

---

## Testing

### Unit Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rules.py -v

# Run with coverage
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/
```

### Test Structure

```python
# tests/test_rules.py
import pytest
from src.rules.violations import head_region, bbox_iou, is_violation

def test_head_region_extraction():
    person_box = (0, 0, 100, 100)
    head = head_region(person_box, top_ratio=0.35)
    assert head == (0, 0, 100, 35)

def test_iou_calculation():
    box1 = (0, 0, 10, 10)
    box2 = (5, 5, 15, 15)
    iou = bbox_iou(box1, box2)
    assert 0.1 < iou < 0.2

def test_violation_detection():
    person_box = (0, 0, 100, 200)
    helmet_boxes = []  # No helmet
    vest_boxes = []    # No vest

    is_viol, label = is_violation(person_box, helmet_boxes, vest_boxes)
    assert is_viol == True
    assert "NO HELMET" in label
    assert "NO VEST" in label
```

### Integration Testing

**Test video processing pipeline:**
```bash
# Process sample video
python -m src.inference.video_processor \
    --source tests/fixtures/sample_10s.mp4 \
    --output tests/output/ \
    --model runs/helmet/train/weights/best.pt

# Verify outputs
ls tests/output/
# Should contain: output_annotated.avi, events_*.csv
```

### Manual Testing Checklist

- [ ] Bot starts without errors
- [ ] `/start` command shows welcome message
- [ ] `/help` command shows all commands
- [ ] `/latest` command sends today's report
- [ ] Video upload triggers processing
- [ ] Annotated video is playable
- [ ] Events are logged to CSV
- [ ] Reports are generated correctly
- [ ] Charts display violations accurately
- [ ] PDF report is well-formatted

---

## Troubleshooting

### Common Issues

#### 1. Bot not responding

**Symptoms:** Bot doesn't reply to commands

**Solutions:**
```bash
# Check if bot token is correct
cat .env | grep TELEGRAM_BOT_TOKEN

# Verify bot is running
ps aux | grep telegram_bot

# Check for error messages in terminal
python -m src.delivery.telegram_bot_interactive
```

#### 2. Video processing fails

**Symptoms:** Error during video processing, no annotated video

**Solutions:**
```bash
# Check model file exists
ls runs/helmet/train/weights/best.pt

# Verify video format
ffmpeg -i your_video.mp4

# Check available disk space
df -h

# Try with smaller video
# Video size limit: 20MB for Telegram
```

#### 3. Detection accuracy issues

**Symptoms:** Too many false positives/negatives

**Solutions:**
```python
# Adjust thresholds in video_processor.py

# For more false positives (too strict):
CONFIDENCE_THRESHOLD = 0.20  # Lower
HELMET_IOU_THRESHOLD = 0.08  # Lower
VEST_IOU_THRESHOLD = 0.12    # Lower

# For more false negatives (too lenient):
CONFIDENCE_THRESHOLD = 0.35  # Higher
HELMET_IOU_THRESHOLD = 0.15  # Higher
VEST_IOU_THRESHOLD = 0.20    # Higher
```

#### 4. Report not generating

**Symptoms:** `/latest` returns "No report for today"

**Solutions:**
```bash
# Check if events CSV exists
ls events/events_$(date +%Y-%m-%d).csv

# Manually generate report
python -m src.reporting.aggregate_day --date $(date +%Y-%m-%d)

# Check reports directory
ls reports/
```

#### 5. Memory issues

**Symptoms:** Out of memory errors during processing

**Solutions:**
```python
# Reduce batch size in inference
# Process fewer frames per second

# In video_processor.py:
fps = cap.get(cv2.CAP_PROP_FPS)
process_every_n = 2  # Process every 2nd frame
```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `409 Conflict` | Multiple bot instances | Kill all instances, run one |
| `400 Bad Request` | Invalid message format | Use plain text, no special chars |
| `FileNotFoundError: best.pt` | Model not found | Train model or download weights |
| `cv2.error: VideoWriter` | Codec not available | Use XVID codec with AVI |
| `ImportError: ultralytics` | Package not installed | `pip install ultralytics` |

### Getting Help

1. **Check documentation:** Read `CLAUDE.md` for detailed guide
2. **Check logs:** Review terminal output for error messages
3. **Check issues:** Search GitHub issues for similar problems
4. **Open issue:** Create new issue with error details and logs

---

## Contributing

Contributions are welcome! Please follow these guidelines:

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Contribution Guidelines

- **Code Style:** Follow PEP 8
- **Documentation:** Update README if adding features
- **Tests:** Add tests for new functionality
- **Commits:** Use clear, descriptive commit messages
- **Issues:** Link PR to related issue

### Areas for Contribution

- Improve detection accuracy
- Add new violation rules
- Enhance report visualizations
- Optimize performance
- Add more tests
- Improve documentation
- Add new features (e.g., email notifications)

---

## License

This project is developed as a special project for educational purposes at Asia University, Taiwan.

**Author:** Radian Try Darmawan
**Institution:** Asia University (Taiwan)
**Semester:** 2nd Semester, 2024-2025
**Course:** Special Project

---

## Acknowledgments

- **Dataset:** [Safety Helmet and Reflective Jacket Dataset](https://datasetninja.com/safety-helmet-and-reflective-jacket)
- **YOLO:** [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- **Tracking:** [ByteTrack](https://github.com/ifzhang/ByteTrack)
- **Telegram:** [Telegram Bot API](https://core.telegram.org/bots/api)

---

## Contact

For questions or support:
- **GitHub Issues:** [Open an issue](https://github.com/your-username/ppe-watch/issues)
- **Email:** your.email@example.com

---

## Changelog

### v1.0.0 (2025-11-12)
- Initial release
- YOLOv8 detection for helmet and vest
- ByteTrack multi-object tracking
- Multi-attribute violation labeling
- Telegram bot integration
- Automated daily reporting
- CSV/PNG/PDF report generation
- Interactive video upload feature
- Webcam testing support

---

**Built with ❤️ for workplace safety**
