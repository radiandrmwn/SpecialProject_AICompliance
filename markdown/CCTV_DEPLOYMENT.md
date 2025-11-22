# CCTV Deployment Guide

## Overview

This guide explains how to deploy PPE-Watch for production CCTV systems with hours of footage.

---

## Deployment Options

### Option 1: Scheduled Batch Processing ⭐ **RECOMMENDED FOR START**

**Best for:**
- 1-4 cameras
- Daily compliance reports
- Standard CCTV systems that record to files

**Setup Time:** 1-2 hours

**Requirements:**
- CCTV system that saves recordings as video files (MP4, AVI, etc.)
- Computer with GPU (can be same as CCTV server)
- 100-200 GB storage for 7 days of recordings

---

## Step-by-Step Setup

### Step 1: Configure CCTV Recording

**Option A: Network Video Recorder (NVR)**

Most CCTV systems have NVR that saves recordings. Configure it to:
- Save recordings as MP4 or AVI files
- Split recordings into 1-hour segments
- Use clear naming: `cam1_2025-11-20_14-00.mp4`
- Save to a network share accessible by processing computer

**Folder structure:**
```
\\NVR-SERVER\recordings\
├── 2025-11-20\
│   ├── cam1_00-01.mp4
│   ├── cam1_01-02.mp4
│   ├── cam1_02-03.mp4
│   ...
│   └── cam1_23-00.mp4
├── 2025-11-21\
└── ...
```

**Option B: USB Cameras / IP Cameras**

Use OBS Studio or FFmpeg to record:
```bash
# Record in 1-hour segments
ffmpeg -i rtsp://camera-ip:554/stream \
    -c copy \
    -f segment -segment_time 3600 \
    -strftime 1 \
    "cctv_recordings/%Y-%m-%d/cam1_%H-%M.mp4"
```

### Step 2: Install PPE-Watch on Processing Computer

```bash
# Clone and setup
git clone <your-repo-url>
cd SpecialProject
pip install -r requirements.txt

# Copy YOLO models
# Make sure you have:
# - runs/helmet/train4/weights/best.pt
# - yolov8s.pt
```

### Step 3: Configure Batch Processor

Edit `scripts/process_cctv_batch.py`:

```python
# Line 24: Update to your CCTV recordings folder
CCTV_RECORDINGS_PATH = Path("Z:/cctv_recordings")  # Network drive
# or
CCTV_RECORDINGS_PATH = Path("C:/CCTV/recordings")  # Local folder

# Line 26: Adjust sample rate based on your needs
SAMPLE_RATE = 4  # 4 = faster, 2 = more accurate

# Line 27: Adjust resize based on camera resolution
RESIZE_WIDTH = 960  # 960 for 1080p cameras, None for 720p
```

### Step 4: Test Manual Processing

Test with one day's recordings:

```bash
# Process today's recordings
python scripts/process_cctv_batch.py

# Process specific date
python scripts/process_cctv_batch.py --date 2025-11-20

# Process specific folder
python scripts/process_cctv_batch.py --input "C:/test_recordings"
```

**Expected output:**
```
===============================================================================
PPE-Watch CCTV Batch Processor
===============================================================================
Date: 2025-11-20
Input: cctv_recordings\2025-11-20
Sample Rate: 4 (every 4th frame)
Resize: 960px width
===============================================================================

📹 Found 8 video files

[1/8] Processing: cam1_08-09.mp4
   ✅ Violations: 2, Compliant: 5

[2/8] Processing: cam1_09-10.mp4
   ✅ Violations: 1, Compliant: 7

...

===============================================================================
📊 Batch Processing Complete
===============================================================================
Videos processed: 8/8
Total violations: 12
Total compliant: 45

📊 Generating daily report for 2025-11-20...
📱 Sending WhatsApp report...

✅ Daily report generated and sent!
```

### Step 5: Schedule Automatic Processing

**Windows Task Scheduler:**

1. Open Task Scheduler
2. Create Task → "PPE-Watch Daily Processing"
3. Trigger: Daily at 6:00 PM
4. Action: Start a program
   - Program: `python`
   - Arguments: `scripts/process_cctv_batch.py`
   - Start in: `C:\path\to\SpecialProject`

**Linux/Mac (cron):**

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 6 PM)
0 18 * * * cd /path/to/SpecialProject && python scripts/process_cctv_batch.py
```

---

## Performance Tuning

### Processing Speed

| Sample Rate | Speed | Accuracy | Use Case |
|-------------|-------|----------|----------|
| 1 | 1x | Best | High accuracy needed |
| 2 | 2x | Excellent | **Recommended** |
| 4 | 4x | Very Good | Fast processing, multiple cameras |
| 8 | 8x | Good | Quick overview only |

### Video Resolution

| Resolution | Resize | Speed | Accuracy |
|------------|--------|-------|----------|
| 4K (3840×2160) | 1280 | 3-4x faster | Excellent |
| 1080p (1920×1080) | 960 | 2-3x faster | Excellent |
| 720p (1280×720) | None | 1x | Best |

### Example Configurations

**High Accuracy (Court Evidence):**
```python
SAMPLE_RATE = 1
RESIZE_WIDTH = None
```

**Balanced (Recommended):**
```python
SAMPLE_RATE = 2
RESIZE_WIDTH = 960
```

**High Speed (4+ cameras):**
```python
SAMPLE_RATE = 4
RESIZE_WIDTH = 960
```

---

## Storage Management

### Automatic Cleanup

Create cleanup script to delete old recordings:

```python
# scripts/cleanup_old_recordings.py
import shutil
from datetime import datetime, timedelta
from pathlib import Path

RECORDINGS_PATH = Path("cctv_recordings")
KEEP_DAYS = 7  # Keep last 7 days

cutoff_date = datetime.now() - timedelta(days=KEEP_DAYS)

for folder in RECORDINGS_PATH.iterdir():
    if folder.is_dir():
        folder_date = datetime.strptime(folder.name, '%Y-%m-%d')
        if folder_date < cutoff_date:
            print(f"Deleting old recordings: {folder}")
            shutil.rmtree(folder)
```

Schedule to run weekly.

---

## Monitoring & Alerts

### Health Check Script

```python
# scripts/health_check.py
# Check if processing is running and up-to-date

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Check if today's report exists
today = datetime.now().strftime('%Y-%m-%d')
report_path = Path(f"reports/report_{today}.csv")

if not report_path.exists():
    print(f"⚠️ WARNING: No report generated for {today}")
    # Send alert email/WhatsApp
    sys.exit(1)

# Check if report is recent (within last 2 hours)
report_age = datetime.now() - datetime.fromtimestamp(report_path.stat().st_mtime)
if report_age > timedelta(hours=2):
    print(f"⚠️ WARNING: Report is {report_age.hours} hours old")
    sys.exit(1)

print("✅ System healthy")
```

---

## Troubleshooting

### Issue: "No video files found"

**Solution:** Check folder path and date structure
```bash
# Verify folder exists
dir "cctv_recordings\2025-11-20"

# Check video file extensions
# Update video_extensions in script if needed
```

### Issue: Processing too slow

**Solution:** Increase sample_rate or reduce resolution
```python
SAMPLE_RATE = 4  # Increase to 4 or 8
RESIZE_WIDTH = 640  # Reduce from 960
```

### Issue: Out of GPU memory

**Solution:** Process one video at a time (already default) or reduce resolution
```python
RESIZE_WIDTH = 640  # or 480
```

### Issue: Reports not sending

**Solution:** Check WhatsApp credentials in `.env`
```bash
# Test WhatsApp sending
python -c "from src.delivery.whatsapp import test_connection; test_connection()"
```

---

## Scaling to Multiple Cameras

### Parallel Processing

For 4+ cameras, process in parallel:

```python
# scripts/process_cctv_parallel.py
from multiprocessing import Pool

def process_camera(cam_id):
    videos = glob(f"cctv_recordings/*/cam{cam_id}_*.mp4")
    for video in videos:
        process_video_for_violations(video, ...)

# Process 4 cameras in parallel
with Pool(4) as p:
    p.map(process_camera, [1, 2, 3, 4])
```

**Requirements:**
- 1 GPU can handle 2-4 cameras in parallel
- 16+ GB RAM recommended
- SSD storage for faster I/O

---

## Cost Estimation

### Hardware Requirements

**For 1-2 Cameras:**
- GPU: NVIDIA GTX 1660 or better ($200-300)
- RAM: 8 GB
- Storage: 100 GB per camera per week

**For 4-8 Cameras:**
- GPU: NVIDIA RTX 3060 or better ($400-600)
- RAM: 16 GB
- Storage: SSD 1 TB

### Monthly Operating Cost

- Electricity: ~$10-20 (if running 24/7)
- WhatsApp Business API: Free for basic usage
- Cloud storage (optional): $5-10/month

**Total: ~$15-30/month**

---

## Next Steps

1. ✅ Test with sample CCTV footage
2. ✅ Configure scheduled processing
3. ✅ Set up monitoring and alerts
4. ✅ Train your team on reading reports
5. ✅ Deploy to production!

For questions or issues, refer to main README.md or GitHub issues.
