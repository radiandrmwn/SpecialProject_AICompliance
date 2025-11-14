# PPE-Watch Automation Scripts

This folder contains Windows batch scripts for managing the Telegram bot.

## Available Scripts

| Script | Description |
|--------|-------------|
| `start_bot_background.bat` | Start bot in background (minimized window) |
| `start_bot_simple.bat` | Start bot with visible terminal (for testing) |
| `stop_bot.bat` | Stop the running bot |
| `restart_bot.bat` | Restart the bot |
| `check_bot_status.bat` | Check if bot is running and view logs |
| `setup_windows_venv.bat` | Create/recreate Windows virtual environment |

## Quick Start

**Start the bot:**
```bash
start_bot_background.bat
```

**Check if running:**
```bash
check_bot_status.bat
```

**Stop the bot:**
```bash
stop_bot.bat
```

## Auto-Start on Login

To make the bot start automatically when you login to Windows:

1. Right-click `start_bot_background.bat` → Create shortcut
2. Press `Win+R` → Type `shell:startup` → Enter
3. Move the shortcut to the Startup folder

Done! Bot will now start automatically on login.

## More Information

See [../markdown/BOT_SETUP_GUIDE.md](../markdown/BOT_SETUP_GUIDE.md) for detailed setup instructions and troubleshooting.
