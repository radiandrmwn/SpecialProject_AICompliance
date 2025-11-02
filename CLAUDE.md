PPE-Watch: Helmet Compliance Detection & Daily WhatsApp Reports

Computer-vision pipeline to detect workers without safety helmets inside important zones, aggregate daily stats, and send a WhatsApp report to a supervisor.

Key outcomes

Robust helmet/no-helmet detection + zone rules

Identity-aware counting (tracking) to prevent double counts

Automated daily CSV/PNG/PDF summary

WhatsApp message + attachment at 18:00 every day

0) Repository Structure
ppe-watch/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ data/
│  ├─ images/ (train/val/test per data.yaml)
│  ├─ labels/ (YOLO format)
│  └─ helmet.yaml      # Ultralytics data spec (classes & paths)
├─ configs/
│  ├─ zones.json       # per-camera zone polygons
│  └─ reporter.yaml    # reporting thresholds & layout
├─ src/
│  ├─ models/
│  │  ├─ train.py
│  │  ├─ val.py
│  │  └─ export.py
│  ├─ inference/
│  │  ├─ service.py    # FastAPI or CLI inference
│  │  ├─ trackers.py   # ByteTrack/OC-SORT glue
│  │  └─ zoning.py     # point-in-polygon, head-region logic
│  ├─ rules/
│  │  └─ violations.py
│  ├─ storage/
│  │  ├─ events_writer.py
│  │  └─ schema.py
│  ├─ reporting/
│  │  ├─ aggregate_day.py
│  │  ├─ charts.py
│  │  └─ make_pdf.py
│  ├─ delivery/
│  │  └─ whatsapp.py
│  └─ utils/
│     ├─ viz.py
│     └─ timers.py
├─ scripts/
│  ├─ quick_eda.ipynb
│  ├─ train_yolo.sh
│  ├─ run_infer_cam.sh
│  └─ cron_daily.sh
├─ tests/
│  ├─ test_rules.py
│  ├─ test_zoning.py
│  └─ test_reporting.py
├─ .vscode/
│  ├─ settings.json
│  ├─ tasks.json
│  └─ launch.json
├─ Dockerfile
└─ Makefile

1) Prerequisites

Python 3.10+

NVIDIA GPU (recommended) with CUDA, or CPU fallback

Dataset (YOLO format) with classes: safety_helmet, reflective_jacket

WhatsApp Business Cloud API credentials (App ID, Phone Number ID, Access Token)

2) Install & Environment
# Create env (conda or venv)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install required libs
pip install -U pip
pip install -r requirements.txt

requirements.txt (starter)
ultralytics>=8.3.0
opencv-python
numpy
pandas
shapely
matplotlib
reportlab          # or weasyprint, choose one
fastapi uvicorn
python-dotenv
pydantic
requests
scikit-image

.env.example
# WhatsApp
WHATSAPP_TOKEN=REPLACE_ME
WHATSAPP_PHONE_NUMBER_ID=REPLACE_ME
WHATSAPP_TO=+62XXXXXXXXX
WHATSAPP_TEMPLATE_NAME=ppe_daily_report
WHATSAPP_TEMPLATE_LANG=en_US

# Reporting
DAILY_REPORT_HOUR=18
TIMEZONE=Asia/Taipei

# Paths
DATA_DIR=./data
EVENTS_DIR=./events
REPORTS_DIR=./reports

Copy to .env and fill in real values.

3) Dataset Setup

data/helmet.yaml
path: ./data
train: images/train
val: images/val
test: images/test
names:
  0: safety_helmet
  1: reflective_jacket

Assistant prompt:
“Create a Python script to verify YOLO label integrity under scripts/ that checks missing pairs (image without label, label without image), empty labels, and class id out of range for helmet.yaml.”

4) Training a Baseline (Ultralytics YOLO)

scripts/train_yolo.sh

#!/usr/bin/env bash
set -e
yolo detect train data=data/helmet.yaml model=yolov8s.pt imgsz=640 epochs=50 batch=16 project=runs/helmet
yolo detect val   data=data/helmet.yaml model=runs/helmet/train/weights/best.pt

Acceptance criteria

Save best.pt under runs/helmet/train/weights/

Print mAP50/mAP50-95; target mAP50 ≥ 0.85 (tune later)

VS Code task (.vscode/tasks.json)

{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "train:helmet",
      "type": "shell",
      "command": "bash scripts/train_yolo.sh",
      "problemMatcher": []
    }
  ]
}

5) Person + Helmet Fusion & Zone Rules

We run:

Detector A: helmet model (best.pt)

Detector B: COCO person model (yolov8s.pt pretrained)

Fuse detections → per person, check if helmet overlaps head region; if person is inside important zone polygon without helmet → violation event.

configs/zones.json (example)
{
  "cam_1": {
    "polygons": [
      {"name": "CraneBay", "points": [[120,80],[900,80],[900,600],[120,600]]}
    ]
  }
}

Head region heuristic: top 35% of person bbox.

src/rules/violations.py (stub)
from typing import List, Dict, Tuple
from shapely.geometry import Point, Polygon

def bbox_centroid(xyxy: Tuple[int,int,int,int]) -> Tuple[float,float]:
    x1,y1,x2,y2 = xyxy
    return ( (x1+x2)/2, (y1+y2)/2 )

def head_region(xyxy, top_ratio=0.35):
    x1,y1,x2,y2 = xyxy
    h = y2 - y1
    return (x1, y1, x2, y1 + int(h*top_ratio))

def iou(a, b):
    ax1,ay1,ax2,ay2 = a; bx1,by1,bx2,by2 = b
    inter_x1, inter_y1 = max(ax1,bx1), max(ay1,by1)
    inter_x2, inter_y2 = min(ax2,bx2), min(ay2,by2)
    inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = (ax2-ax1)*(ay2-ay1)
    area_b = (bx2-bx1)*(by2-by1)
    union = area_a + area_b - inter
    return inter/union if union > 0 else 0.0

def point_in_polygons(pt, polygons: List[List[Tuple[int,int]]]) -> Tuple[bool, str]:
    p = Point(*pt)
    for pol in polygons:
        if Polygon(pol).contains(p):
            # return name by index order if needed
            return True, ""
    return False, ""

def is_violation(person_xyxy, helmet_boxes, zone_polygons, head_iou_thresh=0.05):
    centroid = bbox_centroid(person_xyxy)
    inside, _ = point_in_polygons(centroid, zone_polygons)
    if not inside:
        return False
    head = head_region(person_xyxy)
    helmet_on = any(iou(h, head) > head_iou_thresh for h in helmet_boxes)
    return not helmet_on

Assistant prompt:
“Implement point_in_polygons to return the polygon name where the point lies. Update is_violation to return (is_violation: bool, zone_name: str) so we can log the zone.”

Tests tests/test_rules.py
def test_head_region_top35():
    assert head_region((0,0,100,100)) == (0,0,100,35)

def test_violation_when_inside_zone_and_no_helmet():
    # …
    assert is_violation(person, [], [poly])[0] is True

6) Tracking to Prevent Double Counting

Use Ultralytics tracking (ByteTrack/OC-SORT). We count per tracked ID per day per zone.

src/inference/trackers.py
class TrackState:
    # track_id -> last_seen_ts, last_zone
    pass

Assistant prompt:
“Write a TrackState class that remembers track_id → seen_zones set so we only count one violation per track per zone per day. Add method should_count(track_id, zone).”

Acceptance criteria

When a person lingers, we log one violation for that zone.

7) Event Logging & Schema

src/storage/schema.py
EVENT_COLUMNS = [
  "timestamp", "camera_id", "track_id",
  "zone", "has_helmet", "frame_idx"
]

src/storage/events_writer.py
import csv, os, datetime as dt

class EventsWriter:
    def __init__(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir

    def _path_for_day(self, day: str):
        return os.path.join(self.out_dir, f"events_{day}.csv")

    def append(self, row: dict):
        day = dt.datetime.fromtimestamp(row["timestamp"]).strftime("%Y-%m-%d")
        path = self._path_for_day(day)
        write_header = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=row.keys())
            if write_header: w.writeheader()
            w.writerow(row)

Event row (example)
{
  "timestamp": 1730448000.123,  // epoch seconds
  "camera_id": "cam_1",
  "track_id": 42,
  "zone": "CraneBay",
  "has_helmet": false,
  "frame_idx": 671
}

8) Inference Service (CLI or API)

src/inference/service.py (CLI outline)

# CLI: python -m src.inference.service --source cam1.mp4 --camera-id cam_1 --model runs/helmet/train/weights/best.pt

# Steps:
# 1) Load helmet model + person model
# 2) Open video source
# 3) Run detection + tracking per frame
# 4) For each track, compute violation via rules
# 5) Append event rows
# 6) Optional live drawing & FPS print

Assistant prompt:
“Implement service.py with OpenCV capture loop, configurable --conf threshold, and graceful shutdown. Add a --dry-run flag that skips writing events.”

.vscode/launch.json (debug run)
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Inference (cam_1)",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/inference/service.py",
      "args": ["--source", "samples/cam1.mp4", "--camera-id", "cam_1",
               "--model", "runs/helmet/train/weights/best.pt",
               "--zones", "configs/zones.json"],
      "console": "integratedTerminal"
    }
  ]
}

9) Daily Aggregation & Report

src/reporting/aggregate_day.py
# Input: events_YYYY-MM-DD.csv
# Output: stats dict + CSV summary per zone + PNG chart + optional PDF
# Metrics:
#  - total_persons (unique track_id per zone)
#  - with_helmet, without_helmet
#  - violation_rate (%)
#  - top zones by violations

src/reporting/charts.py
# Produce a bar chart: violations per zone
# Produce a pie chart: with vs without helmet

src/reporting/make_pdf.py
# Assemble 1-page PDF with KPIs + charts + generated date/time

Assistant prompt:
“Write aggregate_day.py to read an events CSV, compute metrics per zone and totals, and save report_YYYY-MM-DD.csv + report_YYYY-MM-DD.png. Add unit tests using a tiny fixture CSV.”

Acceptance criteria

Running python -m src.reporting.aggregate_day --date 2025-11-01 yields:

reports/report_2025-11-01.csv

reports/report_2025-11-01.png

10) WhatsApp Delivery

src/delivery/whatsapp.py (outline)
import os, requests

def send_text_summary(token, phone_number_id, to, text):
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    return requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, json={
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }).json()

def send_document(token, phone_number_id, to, file_url, filename):
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    return requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, json={
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {"link": file_url, "filename": filename}
    }).json()

Daily message template (example)
*Daily PPE Summary ({{date}})*
Cameras: {{num_cameras}}
Total Persons: {{total}}
With Helmet: {{with_helmet}}
Without Helmet: {{without_helmet}} ({{rate}}%)
Worst Zone: {{worst_zone}} ({{worst_count}})

Assistant prompt:
“Implement a send_daily_report(date) function that loads .env, composes the message, uploads or links today’s CSV/PNG, and sends via WhatsApp. For dev, allow file:// local path links; in prod, support S3/Azure Blob public URL.”

11) Automation (Cron / GitHub Actions / Azure Logic Apps)

scripts/cron_daily.sh

#!/usr/bin/env bash
set -e
DATE=$(date +%F)
python -m src.reporting.aggregate_day --date "$DATE"
python -c "from src.delivery.whatsapp import send_daily_report; send_daily_report('$DATE')"

Crontab example

0 18 * * * /bin/bash -lc "cd /path/to/ppe-watch && source .venv/bin/activate && bash scripts/cron_daily.sh >> logs/cron.log 2>&1"

12) Testing Strategy

Unit tests (tests/):

test_zoning.py: point-in-polygon, centroid, head region

test_rules.py: violation logic (positive/negative cases)

test_reporting.py: aggregate_day metrics from fixture CSV

Integration tests:

Short 10-sec clip passes through inference → events CSV created

Acceptance tests:

End of day artifacts (CSV + PNG + WhatsApp message) exist & accurate

Assistant prompt:
“Generate pytest tests for edge cases: tiny helmets (small bbox), person near polygon edge, multiple helmets, overlapping persons.”

16) Performance Tuning

Increase imgsz (e.g., 960) for small helmets; trade-off speed

FP16 inference if GPU supported

Limit NMS classes when possible

Batch frames or sample 5–10 FPS for reporting use-case

Consider TensorRT export once baseline is stable

17) Security, Privacy & Compliance

Face blurring on saved frames (optional)

Retention policy for events (e.g., 90 days)

Role-based access to reports

Clear signage that monitoring is active; obtain necessary approvals

18) Developer Prompts (for Code Assistant)

Paste these in VS Code Chat/Cursor/Copilot to drive generation precisely.

Create zoning utilities

“Generate src/inference/zoning.py with functions: bbox_centroid, head_region, point_in_polygons (returns name), and robust unit tests under tests/test_zoning.py.”

Violation rule

“Write src/rules/violations.py exporting is_violation(person_xyxy, helmet_boxes, zone_polygons) -> (bool, zone_name). Include docstrings and edge-case handling for zero-area boxes.”

Tracking state

“Implement TrackState to ensure one violation per (track_id, zone, day). Provide tests mocking repeated frames.”

Inference loop

“Implement an OpenCV loop in src/inference/service.py: batched detection (helmet + person), fuse results, apply tracking, call violation rule, write events. Add --conf, --imgsz, --save-vis flags.”

Aggregation

“Create src/reporting/aggregate_day.py to read events CSV and output totals per zone and overall counts. Save a bar chart and pie chart in reports/.”

WhatsApp delivery

“Implement src/delivery/whatsapp.py with functions to send text and document messages using env vars. Add a send_daily_report(date) orchestrator.”

CI task

“Add a GitHub Action that runs unit tests on PR and (optionally) invokes aggregate_day.py for a sample fixture date.”

20) Troubleshooting

No events created: Check --zones path and polygon coordinates; ensure centroids actually fall inside polygons.

Too many violations: Lower head_iou_thresh? (No—raise it.) Also verify the head region fraction and NMS thresholds.

WhatsApp error 400: Token or phone number ID missing; ensure the recipient is a valid WhatsApp number and you’ve approved the message template or use plain text.

