# PPE-Watch Telegram Bot - Background Setup Guide

This guide shows you how to run the Telegram bot in the background on Windows, so it stays running even when you close the terminal.

---

## Quick Start (Easiest)

### Option A: Manual Start (For Testing)

**Just double-click:**
```
automatescript\start_bot_background.bat
```

The bot will start in the background (no window).

**To check if it's running:**
```
automatescript\check_bot_status.bat
```

**To stop the bot:**
```
automatescript\stop_bot.bat
```

**To restart the bot:**
```
automatescript\restart_bot.bat
```

---

### Option B: Auto-Start on Windows Login (Recommended)

**Make the bot start automatically every time you login to Windows:**

1. **Create a shortcut:**
   - Right-click `automatescript\start_bot_background.bat`
   - Click "Create shortcut"

2. **Move to Startup folder:**
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter
   - Move the shortcut to this folder

3. **Done!**
   - Bot will auto-start every time you login to Windows
   - No need to manually start it anymore

**To disable auto-start:**
   - Go back to the Startup folder (`Win+R` → `shell:startup`)
   - Delete the shortcut

---

## Helper Scripts

### `start_bot_background.bat`
**What it does:**
- Starts the Telegram bot in the background (no window)
- Uses `pythonw.exe` instead of `python.exe` (runs hidden)
- Bot will keep running even if you close the command prompt

**Usage:**
```bash
# Just double-click the file
# Or run from command prompt:
automatescript\start_bot_background.bat
```

---

### `stop_bot.bat`
**What it does:**
- Stops the running Telegram bot
- Finds and kills the pythonw.exe process running the bot

**Usage:**
```bash
# Double-click or run:
automatescript\stop_bot.bat
```

**When to use:**
- Need to restart the bot with new changes
- Bot is misbehaving
- Want to stop the bot temporarily

---

### `restart_bot.bat`
**What it does:**
- Stops the bot (if running)
- Waits 2 seconds
- Starts the bot again in background

**Usage:**
```bash
# Double-click or run:
automatescript\restart_bot.bat
```

**When to use:**
- After making changes to the bot code
- After updating .env file
- Bot seems stuck or unresponsive

---

### `check_bot_status.bat`
**What it does:**
- Checks if the bot is currently running
- Shows process details (PID, memory usage)
- Shows last 10 lines of the log file

**Usage:**
```bash
# Double-click or run:
automatescript\check_bot_status.bat
```

**Output example:**
```
======================================
PPE-Watch Bot Status Check
======================================

Status: RUNNING

Process details:
ProcessId  CreationDate         WorkingSetSize
12345      20250112123045.123   52428800

======================================
Latest log entries:
======================================
2025-01-12 12:30:45 - INFO - 🤖 PPE-Watch Interactive Bot Started
2025-01-12 12:30:45 - INFO - 💡 Bot is now listening for commands...
2025-01-12 12:31:20 - INFO - ✅ Sent welcome to Radian Try (Chat ID: 5982977160)
...
```

---

## Checking Logs

**Log file location:**
```
logs/bot.log
```

**View logs:**

**Option 1: Open with Notepad**
```
notepad logs\bot.log
```

**Option 2: View last 20 lines (PowerShell)**
```powershell
Get-Content logs\bot.log -Tail 20
```

**Option 3: Real-time log monitoring (PowerShell)**
```powershell
Get-Content logs\bot.log -Wait -Tail 20
```
(Press Ctrl+C to stop)

**Log file contains:**
- Bot startup messages
- All commands received
- Video processing progress
- Errors and exceptions
- Telegram API responses

---

## Troubleshooting

### Bot not starting?

1. **Check if Python virtual environment is activated:**
   ```bash
   .venv\Scripts\activate
   ```

2. **Check if .env file exists and has correct token:**
   ```bash
   type .env
   ```

3. **Check logs for errors:**
   ```bash
   notepad logs\bot.log
   ```

4. **Try running in terminal first (to see errors):**
   ```bash
   python src\delivery\telegram_bot_interactive.py
   ```

### Bot already running?

**Error:** "Bot is already running"

**Solution:**
```bash
automatescript\stop_bot.bat
# Wait 2 seconds
automatescript\start_bot_background.bat
```

### Bot not responding to commands?

1. **Check if bot is running:**
   ```bash
   automatescript\check_bot_status.bat
   ```

2. **Check internet connection**

3. **Check logs for errors:**
   ```bash
   notepad logs\bot.log
   ```

4. **Restart the bot:**
   ```bash
   automatescript\restart_bot.bat
   ```

### How to stop bot completely?

**If normal stop doesn't work:**

1. **Open Task Manager** (Ctrl+Shift+Esc)
2. **Go to "Details" tab**
3. **Find `pythonw.exe`**
4. **Right-click → End task**

---

## Advanced: Run Bot as Windows Service (Optional)

**For 24/7 operation even when logged out:**

See `WINDOWS_SERVICE_SETUP.md` for instructions on setting up the bot as a Windows Service using NSSM.

**Benefits:**
- ✅ Bot runs even when logged out
- ✅ Auto-restart on crash
- ✅ Managed via Windows Services

**Drawbacks:**
- Requires additional software (NSSM)
- More complex setup

---

## FAQ

### Q: Does the bot run when laptop is asleep/hibernated?
**A:** No. The laptop must be powered on and running Windows.

### Q: Does the bot run when I close the laptop lid?
**A:** Depends on your power settings. If laptop goes to sleep, bot will pause. Configure Windows to "Do nothing" when lid closes (Power Options) if you want bot to keep running.

### Q: Can the bot run when I'm not logged in to Windows?
**A:** No (with current setup). For that, you need to setup the bot as a Windows Service (see Advanced section) or deploy to cloud.

### Q: How much memory/CPU does the bot use?
**A:** Very little when idle (50-100MB RAM, <1% CPU). Increases when processing videos (up to 500MB RAM, 20-50% CPU during processing).

### Q: Will the bot survive Windows updates/restarts?
**A:** If you setup auto-start (Option B), the bot will restart automatically after Windows reboots. But you need to login to Windows first.

### Q: How do I update the bot code?
**A:**
1. Stop the bot: `automatescript\stop_bot.bat`
2. Make your code changes
3. Start the bot: `automatescript\start_bot_background.bat`

### Q: Can I run multiple bots at the same time?
**A:** No, only one instance should run at a time (they share the same Telegram bot token).

---

## Next Steps

**For Production Deployment (24/7 without laptop):**

See `CLOUD_DEPLOYMENT_GUIDE.md` for instructions on deploying to:
- Oracle Cloud Free Tier (free forever)
- DigitalOcean ($5/month)
- Railway.app (free tier available)
- Raspberry Pi (home server)

---

**Need help?** Check `logs/bot.log` for detailed error messages.
