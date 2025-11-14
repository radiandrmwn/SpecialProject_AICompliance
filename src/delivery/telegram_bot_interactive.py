# -*- coding: utf-8 -*-
"""
Interactive Telegram Bot for PPE-Watch

Bot that can respond to commands:
- /start - Start bot and show welcome
- /help - Show available commands
- /status - Check system status
- /report [date] - Get report for specific date or today
- /latest - Get latest report available
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional
import time

# Setup logging to both file and console
log_dir = Path(__file__).parent.parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'bot.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass  # Might fail if running with pythonw (no stdout)

try:
    from dotenv import load_dotenv
    import requests
except ImportError:
    logger.info("\n❌ Error: Required packages not installed")
    logger.info("📦 Install with: pip install python-dotenv requests")
    sys.exit(1)

# Import existing TelegramBot class
from src.delivery.telegram_bot import TelegramBot


class InteractiveTelegramBot:
    """Interactive Telegram bot with command handling."""

    def __init__(self):
        """Initialize interactive bot."""
        load_dotenv()

        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.telegram_bot = TelegramBot(self.bot_token, self.chat_id)

        # For tracking processed updates
        self.last_update_id = 0

        logger.info("🤖 Interactive PPE-Watch Bot initialized")
        logger.info(f"📱 Monitoring for commands...")

    def get_updates(self, offset: Optional[int] = None, timeout: int = 30) -> list:
        """
        Get updates from Telegram (long polling).

        Args:
            offset: Update ID to start from
            timeout: Long polling timeout

        Returns:
            List of updates
        """
        url = f"{self.base_url}/getUpdates"
        params = {
            'timeout': timeout,
            'allowed_updates': ['message']  # Includes video messages
        }

        if offset:
            params['offset'] = offset

        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            response.raise_for_status()
            data = response.json()

            if data.get('ok'):
                return data.get('result', [])
            return []

        except Exception as e:
            logger.info(f"⚠️ Error getting updates: {e}")
            return []

    def download_file(self, file_id: str, save_path: Path) -> bool:
        """
        Download file from Telegram.

        Args:
            file_id: Telegram file ID
            save_path: Path to save downloaded file

        Returns:
            Success status
        """
        try:
            # Get file path
            url = f"{self.base_url}/getFile"
            response = requests.get(url, params={'file_id': file_id}, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get('ok'):
                logger.info(f"❌ Failed to get file info: {data}")
                return False

            file_path = data['result']['file_path']
            file_size = data['result'].get('file_size', 0)

            # Check file size (Telegram bot API limit is 20MB)
            if file_size > 20 * 1024 * 1024:
                logger.info(f"⚠️ File too large: {file_size / (1024*1024):.1f}MB (max 20MB)")
                return False

            # Download file
            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            file_response = requests.get(file_url, timeout=30)
            file_response.raise_for_status()

            # Save to disk
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(file_response.content)

            logger.info(f"✅ Downloaded file: {save_path} ({file_size / 1024:.1f}KB)")
            return True

        except Exception as e:
            logger.info(f"❌ Error downloading file: {e}")
            return False

    def send_message(self, chat_id: int, text: str, parse_mode: str = None):
        """Send message to specific chat."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }

        if parse_mode:
            payload['parse_mode'] = parse_mode

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.info(f"❌ Error sending message: {e}")
            return None

    def handle_start(self, chat_id: int, user_name: str):
        """Handle /start command."""
        message = (
            f"👋 Hi {user_name}!\n\n"
            "🤖 PPE-Watch Reporter Bot\n\n"
            "I can help you with PPE compliance reports!\n\n"
            "📹 Video Processing:\n"
            "• Send me a video file to check for violations\n"
            "• I'll detect people without helmets & vests\n"
            "• You'll get instant results + annotated video\n\n"
            "📊 Daily Reports:\n"
            "• /report - Get today's report\n"
            "• /report YYYY-MM-DD - Get specific date\n"
            "• /latest - Get most recent report\n\n"
            "⚙️ Other Commands:\n"
            "• /status - Check system status\n"
            "• /help - Show help message\n\n"
            "💡 Tip: Daily reports are generated at 18:00"
        )

        self.send_message(chat_id, message)
        logger.info(f"✅ Sent welcome to {user_name} (Chat ID: {chat_id})")

    def handle_help(self, chat_id: int):
        """Handle /help command."""
        message = (
            "📚 PPE-Watch Bot Commands\n\n"
            "🎥 Video Processing:\n"
            "• Send a video file (up to 20MB)\n"
            "• I'll process it and detect violations\n"
            "• You'll receive results + annotated video\n"
            "• Supported formats: MP4, AVI, MOV\n\n"
            "📊 Daily Reports:\n"
            "• /report - Get today's report\n"
            "• /report 2025-11-06 - Get specific date\n"
            "• /report yesterday - Get yesterday's report\n"
            "• /latest - Get most recent available report\n\n"
            "⚙️ System:\n"
            "• /status - Check system status\n"
            "• /help - Show this help message\n\n"
            "Examples:\n"
            "1. Send video → Get instant analysis\n"
            "2. /report → Get today's report\n"
            "3. /report 2025-11-02 → Specific date\n"
            "4. /latest → Most recent report\n\n"
            "Need help? Contact your system administrator."
        )

        self.send_message(chat_id, message)
        logger.info(f"✅ Sent help to Chat ID: {chat_id}")

    def handle_status(self, chat_id: int):
        """Handle /status command."""
        # Check system components
        events_dir = Path("events")
        reports_dir = Path("reports")
        model_path = Path("runs/helmet/train4/weights/best.pt")

        status_ok = "✅"
        status_error = "❌"

        # Check directories
        events_exist = events_dir.exists()
        reports_exist = reports_dir.exists()
        model_exist = model_path.exists()

        # Count files
        event_files = len(list(events_dir.glob("*.csv"))) if events_exist else 0
        report_files = len(list(reports_dir.glob("*.pdf"))) if reports_exist else 0

        # Get latest event
        latest_event = None
        if events_exist:
            event_files_list = sorted(events_dir.glob("events_*.csv"))
            if event_files_list:
                latest_event = event_files_list[-1].stem.replace('events_', '')

        message = (
            "🔍 System Status Check\n\n"
            f"Core Components:\n"
            f"• Model: {status_ok if model_exist else status_error} "
            f"{'Found' if model_exist else 'Missing'}\n"
            f"• Events Dir: {status_ok if events_exist else status_error} "
            f"({event_files} files)\n"
            f"• Reports Dir: {status_ok if reports_exist else status_error} "
            f"({report_files} files)\n\n"
            f"Latest Data:\n"
            f"• Last Event Log: {latest_event or 'None'}\n\n"
            f"Bot Status:\n"
            f"• Bot Token: {status_ok} Active\n"
            f"• Connection: {status_ok} Online\n"
            f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"System is {'✅ operational' if all([model_exist, events_exist, reports_exist]) else '⚠️ partially operational'}"
        )

        self.send_message(chat_id, message)
        logger.info(f"✅ Sent status to Chat ID: {chat_id}")

    def handle_report(self, chat_id: int, date_arg: Optional[str] = None):
        """Handle /report command."""
        # Parse date argument
        if not date_arg or date_arg.lower() == 'today':
            target_date = date.today()
        elif date_arg.lower() == 'yesterday':
            target_date = date.today() - timedelta(days=1)
        else:
            # Try to parse as YYYY-MM-DD
            try:
                target_date = datetime.strptime(date_arg, '%Y-%m-%d').date()
            except ValueError:
                self.send_message(
                    chat_id,
                    f"❌ Invalid date format: {date_arg}\n\n"
                    "Please use:\n"
                    "• /report - Today\n"
                    "• /report yesterday - Yesterday\n"
                    "• /report YYYY-MM-DD - Specific date\n\n"
                    "Example: /report 2025-11-02"
                )
                return

        date_str = target_date.strftime('%Y-%m-%d')

        # Check if report exists
        reports_dir = Path("reports")
        pdf_path = reports_dir / f"report_{date_str}.pdf"
        charts_path = reports_dir / f"report_{date_str}_charts.png"
        csv_path = reports_dir / f"report_{date_str}.csv"

        if not pdf_path.exists() and not charts_path.exists():
            # Report doesn't exist
            self.send_message(
                chat_id,
                f"⚠️ Report Not Found\n\n"
                f"No report available for {date_str}\n\n"
                f"💡 Try:\n"
                f"• /latest - Get most recent report\n"
                f"• /report yesterday - Yesterday's report\n\n"
                f"Reports are generated daily at 18:00"
            )
            logger.info(f"⚠️ No report found for {date_str}")
            return

        # Send report
        self.send_message(
            chat_id,
            f"📊 Fetching Report\n\n"
            f"Date: {date_str}\n"
            f"Please wait..."
        )

        logger.info(f"📤 Sending report for {date_str} to Chat ID: {chat_id}")

        # Use existing TelegramBot to send
        temp_bot = TelegramBot(self.bot_token, str(chat_id))
        success = temp_bot.send_daily_report(date_str)

        if success:
            logger.info(f"✅ Report sent for {date_str}")
        else:
            self.send_message(
                chat_id,
                f"❌ Error sending report for {date_str}\n\n"
                "Please contact administrator."
            )

    def handle_latest(self, chat_id: int):
        """Handle /latest command - get most recent report."""
        reports_dir = Path("reports")

        if not reports_dir.exists():
            self.send_message(
                chat_id,
                "⚠️ No reports directory found.\n\n"
                "Reports will be available after first video processing."
            )
            return

        # Find latest PDF
        pdf_files = sorted(reports_dir.glob("report_*.pdf"))

        if not pdf_files:
            self.send_message(
                chat_id,
                "⚠️ No reports available yet.\n\n"
                "Reports are generated daily at 18:00"
            )
            return

        # Get latest
        latest_pdf = pdf_files[-1]
        date_str = latest_pdf.stem.replace('report_', '')

        self.send_message(
            chat_id,
            f"📊 Latest Report\n\n"
            f"Date: {date_str}\n"
            f"Sending..."
        )

        logger.info(f"📤 Sending latest report ({date_str}) to Chat ID: {chat_id}")

        # Send report
        temp_bot = TelegramBot(self.bot_token, str(chat_id))
        temp_bot.send_daily_report(date_str)

    def handle_video(self, chat_id: int, video_data: dict, user_name: str):
        """Handle video upload - process for violations."""
        file_id = video_data.get('file_id')
        file_size = video_data.get('file_size', 0)

        logger.info(f"\n🎥 Video received from {user_name} (Chat ID: {chat_id})")
        logger.info(f"   File ID: {file_id}, Size: {file_size / (1024*1024):.2f}MB")

        # Check file size (20MB limit for Telegram Bot API)
        if file_size > 20 * 1024 * 1024:
            self.send_message(
                chat_id,
                f"❌ Video Too Large\n\n"
                f"Your video is {file_size / (1024*1024):.1f}MB\n"
                f"Maximum size: 20MB\n\n"
                f"💡 Tip: Trim or compress your video and try again"
            )
            return

        # Send processing message
        self.send_message(
            chat_id,
            f"🎥 Video Received\n\n"
            f"Size: {file_size / (1024*1024):.1f}MB\n"
            f"Processing for violations...\n\n"
            f"⏳ This may take a few moments"
        )

        try:
            # Create temp directory for processing
            temp_dir = Path("temp") / f"video_{chat_id}_{int(time.time())}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            video_path = temp_dir / "input_video.mp4"

            # Download video
            if not self.download_file(file_id, video_path):
                self.send_message(
                    chat_id,
                    "❌ Failed to download video. Please try again."
                )
                return

            # Run inference
            logger.info(f"   🔍 Running inference on video...")
            from src.inference.video_processor import process_video_for_violations

            results = process_video_for_violations(video_path, temp_dir)

            if results is None:
                self.send_message(
                    chat_id,
                    "❌ Processing Failed\n\n"
                    "Could not process video. Please check:\n"
                    "• Video format (MP4, AVI, MOV)\n"
                    "• Video is not corrupted\n"
                    "• Try a different video"
                )
                return

            # Send results
            total_violations = results['total_violations']
            unique_violators = results['unique_violators']
            compliant = results['compliant_persons']
            total_frames = results['total_frames']
            duration = results['duration']

            message = (
                f"✅ Processing Complete\n\n"
                f"Video Statistics:\n"
                f"• Duration: {duration:.1f} seconds\n"
                f"• Frames processed: {total_frames}\n\n"
                f"Violation Results:\n"
                f"• Unique violators (no helmet & vest): {unique_violators}\n"
                f"• Compliant persons (with helmet & vest): {compliant}\n"
                f"• Total detections: {total_violations}\n\n"
            )

            if unique_violators > 0:
                message += f"⚠️ {unique_violators} person(s) detected without PPE\n\n"
            else:
                message += "✅ No violations detected - All compliant!\n\n"

            # Add zone breakdown if available
            if results.get('zones'):
                message += "Violations by Zone:\n"
                for zone_name, count in results['zones'].items():
                    message += f"• {zone_name}: {count}\n"
                message += "\n"

            message += "💡 Tip: Send another video anytime to check compliance"

            self.send_message(chat_id, message)

            # Send annotated video if available (try .avi first, then .mp4)
            annotated_video = temp_dir / "output_annotated.avi"
            if not annotated_video.exists():
                annotated_video = temp_dir / "output_annotated.mp4"

            if annotated_video.exists():
                logger.info(f"   📤 Sending annotated video...")
                self.send_video(chat_id, annotated_video, "Annotated video with detections")
            else:
                logger.info(f"   ⚠️ Annotated video not found")

            # Generate updated daily report
            try:
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')

                logger.info(f"   📊 Regenerating daily report for {today}...")

                from src.reporting.aggregate_day import DailyAggregator
                from src.reporting.charts import ChartGenerator
                from src.reporting.make_pdf import PDFReportGenerator

                # Aggregate events
                aggregator = DailyAggregator(events_dir="events", reports_dir="reports")
                stats = aggregator.generate_report(today)

                if stats:
                    # Generate charts
                    chart_gen = ChartGenerator()
                    charts_path = chart_gen.generate_charts(today)

                    # Generate PDF
                    pdf_gen = PDFReportGenerator()
                    pdf_path = pdf_gen.generate_report(today, stats, charts_path)

                    logger.info(f"   ✅ Report updated: {pdf_path}")

                    # Send notification about report update
                    self.send_message(
                        chat_id,
                        f"\n📊 Daily Report Updated\n\n"
                        f"Your video has been added to today's report.\n"
                        f"Use /report {today} or /latest to view the updated report."
                    )
                else:
                    logger.info(f"   ℹ️ No aggregated stats available yet")

            except FileNotFoundError:
                logger.info(f"   ℹ️ Events file not found yet (will be created on next event)")
            except Exception as e:
                logger.info(f"   ⚠️ Could not regenerate report: {e}")
                import traceback
                logger.exception("Exception details:")
                # Non-critical error, continue

            # Cleanup
            import shutil
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"   🧹 Cleaned up temporary files")
            except:
                pass

        except Exception as e:
            logger.info(f"❌ Error processing video: {e}")
            import traceback
            logger.exception("Exception details:")

            self.send_message(
                chat_id,
                f"❌ Error Processing Video\n\n"
                f"An error occurred: {str(e)}\n\n"
                f"Please contact administrator if issue persists."
            )

    def send_video(self, chat_id: int, video_path: Path, caption: str = ""):
        """Send video file to chat with extended timeout for large files."""
        url = f"{self.base_url}/sendVideo"

        # Check file size
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        logger.info(f"   📦 Video size: {file_size_mb:.1f}MB")

        # Set timeout based on file size (minimum 120s, +30s per 10MB)
        timeout = max(120, int(120 + (file_size_mb / 10) * 30))
        logger.info(f"   ⏱️  Upload timeout: {timeout}s")

        try:
            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {
                    'chat_id': chat_id,
                    'caption': caption
                }
                logger.info(f"   📤 Uploading video to Telegram...")
                response = requests.post(url, data=data, files=files, timeout=timeout)
                response.raise_for_status()
                logger.info(f"   ✅ Video sent successfully!")
                return response.json()
        except requests.exceptions.Timeout:
            logger.info(f"❌ Upload timeout after {timeout}s - video too large or slow connection")
            return None
        except Exception as e:
            logger.info(f"❌ Error sending video: {e}")
            return None

    def handle_unknown(self, chat_id: int, command: str):
        """Handle unknown command."""
        message = (
            f"❓ Unknown command: {command}\n\n"
            "Try /help to see available commands.\n\n"
            "Quick Commands:\n"
            "• /report - Today's report\n"
            "• /latest - Latest report\n"
            "• /status - System status"
        )

        self.send_message(chat_id, message)

    def process_message(self, message_data: dict):
        """Process incoming message."""
        message = message_data.get('message', {})

        if not message:
            return

        chat_id = message.get('chat', {}).get('id')
        from_user = message.get('from', {})
        user_name = from_user.get('first_name', 'User')

        # Check for video upload
        if 'video' in message:
            video_data = message['video']
            self.handle_video(chat_id, video_data, user_name)
            return

        # Check for command
        text = message.get('text', '')

        if not text.startswith('/'):
            # Not a command or video - send help
            self.send_message(
                chat_id,
                "👋 Hi! Send me:\n"
                "• A video file to check for violations\n"
                "• /help to see all commands"
            )
            return

        # Parse command and arguments
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        logger.info(f"\n📩 Command received: {command} from {user_name} (Chat ID: {chat_id})")

        # Route to handlers
        if command == '/start':
            self.handle_start(chat_id, user_name)
        elif command == '/help':
            self.handle_help(chat_id)
        elif command == '/status':
            self.handle_status(chat_id)
        elif command == '/report':
            self.handle_report(chat_id, arg)
        elif command == '/latest':
            self.handle_latest(chat_id)
        else:
            self.handle_unknown(chat_id, command)

    def run(self):
        """Run bot in polling mode."""
        logger.info("\n" + "=" * 70)
        logger.info("🤖 PPE-Watch Interactive Bot Started")
        logger.info("=" * 70)
        logger.info("\n💡 Bot is now listening for commands...")
        logger.info("📱 Users can send commands like /start, /help, /report")
        logger.info("⏹️  Press Ctrl+C to stop\n")

        try:
            while True:
                # Get updates
                updates = self.get_updates(offset=self.last_update_id + 1)

                for update in updates:
                    # Update last_update_id
                    self.last_update_id = update.get('update_id', 0)

                    # Process message
                    try:
                        self.process_message(update)
                    except Exception as e:
                        logger.info(f"❌ Error processing message: {e}")
                        import traceback
                        logger.exception("Exception details:")

                # Small delay to prevent API spam
                if not updates:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("\n\n👋 Bot stopped by user")
            logger.info("✅ Shutdown complete")


def main():
    """Main entry point."""
    try:
        bot = InteractiveTelegramBot()
        bot.run()
    except Exception as e:
        logger.info(f"\n❌ Error: {e}")
        import traceback
        logger.exception("Exception details:")
        sys.exit(1)


if __name__ == '__main__':
    main()
