# Windows Task Scheduler Setup Guide

## 🎯 Goal
Setup automated daily report generation and delivery at 18:00 every day.

---

## 📋 Step-by-Step Instructions

### **Step 1: Open Task Scheduler**

1. Press `Win + R` (Run dialog)
2. Type: `taskschd.msc`
3. Press Enter

Or:
- Search "Task Scheduler" in Start Menu

---

### **Step 2: Create New Task**

1. In Task Scheduler, click **"Create Basic Task..."** (right sidebar)

2. **Name your task:**
   - Name: `PPE-Watch Daily Report`
   - Description: `Automated daily PPE compliance report generation and delivery`
   - Click **Next**

---

### **Step 3: Set Trigger (When to Run)**

1. Select **"Daily"**
2. Click **Next**

3. **Set start time:**
   - Start date: Today's date
   - Start time: **18:00:00** (6:00 PM)
   - Recur every: **1 days**
   - Click **Next**

---

### **Step 4: Set Action (What to Run)**

1. Select **"Start a program"**
2. Click **Next**

3. **Program/script:**
   ```
   C:\Users\Radian Try\Documents\2nd Asia University (TW)\2nd Semester\SpecialProject\scripts\run_daily_automation.bat
   ```

   **IMPORTANT:** Click "Browse..." and navigate to select the `.bat` file!

4. **Add arguments (optional):**
   ```
   scheduled
   ```
   (This prevents the pause at the end)

5. **Start in (optional):**
   ```
   C:\Users\Radian Try\Documents\2nd Asia University (TW)\2nd Semester\SpecialProject
   ```

6. Click **Next**

---

### **Step 5: Review and Finish**

1. Check the summary
2. ✅ Check **"Open the Properties dialog for this task when I click Finish"**
3. Click **Finish**

---

### **Step 6: Configure Additional Settings**

Properties dialog will open. Configure these:

#### **General Tab:**
- ✅ Check **"Run whether user is logged on or not"**
- ✅ Check **"Run with highest privileges"**
- Configure for: **Windows 10**

#### **Triggers Tab:**
- Verify trigger is correct (Daily at 18:00)
- Optional: Click "Edit" to add:
  - ✅ Check **"Stop task if it runs longer than: 1 hour"**

#### **Actions Tab:**
- Verify action is correct (run_daily_automation.bat)

#### **Conditions Tab:**
- ✅ UN-check **"Start the task only if the computer is on AC power"** (if laptop)
- ✅ Check **"Wake the computer to run this task"** (optional)

#### **Settings Tab:**
- ✅ Check **"Allow task to be run on demand"**
- ✅ Check **"Run task as soon as possible after a scheduled start is missed"**
- If the task fails, restart every: **10 minutes**
- Attempt to restart up to: **3 times**

Click **OK**

---

### **Step 7: Test the Task**

1. In Task Scheduler, find your task: `PPE-Watch Daily Report`
2. Right-click → **"Run"**
3. Watch the "Last Run Result" and "Last Run Time"
4. Check Telegram - you should receive a report!

---

## 📊 Monitoring

### **Check Task Status:**
1. Open Task Scheduler
2. Select your task
3. Look at bottom panel:
   - **Last Run Time:** When it last ran
   - **Last Run Result:** Success (0x0) or Error code
   - **Next Run Time:** When it will run next

### **View Logs:**
Logs are saved in:
```
C:\Users\Radian Try\Documents\2nd Asia University (TW)\2nd Semester\SpecialProject\logs\daily_automation_YYYYMM.log
```

Example: `daily_automation_202511.log`

---

## 🐛 Troubleshooting

### **Task doesn't run:**
1. Check "Task Scheduler Library" for your task
2. Right-click → Properties → History tab (enable if disabled)
3. Check trigger settings (time, date, enabled)

### **Task runs but fails:**
1. Check log file in `logs/` folder
2. Try running `.bat` file manually (double-click)
3. Check Python path and dependencies

### **"No events file found" error:**
- This is normal if no video was processed that day
- Task will skip and wait for next day

### **Telegram not sending:**
- Check `.env` file has correct credentials
- Check internet connection
- Check Telegram bot token is valid

---

## ✅ Success Indicators

When working correctly, you'll see:
- ✅ Task shows "Ready" status
- ✅ "Last Run Result" = 0x0 (Success)
- ✅ Log file shows "✅ Daily Automation Completed Successfully!"
- ✅ Telegram receives report at 18:00 daily

---

## 🎯 What Happens Automatically

Every day at 18:00:
1. Script checks for yesterday's events
2. Generates charts (PNG)
3. Generates PDF report
4. Sends everything via Telegram bot
5. Logs results to file

**No manual intervention needed!** 🚀

---

## 📝 Notes

- Task runs **every day** at 18:00
- Processes **yesterday's** data by default
- Requires **Windows** to be running (not sleep/hibernate)
- If PC is off, task runs when PC starts (if configured)
- Logs kept in `logs/` folder for troubleshooting

---

## 🔧 Manual Run Commands

If you need to run manually:

```bash
# Run for yesterday (default)
python scripts/daily_report_automation.py

# Run for specific date
python scripts/daily_report_automation.py --date 2025-11-06

# Run for today
python scripts/daily_report_automation.py --today
```

---

## 🎊 Done!

Your PPE-Watch system is now **fully automated**! 🚀

Reports will be generated and sent automatically every day at 18:00.
