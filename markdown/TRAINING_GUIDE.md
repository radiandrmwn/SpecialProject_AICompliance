# YOLOv8 Training Guide for PPE-Watch

## Quick Answer: Where Should I Train?

### Check Your GPU First

Run this command after installing requirements:

```bash
python scripts/check_gpu.py
```

This will tell you if you have a compatible GPU and what settings to use.

---

## Option Comparison

| Feature | Local (VS Code) | Google Colab | Kaggle | Cloud (AWS/Azure) |
|---------|----------------|--------------|---------|-------------------|
| **Cost** | Free (electricity) | Free | Free | Paid ($$$) |
| **GPU** | Your GPU | Tesla T4 (15GB) | P100 (16GB) | Custom |
| **Session Limit** | Unlimited | 12 hours | 9-12 hours | Unlimited |
| **Setup Difficulty** | Medium | Easy | Easy | Hard |
| **Data Privacy** | ✅ Private | ⚠️ Google's servers | ⚠️ Kaggle's servers | ✅ Private |
| **Internet Required** | No | Yes | Yes | Yes |
| **Best For** | You have GPU | No GPU / Learning | Longer training | Production |

---

## Option 1: Train Locally in VS Code ⭐ (Recommended if you have GPU)

### Requirements

**Minimum:**
- NVIDIA GPU with 4GB+ VRAM (GTX 1050 Ti or better)
- CUDA 11.8 or 12.1 installed
- 8GB+ system RAM
- 10GB+ free disk space

**Recommended:**
- NVIDIA GPU with 8GB+ VRAM (RTX 3060, RTX 2060 Super, or better)
- 16GB+ system RAM

### Setup Steps

1. **Check if you have compatible GPU:**
   ```bash
   python scripts/check_gpu.py
   ```

2. **Prepare dataset:**
   - Download from [Safety Helmet Dataset](https://datasetninja.com/safety-helmet-and-reflective-jacket)
   - Extract to `data/` folder
   - Verify: `python scripts/verify_dataset.py`

3. **Train in VS Code:**

   **Method A: Using VS Code Task (Easy)**
   - Press `Ctrl+Shift+B`
   - Select "train:helmet"
   - Monitor progress in terminal

   **Method B: Using Terminal**
   ```bash
   bash scripts/train_yolo.sh
   ```

   **Method C: Python Script**
   ```bash
   yolo detect train data=data/helmet.yaml model=yolov8s.pt epochs=50 batch=16
   ```

4. **Monitor Training:**
   - Terminal shows live progress
   - Results saved to `runs/helmet/train/`
   - Charts: `runs/helmet/train/results.png`

### Training Time Estimates (with GPU)

- **Small dataset** (1000 images, 50 epochs): 20-40 minutes
- **Medium dataset** (5000 images, 50 epochs): 1-3 hours
- **Large dataset** (10000 images, 50 epochs): 3-6 hours

### Pros ✅
- No session limits - train for days if needed
- Full control over process
- Can pause/resume anytime
- Private data stays on your machine
- Easy debugging in VS Code
- No upload/download delays
- Can use while offline

### Cons ❌
- Requires GPU (or very slow on CPU)
- Uses your electricity
- Ties up your computer

---

## Option 2: Google Colab 🌐 (Recommended for beginners / no GPU)

### What is Google Colab?

Free Jupyter notebook environment with **FREE GPU access** (Tesla T4 with ~15GB VRAM).

### Setup Steps

1. **Upload the Colab Notebook:**
   - Go to [colab.research.google.com](https://colab.research.google.com)
   - Upload `scripts/train_colab.ipynb` from this project
   - Or create new notebook and copy cells

2. **Enable GPU:**
   - Runtime → Change runtime type → GPU (T4)
   - Verify: Run `!nvidia-smi`

3. **Upload Dataset:**

   **Option A: From Google Drive**
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```

   **Option B: Direct Upload**
   - Use Colab's file browser to upload
   - Or zip dataset and upload: `!unzip dataset.zip`

4. **Run Training:**
   - Execute cells in order
   - Monitor progress in notebook output

5. **Download Results:**
   ```python
   from google.colab import files
   files.download('runs/helmet/train/weights/best.pt')
   ```

### Training Time Estimates (Colab GPU)

- **Small dataset**: 15-30 minutes
- **Medium dataset**: 1-2 hours
- **Large dataset**: 3-5 hours

### Pros ✅
- **FREE GPU** - No hardware needed
- Pre-installed libraries
- Good for learning/experimenting
- Can train from any computer
- Share notebooks easily

### Cons ❌
- 12-hour session limit (disconnects)
- Need to upload dataset (~slow)
- Need to download model after
- Sessions can disconnect randomly
- Not suitable for very long training
- Internet required

### Tips for Colab Success

1. **Prevent Disconnection:**
   ```javascript
   // Run in browser console (F12)
   function ClickConnect(){
     console.log("Working");
     document.querySelector("colab-toolbar-button#connect").click()
   }
   setInterval(ClickConnect, 60000)
   ```

2. **Save Checkpoints:**
   - Save to Google Drive periodically
   - Model auto-saves every epoch to `last.pt`

3. **Resume Training:**
   ```python
   model.train(resume='runs/helmet/train/weights/last.pt')
   ```

---

## Option 3: Kaggle Notebooks (Alternative to Colab)

Similar to Colab but with:
- Slightly longer sessions (9-12 hours)
- P100 GPU (16GB) - slightly faster
- 30 hours/week GPU quota

**When to use:** If Colab is slow or unavailable.

---

## Option 4: Local CPU Training (Last Resort)

If you have **NO GPU** and don't want to use Colab:

### Setup

```bash
# In scripts/train_yolo.sh, change:
DEVICE="cpu"

# Or directly:
yolo detect train data=data/helmet.yaml model=yolov8s.pt device=cpu epochs=50 batch=4
```

### Training Time Estimates (CPU)

- **Small dataset**: 4-8 hours
- **Medium dataset**: 10-20 hours
- **Large dataset**: 24+ hours

### Tips

1. Use smaller model: `yolov8n.pt` instead of `yolov8s.pt`
2. Reduce image size: `imgsz=416` instead of `640`
3. Smaller batch: `batch=4` or `batch=2`
4. Train overnight
5. Use fewer epochs initially (20-30) to test

---

## Which Option Should YOU Choose?

### ✅ Use Local Training (VS Code) if:
- You have NVIDIA GPU with 4GB+ VRAM
- You value privacy
- You want full control
- You have reliable power
- You don't mind using your computer

### ✅ Use Google Colab if:
- You don't have a GPU
- You're a beginner
- You want to try quickly
- Your dataset is small-medium
- Training takes < 10 hours

### ✅ Use CPU Training if:
- You absolutely can't use cloud
- Dataset is very small
- You can wait overnight
- Privacy is critical

---

## Recommended Workflow (Best of Both Worlds)

1. **Experiment on Colab First** (Free GPU)
   - Test with small subset of data
   - Find good hyperparameters
   - Validate your approach
   - Takes 30 minutes

2. **Final Training Locally** (If you have GPU)
   - Use full dataset
   - Train for more epochs
   - Better privacy
   - Takes 2-4 hours

3. **Or stick with Colab for everything** (No GPU)
   - Train in multiple sessions if needed
   - Save checkpoints to Drive
   - Resume if disconnected

---

## Training Checklist

Before training, ensure:

- [ ] Dataset verified: `python scripts/verify_dataset.py`
- [ ] At least 500+ images per class
- [ ] Train/val/test split (~70/20/10)
- [ ] GPU available OR using Colab
- [ ] Enough disk space (10GB+)
- [ ] Config file ready: `data/helmet.yaml`

---

## After Training

1. **Evaluate Results:**
   - Check mAP50 score (target: ≥0.85)
   - Review confusion matrix
   - Test on sample images

2. **Move Model to Project:**
   ```bash
   # If trained on Colab, download and place:
   # best.pt → runs/helmet/train/weights/best.pt
   ```

3. **Test Inference:**
   ```bash
   yolo predict model=runs/helmet/train/weights/best.pt source=test_image.jpg
   ```

4. **Integrate with PPE-Watch:**
   - Model will be auto-loaded by inference service
   - Update `.env` if needed: `HELMET_MODEL_PATH=runs/helmet/train/weights/best.pt`

---

## Troubleshooting

### "CUDA out of memory"
- Reduce batch size: `batch=8` or `batch=4`
- Reduce image size: `imgsz=416`
- Close other programs
- Use smaller model: `yolov8n.pt`

### "RuntimeError: CUDA not available"
```bash
# Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with CUDA
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Colab Disconnects
- Use the console trick above
- Save to Google Drive regularly
- Use `patience=10` for early stopping
- Split training into multiple sessions

### Training is Slow
- Check GPU usage: `nvidia-smi` (should be 90-100%)
- Increase batch size if possible
- Use larger model if you decreased it
- Check CPU bottleneck (data loading)

---

## Need More Help?

- **YOLOv8 Docs**: https://docs.ultralytics.com/modes/train/
- **Colab Tutorial**: Open `scripts/train_colab.ipynb`
- **Check GPU**: `python scripts/check_gpu.py`
- **Verify Dataset**: `python scripts/verify_dataset.py`

Good luck with training! 🚀
