#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Aggregation Module

Reads event CSV logs and generates daily statistics:
- Total violations per zone
- Unique violators (track IDs)
- Hourly violation distribution
- Compliance rates
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class DailyAggregator:
    """Aggregate daily violation statistics from event logs."""

    def __init__(self, events_dir: str = "./events", reports_dir: str = "./reports"):
        """
        Initialize aggregator.

        Args:
            events_dir: Directory containing event CSV files
            reports_dir: Directory to save reports
        """
        self.events_dir = Path(events_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def get_events_file(self, date_str: str) -> Path:
        """Get events file path for a specific date."""
        return self.events_dir / f"events_{date_str}.csv"

    def load_events(self, date_str: str) -> pd.DataFrame:
        """
        Load events for a specific date.

        Args:
            date_str: Date in format YYYY-MM-DD

        Returns:
            DataFrame with events
        """
        events_file = self.get_events_file(date_str)

        if not events_file.exists():
            raise FileNotFoundError(f"No events file found for {date_str}: {events_file}")

        print(f"📂 Loading events from: {events_file}")
        df = pd.read_csv(events_file)

        print(f"   Found {len(df)} event records")
        return df

    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive statistics from events.

        Args:
            df: DataFrame with events

        Returns:
            Dictionary with statistics
        """
        print("\n📊 Calculating statistics...")

        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['hour'] = df['datetime'].dt.hour

        # Overall statistics
        total_events = len(df)
        unique_violators = df['track_id'].nunique()
        violations_without_helmet = (~df['has_helmet']).sum()

        # Zone statistics
        zone_stats = []
        for zone in df['zone'].unique():
            zone_df = df[df['zone'] == zone]
            zone_stats.append({
                'zone': zone,
                'total_violations': len(zone_df),
                'unique_violators': zone_df['track_id'].nunique(),
                'avg_confidence': zone_df['confidence'].mean(),
                'first_violation': zone_df['datetime'].min(),
                'last_violation': zone_df['datetime'].max()
            })

        zone_stats_df = pd.DataFrame(zone_stats)

        # Hourly distribution
        hourly_violations = df.groupby('hour').size().to_dict()

        # Top violators (tracks with most violations)
        top_violators = df['track_id'].value_counts().head(10).to_dict()

        stats = {
            'date': df['datetime'].dt.date.iloc[0],
            'total_events': total_events,
            'unique_violators': unique_violators,
            'violations_without_helmet': violations_without_helmet,
            'zone_stats': zone_stats_df,
            'hourly_violations': hourly_violations,
            'top_violators': top_violators,
            'events_df': df
        }

        # Print summary
        print(f"\n📈 Summary Statistics:")
        print(f"   Date: {stats['date']}")
        print(f"   Total Events: {total_events}")
        print(f"   Unique Violators: {unique_violators}")
        print(f"   Violations (no helmet): {violations_without_helmet}")
        print(f"\n🗺️  Zone Breakdown:")
        for _, row in zone_stats_df.iterrows():
            print(f"   {row['zone']}: {row['total_violations']} violations ({row['unique_violators']} unique)")

        return stats

    def save_summary_csv(self, stats: Dict, date_str: str):
        """
        Save summary statistics to CSV.

        Args:
            stats: Statistics dictionary
            date_str: Date string
        """
        output_file = self.reports_dir / f"report_{date_str}.csv"

        print(f"\n💾 Saving summary to: {output_file}")

        # Create summary rows
        summary_data = {
            'Metric': [
                'Date',
                'Total Events',
                'Unique Violators',
                'Violations Without Helmet'
            ],
            'Value': [
                str(stats['date']),
                stats['total_events'],
                stats['unique_violators'],
                stats['violations_without_helmet']
            ]
        }

        summary_df = pd.DataFrame(summary_data)

        # Write summary section
        with open(output_file, 'w') as f:
            f.write("=== DAILY SUMMARY ===\n")
            summary_df.to_csv(f, index=False)

            f.write("\n=== ZONE STATISTICS ===\n")
            stats['zone_stats'].to_csv(f, index=False)

            f.write("\n=== HOURLY DISTRIBUTION ===\n")
            hourly_df = pd.DataFrame(list(stats['hourly_violations'].items()),
                                    columns=['Hour', 'Violations'])
            hourly_df = hourly_df.sort_values('Hour')
            hourly_df.to_csv(f, index=False)

            f.write("\n=== TOP VIOLATORS ===\n")
            violators_df = pd.DataFrame(list(stats['top_violators'].items()),
                                       columns=['Track_ID', 'Violation_Count'])
            violators_df.to_csv(f, index=False)

        print(f"   ✅ Summary saved!")
        return output_file

    def generate_report(self, date_str: str) -> Dict:
        """
        Generate complete daily report.

        Args:
            date_str: Date in format YYYY-MM-DD

        Returns:
            Statistics dictionary
        """
        print("=" * 70)
        print(f"Daily Report Generation - {date_str}")
        print("=" * 70)

        # Load events
        df = self.load_events(date_str)

        # Calculate statistics
        stats = self.calculate_statistics(df)

        # Save summary CSV
        self.save_summary_csv(stats, date_str)

        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate daily PPE compliance report')
    parser.add_argument('--date', required=True, help='Date in format YYYY-MM-DD')
    parser.add_argument('--events-dir', default='./events', help='Events directory')
    parser.add_argument('--reports-dir', default='./reports', help='Reports output directory')

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ Invalid date format: {args.date}")
        print("   Please use YYYY-MM-DD format (e.g., 2025-11-02)")
        sys.exit(1)

    # Create aggregator
    aggregator = DailyAggregator(
        events_dir=args.events_dir,
        reports_dir=args.reports_dir
    )

    # Generate report
    try:
        stats = aggregator.generate_report(args.date)

        print("\n" + "=" * 70)
        print("✅ Report generation complete!")
        print("=" * 70)
        print(f"\n📁 Output files:")
        print(f"   CSV: {aggregator.reports_dir}/report_{args.date}.csv")
        print("\n💡 Next steps:")
        print(f"   1. Generate charts: python -m src.reporting.charts --date {args.date}")
        print(f"   2. Create PDF report: python -m src.reporting.make_pdf --date {args.date}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Available event files:")
        events_dir = Path(args.events_dir)
        if events_dir.exists():
            event_files = list(events_dir.glob('events_*.csv'))
            if event_files:
                for f in event_files:
                    print(f"   - {f.name}")
            else:
                print("   (none found)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
