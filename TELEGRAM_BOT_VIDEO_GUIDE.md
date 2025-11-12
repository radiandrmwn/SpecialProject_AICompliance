# Telegram Bot Video Upload Feature

## Overview

The PPE-Watch Telegram Bot can now process video uploads from users and detect PPE violations in real-time. This allows supervisors to check any video for helmet compliance without needing direct CCTV access.

---

## Features

- **Video Upload Processing**: Send any video file to the bot
- **Instant Analysis**: Get violation count and statistics
- **Annotated Video**: Receive video with detection boxes and labels
- **No CCTV Required**: Works with any video source (phone, GoPro, sample videos, etc.)
- **Track-based Counting**: Unique person tracking prevents double-counting

---

## How to Use

### 1. Start the Bot

Run the interactive bot:

```bash
python -m src.delivery.telegram_bot_interactive
```

You should see:
```
🤖 PPE-Watch Interactive Bot Started
💡 Bot is now listening for commands...
```

### 2. Send Video to Bot

From your Telegram app:

1. Open chat with your PPE-Watch bot
2. Click the attachment icon (📎)
3. Select "Video" or "File"
4. Choose your video file (MP4, AVI, or MOV)
5. Send the video

**Limitations:**
- Maximum file size: **20MB** (Telegram Bot API limit)
- Supported formats: MP4, AVI, MOV
- For larger files, compress or trim video first

### 3. Receive Results

The bot will:

1. Confirm receipt of video
   ```
   🎥 Video Received
   Size: 5.2MB
   Processing for violations...
   ⏳ This may take a few moments
   ```

2. Process the video (may take 30s - 2min depending on length)

3. Send detailed results:
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

4. Send annotated video with:
   - Green boxes: Persons with helmets
   - Red boxes: Persons without helmets
   - Track IDs and labels on each person
   - Frame statistics overlay

---

## Bot Commands

### Video Processing
- **Send video file** - Process video for violations

### Daily Reports
- `/report` - Get today's report
- `/report YYYY-MM-DD` - Get specific date report
- `/report yesterday` - Get yesterday's report
- `/latest` - Get most recent available report

### System
- `/start` - Show welcome message
- `/help` - Show all commands
- `/status` - Check system status

---

## Example Workflow

**Scenario:** Supervisor wants to check a video recorded on their phone

1. **Record video** of work area with phone
2. **Send video** to Telegram bot
3. **Wait** for processing (30s - 2min)
4. **Receive results:**
   - Summary statistics
   - Number of violations
   - Annotated video showing detections
5. **Review** annotated video to see exactly who was detected

---

## Technical Details

### Processing Pipeline

1. **Download**: Bot downloads video from Telegram servers
2. **Detection**:
   - Person detection (YOLOv8)
   - Helmet detection (Custom trained model)
   - Track persons across frames (ByteTrack)
3. **Analysis**:
   - Check head region for helmet overlap
   - Count unique violators (not per-frame)
   - Aggregate statistics
4. **Annotation**:
   - Draw bounding boxes (green=compliant, red=violation)
   - Add labels with track IDs
   - Add statistics overlay
5. **Upload**: Send results and annotated video back

### Performance Optimization

- **Frame sampling**: Processes every 2nd frame by default (configurable)
- **Model optimization**: Uses efficient YOLOv8s for person detection
- **Temporary storage**: Auto-cleanup after processing

### File Locations

```
temp/
├── video_{chat_id}_{timestamp}/
│   ├── input_video.mp4          # Downloaded video
│   └── output_annotated.mp4      # Annotated result
```

Files are automatically deleted after sending.

---

## Troubleshooting

### "Video Too Large" Error

**Problem:** Video exceeds 20MB limit

**Solutions:**
1. Trim video to shorter duration
2. Compress video using:
   - [HandBrake](https://handbrake.fr/) (Desktop)
   - Video compressor apps (Mobile)
   - Online tools: [VideoSmaller](https://www.videosmaller.com/)

**Quick compression with ffmpeg:**
```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 output.mp4
```

### "Processing Failed" Error

**Problem:** Video format not supported or corrupted

**Solutions:**
1. Convert to MP4 format
2. Re-export video
3. Try a different video

**Convert with ffmpeg:**
```bash
ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
```

### Bot Not Responding

**Problem:** Bot not processing uploads

**Checks:**
1. Is bot running? Check terminal for "🤖 PPE-Watch Interactive Bot Started"
2. Check internet connection
3. Verify `.env` has correct `TELEGRAM_BOT_TOKEN`
4. Restart bot: `Ctrl+C` then rerun

### Slow Processing

**Problem:** Video takes very long to process

**Normal timings:**
- 10-second video: ~30s processing
- 30-second video: ~1-2min processing
- 1-minute video: ~3-5min processing

**Factors:**
- Video resolution (higher = slower)
- Number of people in frame
- GPU vs CPU (GPU is much faster)

---

## Running the Bot

### Manual Start

```bash
# Activate environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run bot
python -m src.delivery.telegram_bot_interactive
```

Keep terminal open while bot is running.

### Background Service (Linux)

Create systemd service at `/etc/systemd/system/ppe-bot.service`:

```ini
[Unit]
Description=PPE-Watch Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/SpecialProject
ExecStart=/path/to/.venv/bin/python -m src.delivery.telegram_bot_interactive
Restart=always

[Install]
WantedBy=multi-user.target
```

Commands:
```bash
sudo systemctl start ppe-bot      # Start
sudo systemctl stop ppe-bot       # Stop
sudo systemctl status ppe-bot     # Check status
sudo systemctl enable ppe-bot     # Auto-start on boot
```

### Background Service (Windows)

Use [NSSM](https://nssm.cc/) to create Windows service:

```cmd
nssm install PPE-Bot "C:\path\to\.venv\Scripts\python.exe" "-m" "src.delivery.telegram_bot_interactive"
nssm set PPE-Bot AppDirectory "C:\path\to\SpecialProject"
nssm start PPE-Bot
```

---

## Security Considerations

1. **Access Control**: Only users who know your bot username can send videos
2. **Data Privacy**: Videos are temporarily stored and auto-deleted
3. **No Cloud Storage**: Videos not permanently stored anywhere
4. **Local Processing**: All detection runs on your server

**Recommendations:**
- Don't share bot username publicly
- Keep bot token secret (in `.env`, never commit to git)
- Monitor `temp/` directory size periodically
- Consider adding user whitelist if needed

---

## Advanced: Standalone Video Processing

You can also process videos via command line:

```bash
python -m src.inference.video_processor \
  --video samples/test.mp4 \
  --output results/test_output \
  --model runs/helmet/train4/weights/best.pt \
  --conf 0.3
```

This is useful for:
- Batch processing multiple videos
- Testing without Telegram
- Integration with other systems

---

## FAQ

**Q: Can I send videos longer than 1 minute?**
A: Yes, as long as file size is under 20MB. Longer videos take more time to process.

**Q: Does the bot save my videos?**
A: No, videos are deleted immediately after processing and sending results.

**Q: Can multiple people use the bot at once?**
A: Yes, each upload is processed independently. However, processing is sequential (one at a time).

**Q: Can I get just the count without annotated video?**
A: Currently, annotated video is always sent. You can modify `save_annotated=False` in code to skip.

**Q: What if there are no people in the video?**
A: Bot will report "0 violators, 0 compliant persons" - valid result.

**Q: Can I adjust detection sensitivity?**
A: Yes, edit `conf_thresh` parameter in [video_processor.py](src/inference/video_processor.py) (default: 0.3)

---

## Next Steps

1. **Test with Sample Video**:
   - Send one of the `samples/*.mp4` videos to test
   - Verify you receive results and annotated video

2. **Record Real Scenario**:
   - Record short video of work area
   - Send to bot
   - Review results

3. **Share with Team**:
   - Give bot username to supervisors
   - They can send videos directly from their phones
   - Instant compliance checking!

---

## Support

**Issues or Questions?**
- Check logs in terminal where bot is running
- Review this guide's troubleshooting section
- Check [SCHEDULER_SETUP.md](SCHEDULER_SETUP.md) for automation setup
- See [README.md](README.md) for general system overview

**Bot Commands in Telegram:**
- `/help` - Show all available commands
- `/status` - Check if system is working

---

## Summary

The video upload feature transforms your PPE-Watch bot into an **on-demand compliance checker**:

- ✅ No CCTV setup required
- ✅ Works with any video source
- ✅ Instant violation detection
- ✅ Visual feedback with annotated video
- ✅ Easy to use (just send video)

Perfect for scenarios where live CCTV isn't available but you need to verify compliance from recorded footage!
