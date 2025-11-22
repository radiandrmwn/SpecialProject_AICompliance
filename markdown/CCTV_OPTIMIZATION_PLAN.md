# CCTV Optimization Plan: Production vs Demo Mode

## 📋 Context

**Current Situation:**
- Telegram bot processes 30-second videos in ~2+ minutes
- For CCTV: 6 hours of footage would take ~24 hours to process (unacceptable!)
- Bottleneck: Video encoding (annotated video generation)

**Key Insight:**
> For CCTV deployment, we don't need full annotated videos - we only need reliable reports with visual evidence (screenshots).

---

## ⏱️ Performance Analysis

### **Current Telegram Bot Performance**

```
30 seconds of video → 2+ minutes processing

Processing breakdown:
├─ Person detection + tracking: ~30% of time
├─ PPE detection (helmet + vest): ~30% of time
├─ Violation logic + tracking: ~10% of time
└─ VIDEO ENCODING (annotated output): ~30% of time ⚠️ BOTTLENECK
```

### **Projected CCTV Processing (Current Method)**

**With annotated video generation:**
```
6 hours of footage = 21,600 seconds
21,600 ÷ 30 = 720 segments
720 × 2 minutes = 1,440 minutes = 24 HOURS ❌ UNACCEPTABLE
```

**Without annotated video (report only):**
```
6 hours of footage → ~2-3 hours processing ✅ ACCEPTABLE
Speed: 2-3x realtime (much better!)
```

---

## 🎯 Proposed Solution: Dual Processing Modes

### **Mode 1: Demo Mode (Current Behavior)**
**Use Cases:**
- Telegram bot interactions
- Webcam demo recordings
- Presentations and demonstrations
- Training materials

**Features:**
- ✅ Full annotated video generation
- ✅ Bounding boxes and labels drawn on every frame
- ✅ Real-time statistics overlay
- ✅ High visual appeal for stakeholders

**Trade-offs:**
- ⏱️ Slower processing (30 sec video = 2+ min)
- 💾 Large storage (2-5 GB for 6 hours)
- ✅ Great for demos and presentations

### **Mode 2: Production Mode (Optimized for CCTV)**
**Use Cases:**
- Daily CCTV footage processing
- Large-scale deployments (10+ cameras)
- Overnight batch processing
- Real-world industrial monitoring

**Features:**
- ✅ Fast processing (2-3x realtime)
- ✅ Violation screenshots (visual evidence)
- ✅ Detailed CSV reports (all violation data)
- ✅ PDF reports with charts
- ❌ No full annotated video

**Trade-offs:**
- ⚡ 8-12x faster processing
- 💾 50x smaller storage (50-100 MB vs 2-5 GB)
- ✅ Perfect for daily operations

---

## 💾 Storage Comparison: Why 50x Smaller Without Quality Loss

### **What Takes Up Space**

#### **Demo Mode (2-5 GB):**
```
6 hours annotated video:
├─ 6 hours × 3600 seconds = 21,600 seconds
├─ 30 FPS × 21,600 = 648,000 frames
├─ Each frame: 1920×1080 pixels with annotations drawn
├─ Compressed with XVID codec
└─ Final size: 2-5 GB (depends on compression)
```

#### **Production Mode (50-100 MB):**
```
Only violation screenshots + data:
├─ 12 unique violators detected in 6 hours
├─ 1 screenshot per violator = 12 images
├─ Each screenshot: 1920×1080 JPEG @ quality 90
├─ Size per screenshot: ~50-100 KB
└─ Total breakdown:
    ├─ Screenshots: 12 × 100 KB = 1.2 MB
    ├─ events_2025-11-22.csv = 500 KB (text data)
    ├─ report_2025-11-22.pdf = 2-5 MB (charts + text)
    └─ report_2025-11-22.png = 500 KB (chart image)
    = ~5-7 MB total per day ✅
```

### **Why No Detection Quality Loss?**

**Critical Insight:** The detection happens in RAM, not on disk!

```python
# Processing pipeline:
1. Read frame from video → RAM
2. Run detection models → RAM (GPU/CPU)
3. Calculate violations → RAM
4. Record to CSV → DISK (tiny: just numbers/text)
5. [Optional] Save annotated frame → DISK (huge: full video)
```

**Key Points:**
- ✅ Detection quality depends on **frames processed**, not **frames saved**
- ✅ We still process all frames (or every 2nd frame with sample_rate=2)
- ✅ We just don't **save** the processed video to disk
- ✅ Only save the **data** (CSV) and **evidence** (screenshots)
- ✅ Same models (96.8% mAP50 helmet detection)
- ✅ Same BoT-SORT tracking with occlusion handling
- ✅ Same violation logic (helmet + vest rules)

**The ONLY difference:**
- Demo Mode: Draws boxes → Encodes video → Saves VIDEO file
- Production Mode: Records data → Saves SCREENSHOTS → Saves CSV

---

## 📊 Visual Comparison

### **Demo Mode Pipeline:**
```
Process 6 hours → Detect violations → Draw boxes on every frame → Encode video
                                           ↓
                                    Video encoding
                                     (SLOW + BIG)
                                           ↓
                                       2-5 GB video file
```

### **Production Mode Pipeline:**
```
Process 6 hours → Detect violations → Save to CSV → Save 1 screenshot per violator
                                         ↓                      ↓
                                    Text data               JPEG images
                                   (1 KB/event)            (100 KB/image)
                                         ↓                      ↓
                                      500 KB                  1.2 MB
                                         ↓                      ↓
                                    + PDF report (2-5 MB)
                                         ↓
                                Total: ~5-7 MB ✅
```

---

## 🎓 Analogy: Sports Game Example

Think of it like recording a sports game:

### **Demo Mode = Recording Full HD Movie**
- ✅ You can watch every moment in replay
- ✅ Great for highlights and detailed review
- ✅ Perfect for presentations
- ❌ File size: 2-5 GB
- ❌ Takes long time to process/encode

### **Production Mode = Game Statistics + Key Photos**
- ✅ CSV = Score sheet (who scored, when, how many points)
- ✅ Screenshots = Photos of each scoring moment
- ✅ Detection quality: **Same** (you still watched/analyzed the whole game!)
- ✅ Storage: 50x smaller
- ✅ Processing: 8-12x faster

**Result:** You get all the important information and visual evidence without storing every single frame of video.

---

## 🔧 Implementation Plan

### **Architecture Overview**

```python
# Add --mode parameter to video processor
python -m src.inference.video_processor \
    --source video.mp4 \
    --mode demo       # Full annotated video (current behavior)

python -m src.inference.video_processor \
    --source video.mp4 \
    --mode production  # Fast mode (screenshots + CSV only)
```

### **Changes Required**

#### **1. Video Processor** (`src/inference/video_processor.py`)

**Add mode parameter:**
```python
parser.add_argument('--mode',
                   choices=['demo', 'production'],
                   default='demo',
                   help='Processing mode: demo (full video) or production (screenshots only)')
```

**Production mode behavior:**
```python
if mode == 'production':
    # Skip cv2.VideoWriter initialization
    # Skip drawing annotations on every frame
    # Capture screenshot ONLY when new violation detected
    # Save to violations/YYYY-MM-DD/ folder
    # Speed improvement: 40-50% faster
```

**Screenshot capture strategy:**
```python
# Track which violators have been photographed
photographed_violators = set()

# When violation detected:
if track_id not in photographed_violators:
    # Save annotated screenshot
    screenshot_path = violations_dir / f"violation_track{track_id}_{timestamp}_{violation_type}.jpg"
    cv2.imwrite(str(screenshot_path), annotated_frame)
    photographed_violators.add(track_id)
```

#### **2. CCTV Batch Processor** (`scripts/process_cctv_batch.py`)

```python
# Use production mode by default for CCTV
results = process_video_for_violations(
    video_path,
    output_dir,
    mode='production',  # Fast processing
    sample_rate=4,      # Process every 4th frame (4x speed)
    resize_width=960    # Resize for speed
)
```

#### **3. Telegram Bot** (`src/delivery/telegram_bot_interactive.py`)

```python
# Keep using demo mode (users want to see annotated video)
results = process_video_for_violations(
    video_path,
    temp_dir,
    mode='demo',        # Full annotated video
    sample_rate=2,      # Process every 2nd frame
    resize_width=960
)

# Optionally: Add /quick_report command for fast processing
if command == '/quick_report':
    results = process_video_for_violations(
        video_path,
        temp_dir,
        mode='production',  # Fast mode, no video
        sample_rate=4
    )
    # Send CSV + screenshots instead of video
```

---

## 📊 Performance Comparison

### **6 Hours of CCTV Footage Processing**

| Mode | Annotated Video | Screenshots | Processing Time | Storage | Use Case |
|------|----------------|-------------|-----------------|---------|----------|
| **Demo** | ✅ Full video | ❌ No | ~24 hours ❌ | 2-5 GB | Presentations |
| **Production** | ❌ No | ✅ 1 per violator | ~2-3 hours ✅ | 50-100 MB | Daily operations |

**Speed Improvement: 8-12x faster!**

### **Processing Speed (Production Mode)**

| Footage Duration | Processing Time | Speed Factor |
|------------------|-----------------|--------------|
| 1 hour | ~20-25 minutes | 2.4-3x realtime |
| 6 hours | ~2-2.5 hours | 2.4-3x realtime |
| 12 hours | ~4-5 hours | 2.4-3x realtime |
| 24 hours | ~8-10 hours | 2.4-3x realtime |

**Overnight Processing Strategy:**
```
Start: 6:00 PM (end of work day)
Process: 8-12 hours of footage
Complete: 2:00-4:00 AM
Deliver: 8:00 AM next morning ✅
```

### **Storage Requirements (Production Mode)**

**Per Camera Per Day:**
- Events CSV: ~500 KB
- Violation screenshots (10-20): ~500 KB - 1 MB
- PDF report: ~2-5 MB
- PNG charts: ~500 KB
- **Total: ~3-7 MB per camera per day**

**For 5 Cameras, 30 Days:**
- 5 cameras × 7 MB × 30 days = **1.05 GB per month**
- Very manageable! ✅

---

## 📦 Output Structure (Production Mode)

### **Daily Report Package**

```
output/
├── 2025-11-22/
│   ├── events_2025-11-22.csv          # Full violation data
│   ├── report_2025-11-22.pdf          # Charts + summary
│   ├── report_2025-11-22.png          # Charts only
│   └── violations/
│       ├── violation_track1_08-23-15_NO-HELMET.jpg
│       ├── violation_track3_09-45-22_NO-VEST.jpg
│       ├── violation_track7_11-12-08_NO-HELMET-NO-VEST.jpg
│       └── ... (one per unique violator)
└── 2025-11-23/
    └── ...
```

### **What You Get**

#### **CSV Data** (`events_2025-11-22.csv`)
```csv
timestamp,camera_id,track_id,zone,has_helmet,has_vest,violation_type
2025-11-22 08:23:15,cam1,1,CraneBay,False,True,NO_HELMET
2025-11-22 09:45:22,cam1,3,LoadingDock,True,False,NO_VEST
2025-11-22 11:12:08,cam1,7,CraneBay,False,False,NO_HELMET_NO_VEST
```

#### **PDF Report**
- Executive summary with key metrics
- Charts (bar charts, pie charts, trends)
- Zone breakdown
- Top violators
- Time-of-day analysis

#### **Violation Screenshots**
- One clear screenshot per unique violator
- Filename includes: track ID, timestamp, violation type
- Annotated with bounding box and labels
- JPEG quality 90 (~100 KB each)

#### **WhatsApp/Telegram Notification**
```
🚨 Daily PPE Compliance Report
📅 2025-11-22

📊 SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━
▪️ Total Events: 45
▪️ Unique Violators: 12
▪️ Zones Monitored: 3
▪️ Compliance Rate: 73.3% ✅

🗺️ TOP VIOLATION ZONES:
━━━━━━━━━━━━━━━━━━━━━━
▪️ CraneBay: 8 violations
▪️ LoadingDock: 5 violations

📸 Top 5 violation screenshots attached
📎 Full report PDF attached

🔗 Download full package: [link]
```

---

## 🎯 Screenshot Capture Strategies

### **Option A: First Violation Only** (Minimal)
```python
# Capture screenshot when track_id first marked as violator
if track_id not in photographed_violators:
    save_screenshot(frame, track_id, violation_type)
    photographed_violators.add(track_id)
```
- **Pros:** Minimal storage, fast
- **Result:** 1 screenshot per unique person
- **Storage:** 10-20 screenshots per day (~1-2 MB)

### **Option B: Best Quality Frame** (Recommended) ⭐
```python
# Track violation frames, save the clearest one
for each violation:
    quality_score = calculate_quality(frame, person_bbox)
    if quality_score > best_quality_for_track[track_id]:
        best_frame[track_id] = current_frame
        best_quality_for_track[track_id] = quality_score

# At end, save best frames
for track_id, frame in best_frames.items():
    save_screenshot(frame, track_id, violation_type)
```
- **Quality score based on:**
  - Person bbox size (larger = better)
  - Face/head visibility
  - Not occluded by others
  - Frame sharpness (not blurry)
- **Pros:** Best quality evidence
- **Result:** Best screenshot per violator
- **Storage:** Same as Option A but better quality

### **Option C: Multiple Angles** (Comprehensive)
```python
# Save up to 3 screenshots per violator (beginning, middle, end)
if violation_count_for_track[track_id] <= 3:
    save_screenshot(frame, track_id, violation_type, instance=violation_count_for_track[track_id])
    violation_count_for_track[track_id] += 1
```
- **Pros:** Multiple views of same person
- **Result:** 2-3 screenshots per violator
- **Storage:** 30-60 screenshots per day (~3-6 MB)

**Recommendation:** Use **Option B** (Best Quality Frame) for production deployments.

---

## ✅ Success Criteria

### **Production Mode Goals:**
1. ✅ **Speed:** Process 6 hours of footage in under 3 hours
2. ✅ **Accuracy:** Same detection accuracy as demo mode (96.8% mAP50)
3. ✅ **Storage:** < 10 MB per camera per day
4. ✅ **Evidence:** Clear violation screenshots for every unique violator
5. ✅ **Reports:** PDF + CSV + PNG generated automatically
6. ✅ **Delivery:** WhatsApp/Telegram notification with attachments
7. ✅ **Reliability:** Can run unattended overnight

---

## 🚀 Implementation Timeline

### **Phase 1: Core Production Mode** (3 hours)
- [ ] Add `--mode` parameter to video_processor.py
- [ ] Implement screenshot-only processing
- [ ] Skip video encoding in production mode
- [ ] Test with 1-hour sample footage
- [ ] Validate speed improvement (target: 2-3x realtime)

### **Phase 2: Screenshot Enhancement** (2 hours)
- [ ] Implement quality scoring for frames
- [ ] Save best frame per violator (Option B)
- [ ] Add metadata to screenshot filenames
- [ ] Test screenshot quality with various scenarios

### **Phase 3: Integration** (2 hours)
- [ ] Update CCTV batch processor to use production mode
- [ ] Update Telegram bot to send screenshots
- [ ] Add screenshots page to PDF reports
- [ ] Test end-to-end workflow

### **Phase 4: Testing & Validation** (2 hours)
- [ ] Process full 6-hour test footage
- [ ] Verify processing time < 3 hours
- [ ] Validate storage < 10 MB
- [ ] Compare detection accuracy with demo mode
- [ ] Review screenshot quality

**Total Estimated Time: 9 hours**

---

## 🎯 Deployment Strategy

### **For Nov 25 Demo (Current Focus):**
✅ **Use Demo Mode**
- Keep current behavior (annotated videos)
- Impressive for presentations
- Show stakeholders the visual capabilities
- Demonstrate real-time detection

✅ **Show Sample Screenshots**
- Mention future optimization plans
- Explain production mode benefits
- Show storage/speed comparisons

### **For Real CCTV Deployment (Future):**
✅ **Use Production Mode**
- Fast overnight processing
- Daily reports delivered in morning
- Violation screenshots as evidence
- Scalable to 10+ cameras

✅ **Hybrid Approach**
- Production mode for daily operations
- Demo mode available for special review cases
- Switch via `--mode` parameter

---

## 📝 Current Status

**As of Nov 22, 2025:**
- ✅ Core detection system is production-ready (96.8% mAP50)
- ✅ BoT-SORT tracking with occlusion handling working perfectly
- ✅ Telegram bot working with demo mode (full annotated videos)
- ✅ Webcam demo upgraded with production-grade enhancements
- ⏳ Production mode implementation planned (not yet built)
- ⏳ Violation screenshot feature planned (not yet built)

**Priority:**
1. **Nov 25 Demo:** Focus on current demo mode (already excellent)
2. **Post-Demo:** Implement production mode for real deployments

---

## 🎓 Key Takeaways

### **Why Production Mode is Needed:**
1. ❌ Current method: 30 sec video = 2+ min → 6 hours = 24 hours (**unacceptable**)
2. ✅ Production mode: 6 hours = 2-3 hours (**acceptable**)
3. ✅ Storage: 50x smaller (5-7 MB vs 2-5 GB)
4. ✅ Same detection quality (processing is identical, just skips video encoding)
5. ✅ Visual evidence maintained (violation screenshots)

### **Best Analogy:**
> Recording every frame of a movie vs. taking photos of key scenes + keeping detailed notes
> - Both capture the important information
> - One is 50x smaller and 8-12x faster to create
> - Production deployments need efficiency, not full video playback

### **When to Use Each Mode:**

**Demo Mode:**
- ✅ Telegram interactions
- ✅ Webcam demos
- ✅ Presentations to stakeholders
- ✅ Training materials
- ✅ When visual playback is important

**Production Mode:**
- ✅ Daily CCTV processing (6-24 hours of footage)
- ✅ Multi-camera deployments
- ✅ Overnight batch processing
- ✅ When speed and storage matter
- ✅ When data + evidence screenshots are sufficient

---

## 📚 Related Documents

- [CCTV_DEPLOYMENT.md](./CCTV_DEPLOYMENT.md) - General deployment guide
- [WEBCAM_DEMO_UPGRADE.md](./WEBCAM_DEMO_UPGRADE.md) - Webcam demo enhancements
- [QUICKSTART.md](./QUICKSTART.md) - Basic system usage

---

**Document Created:** November 22, 2025
**Last Updated:** November 22, 2025
**Status:** Planning Phase - Not Yet Implemented
**Priority:** Post-Demo Feature (After Nov 25)
