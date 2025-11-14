# Dataset Setup Guide

## Current Situation

You have: `data/safety-helmet-and-reflective-jacket-DatasetNinja.tar` (135MB)

**Problem**: The tar file appears to be corrupted or incomplete.

---

## Option 1: Re-download the Dataset (Recommended)

The tar file might have been interrupted during download. Try downloading again:

### Step 1: Download Dataset

Visit: https://datasetninja.com/safety-helmet-and-reflective-jacket

Click **Download** and select one of these formats:
- **Supervisely format** (recommended - easier to convert)
- **COCO format** (also good)
- Direct download link

### Step 2: Extract Using WinRAR/7-Zip

Since you're on Windows and the tar file is corrupted, **manually extract** using WinRAR:

1. Right-click `safety-helmet-and-reflective-jacket-DatasetNinja.tar`
2. Select "Extract to safety-helmet-and-reflective-jacket-DatasetNinja\"
3. Extract to: `data/extracted/`

### Step 3: Convert to YOLO Format

```bash
python scripts/prepare_dataset.py --skip-extract
```

This will:
- Read from `data/extracted/`
- Convert JSON annotations to YOLO format
- Organize into train/val/test splits
- Save to `data/images/` and `data/labels/`

---

## Option 2: Try Extracting Current File Manually

Even though the tar is corrupted, you might be able to extract partial data:

### Using WinRAR (Windows)

1. Open WinRAR
2. Navigate to your `data/` folder
3. Double-click `safety-helmet-and-reflective-jacket-DatasetNinja.tar`
4. Click "Extract To" → Choose `data/extracted/`
5. If it asks about errors, click "Keep" to keep extracted files
6. Run conversion script:
   ```bash
   python scripts/prepare_dataset.py --skip-extract
   ```

### Using 7-Zip (Windows)

1. Right-click the tar file
2. 7-Zip → Extract to "data\extracted\"
3. Ignore any error messages
4. Check if files were extracted
5. Run conversion:
   ```bash
   python scripts/prepare_dataset.py --skip-extract
   ```

---

## Option 3: Alternative Dataset Sources

If download keeps failing, try alternative sources:

### Roboflow Universe
https://universe.roboflow.com/

Search for "helmet detection" or "PPE detection" datasets

Many are already in YOLO format!

### Kaggle
https://www.kaggle.com/datasets

Search: "helmet detection dataset"

### Manual Collection
For a small project, you can:
1. Collect 200-500 images from Google Images
2. Annotate using [LabelImg](https://github.com/heartexlabs/labelImg) or [Roboflow](https://roboflow.com)
3. Export in YOLO format

---

## After Dataset is Ready

### Verify Dataset Structure

Your `data/` folder should look like this:

```
data/
├── helmet.yaml          ✅ (already exists)
├── images/
│   ├── train/          ← Should contain .jpg/.png files
│   ├── val/
│   └── test/
└── labels/
    ├── train/          ← Should contain .txt files (YOLO format)
    ├── val/
    └── test/
```

### Run Verification

```bash
python scripts/verify_dataset.py
```

Expected output:
```
✅ Dataset verification PASSED!
   Total images: XXXX
   Total labels: XXXX
   Missing labels: 0
   Missing images: 0
```

### Update helmet.yaml

Check that paths are correct in `data/helmet.yaml`:

```yaml
path: ./data
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: safety_helmet
  1: reflective_jacket
```

---

## Quick Troubleshooting

### "No such file or directory: data/extracted"

Extract the tar file first manually using WinRAR or 7-Zip.

### "No images found"

Check that extraction created these folders:
- `data/extracted/train/img/`
- `data/extracted/val/img/`
- `data/extracted/test/img/`

### "Conversion failed"

The dataset might be in a different format. Check the structure:

```bash
ls data/extracted/
```

If different structure, we'll need to adjust the conversion script.

### Still Having Issues?

Let me know the output of:

```bash
# Check what was extracted
ls -la data/extracted/

# Check structure
find data/extracted/ -type d | head -20
```

---

## Alternative: Use Sample Data for Testing

While waiting for the full dataset, create a tiny test dataset to verify your pipeline:

### Quick Test Dataset (5 images)

1. Download 5-10 construction worker images from Google Images
2. Save to `data/images/train/`
3. Create dummy labels in `data/labels/train/` (same filename, .txt extension)
4. Label format: `0 0.5 0.3 0.2 0.15` (class x y w h)
5. Test training:
   ```bash
   yolo detect train data=data/helmet.yaml epochs=5 batch=2
   ```

This lets you test the pipeline while you work on getting the full dataset.

---

## Next Steps After Dataset is Ready

1. ✅ Verify dataset: `python scripts/verify_dataset.py`
2. ✅ Check GPU: `python scripts/check_gpu.py`
3. ✅ Train model: `bash scripts/train_yolo.sh`
4. ✅ Test inference: `yolo predict model=runs/helmet/train/weights/best.pt source=test_image.jpg`

---

## Need Help?

Show me the output of:

```bash
# What's currently in data folder?
ls -la data/

# What's in the tar file?
tar -tf data/safety-helmet-and-reflective-jacket-DatasetNinja.tar | head -30

# Or if already extracted:
ls -la data/extracted/
```

I'll help you adapt the conversion script to match your dataset structure!
