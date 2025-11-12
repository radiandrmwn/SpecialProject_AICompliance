#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Report Automation Script

This script runs daily to:
1. Aggregate yesterday's events
2. Generate charts
3. Generate PDF report
4. Send via Telegram

Designed to be scheduled via Windows Task Scheduler or Cron.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"daily_automation_{date.today().strftime('%Y%m')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_daily_automation(target_date: date = None):
    """
    Run daily report automation.

    Args:
        target_date: Date to process (default: yesterday)
    """
    # Use yesterday by default
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    date_str = target_date.strftime('%Y-%m-%d')

    logger.info("=" * 70)
    logger.info("PPE-Watch Daily Automation")
    logger.info("=" * 70)
    logger.info(f"Target Date: {date_str}")
    logger.info(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Check if events file exists
    events_file = Path("events") / f"events_{date_str}.csv"
    if not events_file.exists():
        logger.warning(f"No events file found for {date_str}")
        logger.warning(f"Expected: {events_file}")
        logger.info("Skipping automation - no data to process")
        return False

    logger.info(f"✅ Events file found: {events_file}")
    logger.info("")

    success = True

    # Step 1: Generate Charts
    logger.info("📊 Step 1: Generating Charts...")
    try:
        from src.reporting.charts import ChartGenerator

        chart_gen = ChartGenerator()
        chart_path = chart_gen.generate_charts(date_str)

        if chart_path and chart_path.exists():
            logger.info(f"   ✅ Charts generated: {chart_path}")
        else:
            logger.error("   ❌ Charts generation failed")
            success = False

    except Exception as e:
        logger.error(f"   ❌ Error generating charts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        success = False

    logger.info("")

    # Step 2: Generate PDF Report
    logger.info("📄 Step 2: Generating PDF Report...")
    try:
        from src.reporting.aggregate_day import DailyAggregator
        from src.reporting.make_pdf import PDFReportGenerator

        # Load events and calculate stats
        aggregator = DailyAggregator()
        df = aggregator.load_events(date_str)
        stats = aggregator.calculate_statistics(df)

        # Generate PDF
        pdf_gen = PDFReportGenerator()
        charts_path = Path("reports") / f"report_{date_str}_charts.png"
        pdf_path = pdf_gen.generate_report(date_str, stats, charts_path)

        if pdf_path and pdf_path.exists():
            logger.info(f"   ✅ PDF generated: {pdf_path}")
        else:
            logger.error("   ❌ PDF generation failed")
            success = False

    except Exception as e:
        logger.error(f"   ❌ Error generating PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        success = False

    logger.info("")

    # Step 3: Send via Telegram
    logger.info("📱 Step 3: Sending Report via Telegram...")
    try:
        from src.delivery.telegram_bot import TelegramBot

        bot = TelegramBot()
        telegram_success = bot.send_daily_report(date_str)

        if telegram_success:
            logger.info("   ✅ Report sent via Telegram")
        else:
            logger.error("   ❌ Failed to send via Telegram")
            success = False

    except Exception as e:
        logger.error(f"   ❌ Error sending Telegram: {e}")
        import traceback
        logger.error(traceback.format_exc())
        success = False

    logger.info("")
    logger.info("=" * 70)

    if success:
        logger.info("✅ Daily Automation Completed Successfully!")
    else:
        logger.error("⚠️ Daily Automation Completed with Errors")

    logger.info("=" * 70)
    logger.info("")

    return success


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Run daily report automation')
    parser.add_argument(
        '--date',
        help='Date to process (YYYY-MM-DD). Default: yesterday'
    )
    parser.add_argument(
        '--today',
        action='store_true',
        help='Process today instead of yesterday'
    )

    args = parser.parse_args()

    # Determine target date
    if args.today:
        target_date = date.today()
    elif args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}")
            logger.error("Use YYYY-MM-DD format")
            sys.exit(1)
    else:
        target_date = None  # Will default to yesterday

    # Run automation
    try:
        success = run_daily_automation(target_date)
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
