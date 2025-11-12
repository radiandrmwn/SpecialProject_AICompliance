#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chart Generation Module

Creates visualizations for daily PPE compliance reports:
- Bar chart: Violations per zone
- Pie chart: Compliance rate
- Timeline: Hourly violation distribution
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10


class ChartGenerator:
    """Generate charts for daily violation reports."""

    def __init__(self, events_dir: str = "./events", reports_dir: str = "./reports"):
        """
        Initialize chart generator.

        Args:
            events_dir: Directory containing event CSV files
            reports_dir: Directory to save charts
        """
        self.events_dir = Path(events_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Color scheme
        self.colors = {
            'violation': '#e74c3c',  # Red
            'compliant': '#2ecc71',  # Green
            'warning': '#f39c12',    # Orange
            'info': '#3498db'        # Blue
        }

    def load_events(self, date_str: str) -> pd.DataFrame:
        """Load events for a specific date."""
        events_file = self.events_dir / f"events_{date_str}.csv"

        if not events_file.exists():
            raise FileNotFoundError(f"No events file found for {date_str}")

        print(f"📂 Loading events from: {events_file}")
        df = pd.read_csv(events_file)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['hour'] = df['datetime'].dt.hour
        print(f"   Loaded {len(df)} events")
        return df

    def create_zone_violations_chart(self, df: pd.DataFrame, ax):
        """Create bar chart of violations per zone."""
        zone_counts = df.groupby('zone').size().sort_values(ascending=False)

        ax.bar(range(len(zone_counts)), zone_counts.values,
               color=self.colors['violation'], alpha=0.8, edgecolor='black')

        ax.set_xlabel('Zone', fontweight='bold')
        ax.set_ylabel('Number of Violations', fontweight='bold')
        ax.set_title('Violations by Zone', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(zone_counts)))
        ax.set_xticklabels(zone_counts.index, rotation=45, ha='right')

        # Add value labels on bars
        for i, v in enumerate(zone_counts.values):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

        ax.grid(axis='y', alpha=0.3)

    def create_hourly_distribution_chart(self, df: pd.DataFrame, ax):
        """Create line chart of violations throughout the day."""
        hourly_counts = df.groupby('hour').size()

        # Ensure all hours 0-23 are represented
        all_hours = pd.Series(0, index=range(24))
        all_hours.update(hourly_counts)

        ax.plot(all_hours.index, all_hours.values,
                marker='o', linewidth=2, markersize=6,
                color=self.colors['violation'], markerfacecolor=self.colors['violation'])

        ax.fill_between(all_hours.index, all_hours.values, alpha=0.3, color=self.colors['violation'])

        ax.set_xlabel('Hour of Day', fontweight='bold')
        ax.set_ylabel('Number of Violations', fontweight='bold')
        ax.set_title('Hourly Violation Distribution', fontsize=14, fontweight='bold')
        ax.set_xticks(range(0, 24, 2))
        ax.set_xlim(-0.5, 23.5)
        ax.grid(True, alpha=0.3)

        # Highlight peak hours
        if all_hours.max() > 0:
            peak_hour = all_hours.idxmax()
            ax.axvline(peak_hour, color=self.colors['warning'], linestyle='--', alpha=0.5)
            ax.text(peak_hour, all_hours.max() * 1.1,
                   f'Peak: {peak_hour}:00', ha='center', fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def create_compliance_pie_chart(self, df: pd.DataFrame, ax):
        """Create summary chart showing violation statistics."""
        # NOTE: We only log violations (persons without helmets), not compliant persons
        # So this chart shows violation distribution, NOT overall compliance rate

        # Count violations
        violations = len(df[~df['has_helmet']])
        total = len(df)

        # For the summary, show unique violators
        unique_violators = df['track_id'].nunique()

        # Since we only track violations, show a simple summary visualization
        # Instead of a misleading pie chart, show key metrics
        ax.axis('off')

        # Display key violation metrics
        metrics_text = [
            f"Total Violation Events: {total}",
            f"Unique Violators: {unique_violators}",
            "",
            "⚠️  NOTE: Only violations (no helmet)",
            "are tracked to reduce data size.",
            "",
            "Compliant persons are detected but",
            "not logged to CSV."
        ]

        y_pos = 0.9
        for line in metrics_text:
            if line.startswith("⚠️"):
                ax.text(0.5, y_pos, line, ha='center', va='top', fontsize=9,
                       fontweight='bold', color=self.colors['warning'],
                       transform=ax.transAxes)
            elif line == "":
                y_pos -= 0.08
                continue
            elif "Total" in line or "Unique" in line:
                ax.text(0.5, y_pos, line, ha='center', va='top', fontsize=13,
                       fontweight='bold', transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))
            else:
                ax.text(0.5, y_pos, line, ha='center', va='top', fontsize=8,
                       style='italic', transform=ax.transAxes)
            y_pos -= 0.12

        ax.set_title('Violation Summary', fontsize=14, fontweight='bold')

    def create_top_violators_chart(self, df: pd.DataFrame, ax):
        """Create bar chart of top violators by track ID."""
        top_violators = df['track_id'].value_counts().head(10)

        ax.barh(range(len(top_violators)), top_violators.values,
                color=self.colors['warning'], alpha=0.8, edgecolor='black')

        ax.set_ylabel('Track ID', fontweight='bold')
        ax.set_xlabel('Number of Violations', fontweight='bold')
        ax.set_title('Top 10 Repeat Violators', fontsize=14, fontweight='bold')
        ax.set_yticks(range(len(top_violators)))
        ax.set_yticklabels([f'Track #{int(tid)}' for tid in top_violators.index])

        # Add value labels
        for i, v in enumerate(top_violators.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')

        ax.grid(axis='x', alpha=0.3)
        ax.invert_yaxis()  # Highest at top

    def generate_charts(self, date_str: str) -> Path:
        """
        Generate all charts for a specific date.

        Args:
            date_str: Date in format YYYY-MM-DD

        Returns:
            Path to saved chart image
        """
        print("=" * 70)
        print(f"Chart Generation - {date_str}")
        print("=" * 70)

        # Load data
        df = self.load_events(date_str)

        print(f"\n📊 Generating charts...")

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 10))

        # Add main title
        fig.suptitle(f'PPE Compliance Report - {date_str}',
                    fontsize=18, fontweight='bold', y=0.98)

        # Create grid spec for better layout
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3,
                             left=0.08, right=0.95, top=0.93, bottom=0.08)

        # 1. Zone violations (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        self.create_zone_violations_chart(df, ax1)

        # 2. Hourly distribution (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        self.create_hourly_distribution_chart(df, ax2)

        # 3. Compliance pie chart (bottom left)
        ax3 = fig.add_subplot(gs[1, 0])
        self.create_compliance_pie_chart(df, ax3)

        # 4. Top violators (bottom right)
        ax4 = fig.add_subplot(gs[1, 1])
        self.create_top_violators_chart(df, ax4)

        # Add footer with metadata
        footer_text = (f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '
                      f'Total Events: {len(df)} | '
                      f'Unique Violators: {df["track_id"].nunique()} | '
                      f'Zones Monitored: {df["zone"].nunique()}')
        fig.text(0.5, 0.02, footer_text, ha='center', fontsize=9, style='italic',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))

        # Save figure
        output_file = self.reports_dir / f"report_{date_str}_charts.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n💾 Charts saved to: {output_file}")

        # Close figure to free memory
        plt.close(fig)

        return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate violation charts')
    parser.add_argument('--date', required=True, help='Date in format YYYY-MM-DD')
    parser.add_argument('--events-dir', default='./events', help='Events directory')
    parser.add_argument('--reports-dir', default='./reports', help='Reports output directory')
    parser.add_argument('--show', action='store_true', help='Display charts (don\'t just save)')

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ Invalid date format: {args.date}")
        print("   Please use YYYY-MM-DD format")
        sys.exit(1)

    # Create generator
    generator = ChartGenerator(
        events_dir=args.events_dir,
        reports_dir=args.reports_dir
    )

    # Generate charts
    try:
        output_file = generator.generate_charts(args.date)

        print("\n" + "=" * 70)
        print("✅ Chart generation complete!")
        print("=" * 70)
        print(f"\n📁 Output file: {output_file}")

        if args.show:
            print("\n👀 Opening chart...")
            import os
            if sys.platform == 'win32':
                os.startfile(output_file)
            else:
                import subprocess
                subprocess.run(['xdg-open', output_file])

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
