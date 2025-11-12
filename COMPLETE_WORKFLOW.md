# PPE-Watch Complete Workflow Guide

## Complete User Journey: Video Upload → Events Logged → Daily Report

This guide explains the complete workflow from sending a video to the Telegram bot, through processing and logging, to viewing the final daily report.

---

## Overview of the System

```
User sends video → Bot downloads → Video processed → Events logged → Report generated → User gets /latest
      ↓                ↓               ↓                 ↓                ↓                    ↓
   Telegram       temp/ folder    Detection runs    events_YYYY-MM-DD   reports/report_    Shows today's
      ↓                ↓           helmet + person      .csv            YYYY-MM-DD.pdf      violations
   Upload          MP4 file        tracking          (daily log)       (aggregated)
```

---

## Step-by-Step Workflow

### Step 1: User Sends Video to Bot

**What user does:**
1. Opens Telegram chat with PPE-Watch bot
2. Sends a video file (recorded on phone, GoPro, etc.)
3. File size must be ≤ 20MB
4. Formats: MP4, AVI, MOV

**What bot does:**
```
🎥 Video Received
Size: 8.5MB
Processing for violations...
⏳ This may take a few moments
```

---

### Step 2: Video Processing

**Technical flow:**

1. **Download** - Bot downloads video from Telegram to `temp/video_{chat_id}_{timestamp}/input_video.mp4`

2. **Detection** - [video_processor.py](src/inference/video_processor.py) runs:
   - Opens video with OpenCV
   - For each frame (sampling every 2nd frame):
     - Detect persons (YOLOv8)
     - Detect helmets (trained model)
     - Track persons across frames (ByteTrack)
     - Check if helmet covers head region
     - Determine violation (no helmet = violation)

3. **Event Logging** - For each unique person detected:
   ```python
   {
       'timestamp': 1730448000.123,
       'camera_id': 'telegram_upload',
       'track_id': 42,
       'zone': 'main_zone',
       'has_helmet': False,  # True = compliant, False = violation
       'frame_idx': 671
   }
   ```

   Events are written to: `events/events_2025-11-11.csv`

4. **Annotation** - Creates annotated video:
   - Green boxes: Persons with helmets
   - Red boxes: Persons without helmets
   - Labels: Track IDs and status
   - Saved as: `temp/.../output_annotated.mp4`

**Processing time:** ~30s for 10-second video, ~2min for 30-second video

---

### Step 3: Results Sent to User

Bot sends **two things**:

**1. Statistics Message:**
```
✅ Processing Complete

Video Statistics:
• Duration: 12.5 seconds
• Frames processed: 312

Violation Results:
• Unique violators (no helmet): 2
• Compliant persons (with helmet): 1
• Total detections: 45

⚠️ 2 person(s) detected without helmet

💡 Tip: Send another video anytime to check compliance
```

**2. Annotated Video:**
- Video with detection boxes overlaid
- Visual confirmation of who was detected
- Shows track IDs for reference

---

### Step 4: Events Logged to Daily CSV

**File created/updated:** `events/events_2025-11-11.csv`

**Content example:**
```csv
timestamp,camera_id,track_id,zone,has_helmet,frame_idx
1731294000.123,telegram_upload,1,main_zone,False,45
1731294001.456,telegram_upload,2,main_zone,False,78
1731294002.789,telegram_upload,3,main_zone,True,112
```

**Key points:**
- Each row = one unique person detected
- `has_helmet=False` = violation
- `has_helmet=True` = compliant
- Multiple videos on same day → appended to same file
- Timestamp uses video processing time (current time)

---

### Step 5: Daily Report Auto-Generated

**Immediately after video processing:**

Bot automatically runs:

```python
# 1. Aggregate events
DailyAggregator.generate_report('2025-11-11')
# Creates: reports/report_2025-11-11.csv

# 2. Generate charts
ChartGenerator.generate_charts('2025-11-11')
# Creates: reports/report_2025-11-11.png

# 3. Generate PDF
PDFReportGenerator.generate_report('2025-11-11', stats, charts_path)
# Creates: reports/report_2025-11-11.pdf
```

**Bot notifies user:**
```
📊 Daily Report Updated

Your video has been added to today's report.
Use `/report 2025-11-11` or `/latest` to view the updated report.
```

---

### Step 6: User Views Daily Report

**Command:** `/latest` or `/report 2025-11-11`

**Bot sends:**
1. **Text summary:**
   ```
   📊 Daily Report - 2025-11-11

   Total Events: 12
   With Helmet: 5
   Without Helmet: 7
   Violation Rate: 58.3%

   Worst Zone: main_zone (7 violations)
   ```

2. **Chart PNG** - Bar charts and pie charts

3. **PDF Report** - Professional 2-page report with:
   - Executive summary
   - Zone breakdown
   - Top violators by track ID
   - Charts embedded

---

## File Structure

After a video is processed:

```
SpecialProject/
├── events/
│   └── events_2025-11-11.csv          # ✅ Your video's violations logged here
│
├── reports/
│   ├── report_2025-11-11.csv          # ✅ Aggregated daily stats
│   ├── report_2025-11-11.png          # ✅ Charts
│   └── report_2025-11-11.pdf          # ✅ Full report
│
└── temp/
    └── video_123456789_1731294000/    # 🗑️ Auto-deleted after sending
        ├── input_video.mp4
        └── output_annotated.mp4
```

---

## Multi-Video Scenario

**If you send 3 videos today:**

1. **First video** (10:00 AM):
   - Detects 2 violators
   - Logs to `events_2025-11-11.csv` (2 rows)
   - Generates report with 2 violations

2. **Second video** (2:00 PM):
   - Detects 1 violator
   - **Appends** to `events_2025-11-11.csv` (now 3 rows)
   - **Regenerates** report with 3 violations total

3. **Third video** (5:00 PM):
   - Detects 3 violators
   - **Appends** to `events_2025-11-11.csv` (now 6 rows)
   - **Regenerates** report with 6 violations total

**Result:** `/latest` shows **combined report** of all 3 videos!

---

## Tomorrow's Workflow

**Next day (2025-11-12):**

1. You send a new video
2. Bot creates **new file**: `events_2025-11-12.csv`
3. Bot generates **new report**: `report_2025-11-12.pdf`
4. `/latest` shows **2025-11-12** report (most recent)

**Yesterday's report still accessible:**
- `/report 2025-11-11` - Shows previous day's report

---

## Sample Use Cases

### Use Case 1: Daily Site Inspection

**Scenario:** Supervisor walks construction site daily at 4 PM

**Workflow:**
1. 4:00 PM - Record 30-second video of work area
2. 4:01 PM - Send to bot via Telegram
3. 4:03 PM - Receive results (2 violations detected)
4. 4:05 PM - Show annotated video to workers
5. 5:00 PM - Check violations with `/latest`
6. Next day - Compare with `/report yesterday`

### Use Case 2: Multiple Area Checks

**Scenario:** Check 5 different zones throughout the day

**Workflow:**
1. 9:00 AM - Zone A video → Bot: "1 violation"
2. 11:00 AM - Zone B video → Bot: "0 violations"
3. 1:00 PM - Zone C video → Bot: "3 violations"
4. 3:00 PM - Zone D video → Bot: "1 violation"
5. 5:00 PM - Zone E video → Bot: "2 violations"
6. 6:00 PM - `/latest` → Report shows: "7 violations total"

### Use Case 3: Weekly Review

**Scenario:** Safety manager reviews weekly compliance

**Workflow:**
1. Monday - Send videos, accumulate events
2. Tuesday - Send videos, accumulate events
3. ...
4. Friday - Send videos, accumulate events
5. `/report 2025-11-11` - Monday's report
6. `/report 2025-11-12` - Tuesday's report
7. Compare violation trends across week

---

## Technical Details

### Event Logging Implementation

**File:** [video_processor.py](src/inference/video_processor.py) lines 208-219

```python
# When unique person detected
if events_writer:
    event_timestamp = process_start_time + (frame_idx / fps)
    event_row = {
        'timestamp': event_timestamp,
        'camera_id': 'telegram_upload',
        'track_id': track_id,
        'zone': 'main_zone',
        'has_helmet': not is_violator,
        'frame_idx': frame_idx
    }
    events_writer.append(event_row)
```

**Key features:**
- Uses `EventsWriter` class from [events_writer.py](src/storage/events_writer.py)
- Automatically creates daily CSV files
- Appends to existing file if already exists
- Thread-safe for concurrent writes

### Report Generation Implementation

**File:** [telegram_bot_interactive.py](src/delivery/telegram_bot_interactive.py) lines 466-507

```python
# After video processing
from src.reporting.aggregate_day import DailyAggregator
from src.reporting.charts import ChartGenerator
from src.reporting.make_pdf import PDFReportGenerator

# Step 1: Aggregate events
aggregator = DailyAggregator(events_dir="events", reports_dir="reports")
stats = aggregator.generate_report(today)

# Step 2: Generate charts
chart_gen = ChartGenerator()
charts_path = chart_gen.generate_charts(today)

# Step 3: Generate PDF
pdf_gen = PDFReportGenerator()
pdf_path = pdf_gen.generate_report(today, stats, charts_path)
```

---

## Differences from Sample Video Processing

### Old Way (Sample Videos):
```bash
# Manual process
python -m src.inference.service --source samples/cam1.mp4 --camera-id cam_1
# Events saved to events/ folder
# Run report generation manually
python -m src.reporting.aggregate_day --date 2025-11-11
python -m src.reporting.charts --date 2025-11-11
python -m src.reporting.make_pdf --date 2025-11-11
```

### New Way (Telegram Upload):
```
# Automated process
1. Send video to bot
2. Bot processes video
3. Bot logs events
4. Bot generates report
5. Bot notifies you
6. Done! Use /latest to view
```

**Key difference:** Everything is **automated** and **integrated**!

---

## Troubleshooting

### "No events found for date"

**Problem:** `/latest` says no reports available

**Check:**
```bash
# Check if events file exists
ls events/events_2025-11-11.csv

# Check if file has content
cat events/events_2025-11-11.csv
```

**Solution:** Send a video with people visible in frame

### "Report not updating"

**Problem:** Sent 2 videos but report still shows first video only

**Check console output:**
```
   📊 Regenerating daily report for 2025-11-11...
   ✅ Report updated: reports/report_2025-11-11.pdf
```

**Solution:** Check for errors in bot console, ensure aggregator ran

### "Track IDs resetting"

**Problem:** Same person gets different track IDs across videos

**Explanation:** This is **expected behavior**
- Each video processes independently
- Track IDs reset per video
- Daily report aggregates **all unique track IDs**
- Track ID 1 in video 1 ≠ Track ID 1 in video 2

**Not a problem:** Report still counts violations correctly

---

## Performance Optimization

### For Faster Processing:

1. **Trim videos** before sending:
   ```bash
   # Keep only 10 seconds
   ffmpeg -i long_video.mp4 -t 10 -c copy short_video.mp4
   ```

2. **Lower resolution:**
   ```bash
   # Scale to 720p
   ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4
   ```

3. **Adjust sample rate** in code:
   ```python
   # Process every 4th frame instead of every 2nd
   results = process_video_for_violations(
       video_path,
       temp_dir,
       sample_rate=4  # Default: 2
   )
   ```

---

## Summary

**Complete Workflow:**

1. ✅ Send video → Bot receives
2. ✅ Bot processes → Detections run
3. ✅ Events logged → `events_YYYY-MM-DD.csv` updated
4. ✅ Report generated → PDF + charts created
5. ✅ User notified → Can view with `/latest`

**Key Benefits:**

- **No CCTV needed** - Use phone/camera videos
- **Instant feedback** - Results in 30s-2min
- **Persistent logging** - All events saved
- **Automatic reporting** - No manual steps
- **Historical access** - View any day's report
- **Cumulative tracking** - Multiple videos per day combined

**Perfect for your situation:**
> "aku tidak punya cctv sendiri yang bisa dihubungkan"

You can now demonstrate a **complete PPE compliance system** using just:
- Your Telegram bot
- Videos recorded on your phone
- Automated violation detection
- Professional daily reports

All without needing a real CCTV installation! 🎉
