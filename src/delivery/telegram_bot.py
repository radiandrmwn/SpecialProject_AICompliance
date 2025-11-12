#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot for PPE-Watch Notifications

Sends daily compliance reports via Telegram.
"""

import sys
import os
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
except ImportError:
    print("\n❌ Error: python-dotenv not installed")
    print("📦 Install with: pip install python-dotenv")
    sys.exit(1)


class TelegramBot:
    """Telegram bot for sending PPE compliance reports."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram bot.

        Args:
            bot_token: Telegram bot token (from BotFather)
            chat_id: Telegram chat ID (recipient)
        """
        # Load from .env if not provided
        if bot_token is None or chat_id is None:
            load_dotenv()
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            raise ValueError(
                "Telegram credentials not found!\n"
                "Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file"
            )

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = None) -> dict:
        """
        Send text message.

        Args:
            text: Message text
            parse_mode: Message formatting (Markdown or HTML)

        Returns:
            API response
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending message: {e}")
            raise

    def send_document(self, file_path: Path, caption: Optional[str] = None) -> dict:
        """
        Send document (PDF, image, etc).

        Args:
            file_path: Path to file
            caption: Optional caption

        Returns:
            API response
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self.base_url}/sendDocument"

        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': self.chat_id}
            if caption:
                data['caption'] = caption
                data['parse_mode'] = 'Markdown'

            try:
                response = requests.post(url, data=data, files=files, timeout=60)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"❌ Error sending document: {e}")
                raise

    def send_photo(self, file_path: Path, caption: Optional[str] = None) -> dict:
        """
        Send photo/image.

        Args:
            file_path: Path to image
            caption: Optional caption

        Returns:
            API response
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self.base_url}/sendPhoto"

        with open(file_path, 'rb') as f:
            files = {'photo': f}
            data = {'chat_id': self.chat_id}
            if caption:
                data['caption'] = caption
                data['parse_mode'] = 'Markdown'

            try:
                response = requests.post(url, data=data, files=files, timeout=60)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"❌ Error sending photo: {e}")
                raise

    def send_daily_report(self, date_str: str, reports_dir: str = "reports") -> bool:
        """
        Send complete daily report (text summary + charts + PDF).

        Args:
            date_str: Date in format YYYY-MM-DD
            reports_dir: Reports directory

        Returns:
            True if successful
        """
        reports_path = Path(reports_dir)

        # File paths
        pdf_path = reports_path / f"report_{date_str}.pdf"
        charts_path = reports_path / f"report_{date_str}_charts.png"
        csv_path = reports_path / f"report_{date_str}.csv"

        print(f"\n{'=' * 70}")
        print(f"Sending Daily Report via Telegram - {date_str}")
        print('=' * 70)

        try:
            # Load summary stats from CSV if exists
            summary_text = self._create_summary_message(date_str, csv_path)

            # 1. Send text summary
            print("\n📤 Sending text summary...")
            print(f"DEBUG: Message content:\n{summary_text}")
            print(f"DEBUG: Message length: {len(summary_text)}")
            self.send_message(summary_text)
            print("   ✅ Text sent")

            # 2. Send charts image
            if charts_path.exists():
                print("\n📤 Sending charts...")
                self.send_photo(
                    charts_path,
                    caption=f"📊 PPE Compliance Charts - {date_str}"
                )
                print("   ✅ Charts sent")
            else:
                print("   ⚠️ Charts not found, skipping")

            # 3. Send PDF report
            if pdf_path.exists():
                print("\n📤 Sending PDF report...")
                self.send_document(
                    pdf_path,
                    caption=f"📄 Full Report - {date_str}"
                )
                print("   ✅ PDF sent")
            else:
                print("   ⚠️ PDF not found, skipping")

            print(f"\n{'=' * 70}")
            print("✅ Daily report sent successfully!")
            print('=' * 70)

            return True

        except Exception as e:
            print(f"\n❌ Error sending daily report: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_summary_message(self, date_str: str, csv_path: Path) -> str:
        """
        Create text summary message.

        Args:
            date_str: Report date
            csv_path: Path to summary CSV

        Returns:
            Formatted message text
        """
        # Header (simplified without special characters)
        message = f"🚨 PPE Compliance Report\n"
        message += f"📅 Date: {date_str}\n"
        message += f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += "\n" + "=" * 30 + "\n\n"

        # Try to load stats from CSV (multi-section format)
        if csv_path.exists():
            try:
                # Parse CSV with multiple sections
                stats = self._parse_multi_section_csv(csv_path)

                if stats:
                    message += f"📊 Summary Statistics\n"
                    message += f"• Total Events: {stats.get('total_events', 'N/A')}\n"
                    message += f"• Unique Violators: {stats.get('unique_violators', 'N/A')}\n"
                    message += f"• Zones Monitored: {len(stats.get('zones', []))}\n\n"

                    # Zone breakdown
                    if stats.get('zones'):
                        message += f"🗺️ Zone Breakdown\n"
                        for zone_name, zone_count in stats['zones']:
                            message += f"• {zone_name}: {zone_count} violations\n"

                    # Top violators
                    if stats.get('top_violators'):
                        message += f"\n⚠️ Top Violators\n"
                        for track_id, count in list(stats['top_violators'])[:3]:
                            message += f"• Track #{track_id}: {count} violations\n"
                else:
                    message += "⚠️ No detailed stats available\n"

            except Exception as e:
                message += f"⚠️ Could not load detailed stats\n"
                message += f"   Error: {str(e)}\n"
        else:
            message += "📝 Summary\n"
            message += "Report files generated. See attachments for details.\n"

        # Footer
        message += "\n" + "=" * 30 + "\n"
        message += "🤖 Generated by PPE-Watch System\n"
        message += "💡 Only violations (no helmet) are logged\n"

        return message

    def _parse_multi_section_csv(self, csv_path: Path) -> dict:
        """
        Parse CSV with multiple sections.

        Args:
            csv_path: Path to CSV file

        Returns:
            Dictionary with parsed stats
        """
        stats = {}

        with open(csv_path, 'r') as f:
            lines = f.readlines()

        current_section = None

        for line in lines:
            line = line.strip()

            # Detect sections
            if line.startswith('==='):
                if 'DAILY SUMMARY' in line:
                    current_section = 'summary'
                elif 'ZONE STATISTICS' in line:
                    current_section = 'zones'
                elif 'TOP VIOLATORS' in line:
                    current_section = 'violators'
                continue

            # Skip empty lines
            if not line:
                continue

            # Parse based on section
            if current_section == 'summary':
                if ',' in line and not line.startswith('Metric'):
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(' ', '_')
                        value = parts[1].strip()
                        stats[key] = value

            elif current_section == 'zones':
                if ',' in line and not line.startswith('zone') and line[0].isalpha():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        zone_name = parts[0].strip()
                        zone_count = parts[1].strip()
                        # Skip if zone_count is not a number
                        if zone_count.isdigit():
                            if 'zones' not in stats:
                                stats['zones'] = []
                            stats['zones'].append((zone_name, zone_count))

            elif current_section == 'violators':
                if ',' in line and not line.startswith('Track_ID'):
                    parts = line.split(',')
                    if len(parts) == 2:
                        track_id = parts[0].strip()
                        count = parts[1].strip()
                        # Only add if both are valid numbers
                        if track_id.isdigit() and count.isdigit():
                            if 'top_violators' not in stats:
                                stats['top_violators'] = []
                            stats['top_violators'].append((track_id, count))

        # Sort zones by count (descending)
        if 'zones' in stats:
            stats['zones'] = sorted(stats['zones'], key=lambda x: int(x[1]), reverse=True)

        return stats


def send_test_message():
    """Send a test message to verify bot setup."""
    print("\n" + "=" * 70)
    print("Telegram Bot Test")
    print("=" * 70)

    try:
        bot = TelegramBot()

        message = (
            "🤖 *PPE-Watch Bot Test*\n\n"
            f"✅ Bot is working!\n"
            f"⏰ Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
            "This bot will send daily compliance reports automatically."
        )

        print("\n📤 Sending test message...")
        response = bot.send_message(message)

        if response.get('ok'):
            print("✅ Test message sent successfully!")
            print(f"📱 Check your Telegram chat!")
        else:
            print(f"❌ Failed to send: {response}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Send PPE report via Telegram')
    parser.add_argument('--date', help='Report date (YYYY-MM-DD)')
    parser.add_argument('--test', action='store_true', help='Send test message')
    parser.add_argument('--reports-dir', default='reports', help='Reports directory')

    args = parser.parse_args()

    try:
        if args.test:
            send_test_message()
        elif args.date:
            bot = TelegramBot()
            success = bot.send_daily_report(args.date, args.reports_dir)
            sys.exit(0 if success else 1)
        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
