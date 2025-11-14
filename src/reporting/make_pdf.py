#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Report Generator for PPE-Watch

Generates professional PDF reports with statistics and visualizations.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
        PageBreak, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("\n❌ Error: reportlab is not installed")
    print("📦 Install with: pip install reportlab")
    sys.exit(1)

import pandas as pd


class PDFReportGenerator:
    """Generate PDF reports for PPE compliance."""

    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize PDF generator.

        Args:
            reports_dir: Directory to save PDF reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Colors
        self.colors = {
            'primary': colors.HexColor('#2C3E50'),
            'secondary': colors.HexColor('#34495E'),
            'success': colors.HexColor('#27AE60'),
            'warning': colors.HexColor('#F39C12'),
            'danger': colors.HexColor('#E74C3C'),
            'info': colors.HexColor('#3498DB'),
            'light_gray': colors.HexColor('#ECF0F1'),
            'dark_gray': colors.HexColor('#7F8C8D')
        }

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=6,
            alignment=TA_LEFT
        ))

        # Footer
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_CENTER
        ))

    def _add_header(self, elements: list, date_str: str):
        """Add report header."""
        # Title
        title = Paragraph(
            f"PPE Compliance Report",
            self.styles['CustomTitle']
        )
        elements.append(title)

        # Date
        date_text = Paragraph(
            f"<b>Report Date:</b> {date_str}",
            self.styles['CustomSubHeading']
        )
        elements.append(date_text)
        elements.append(Spacer(1, 0.2 * inch))

    def _add_summary_section(self, elements: list, stats: Dict):
        """Add summary statistics section."""
        # Section heading
        heading = Paragraph("Executive Summary", self.styles['CustomHeading'])
        elements.append(heading)

        # Summary statistics table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Violation Events', str(stats.get('total_events', 0))],
            ['Unique Violators', str(stats.get('unique_violators', 0))],
            ['Zones Monitored', str(len(stats.get('zone_stats', [])))],
            ['Violations (No Helmet)', str(stats.get('violations_without_helmet', 0))],
        ]

        table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, self.colors['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

    def _add_zone_breakdown(self, elements: list, zone_stats: pd.DataFrame):
        """Add zone-by-zone breakdown."""
        if zone_stats is None or len(zone_stats) == 0:
            return

        heading = Paragraph("Zone Breakdown", self.styles['CustomHeading'])
        elements.append(heading)

        # Prepare table data
        table_data = [['Zone', 'Violations', 'Unique Violators', 'Avg Confidence']]

        for _, row in zone_stats.iterrows():
            table_data.append([
                str(row['zone']),
                str(row['total_violations']),
                str(row['unique_violators']),
                f"{row['avg_confidence']:.2%}"
            ])

        table = Table(table_data, colWidths=[2 * inch, 1.2 * inch, 1.5 * inch, 1.3 * inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['info']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

            # Highlight high violations
            ('BACKGROUND', (0, 1), (-1, 1), self.colors['light_gray']),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, self.colors['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

    def _add_top_violators(self, elements: list, top_violators: Dict):
        """Add top violators section."""
        if not top_violators or len(top_violators) == 0:
            return

        heading = Paragraph("Top Repeat Violators", self.styles['CustomHeading'])
        elements.append(heading)

        # Prepare table data
        table_data = [['Rank', 'Track ID', 'Number of Violations']]

        for rank, (track_id, count) in enumerate(list(top_violators.items())[:5], 1):
            table_data.append([
                str(rank),
                f"Track #{int(track_id)}",
                str(count)
            ])

        table = Table(table_data, colWidths=[1 * inch, 2.5 * inch, 2.5 * inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['warning']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, self.colors['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)

        # Add explanatory note about Track ID limitations
        note_text = (
            "<i><b>Note:</b> Track IDs reset for each video session. "
            "The same Track ID appearing in different videos does NOT represent the same person. "
            "This chart is most useful for continuous CCTV footage, not multiple separate video uploads.</i>"
        )
        note = Paragraph(note_text, self.styles['CustomBody'])
        elements.append(note)

        elements.append(Spacer(1, 0.3 * inch))

    def _add_charts(self, elements: list, charts_path: Path):
        """Add visualization charts."""
        if not charts_path.exists():
            warning = Paragraph(
                "<i>Note: Visualization charts not found. Run charts.py to generate them.</i>",
                self.styles['CustomBody']
            )
            elements.append(warning)
            return

        heading = Paragraph("Visualizations", self.styles['CustomHeading'])
        elements.append(heading)

        # Add charts image
        try:
            img = Image(str(charts_path), width=6.5 * inch, height=4.5 * inch)
            elements.append(img)
        except Exception as e:
            error_text = Paragraph(
                f"<i>Error loading charts: {str(e)}</i>",
                self.styles['CustomBody']
            )
            elements.append(error_text)

        elements.append(Spacer(1, 0.2 * inch))

    def _add_footer(self, elements: list):
        """Add report footer."""
        elements.append(Spacer(1, 0.5 * inch))

        footer_text = f"Generated by PPE-Watch System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, self.styles['Footer'])
        elements.append(footer)

        note = Paragraph(
            "<i>This report is generated automatically. Only violations (no helmet) are logged.</i>",
            self.styles['Footer']
        )
        elements.append(note)

    def generate_report(self, date_str: str, stats: Dict, charts_path: Optional[Path] = None) -> Path:
        """
        Generate PDF report for a specific date.

        Args:
            date_str: Date in format YYYY-MM-DD
            stats: Statistics dictionary from aggregate_day.py
            charts_path: Path to charts PNG file

        Returns:
            Path to generated PDF file
        """
        print(f"\n{'=' * 70}")
        print(f"PDF Report Generation - {date_str}")
        print('=' * 70)

        # Output path
        output_path = self.reports_dir / f"report_{date_str}.pdf"

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )

        # Build content
        elements = []

        # Header
        self._add_header(elements, date_str)

        # Summary section
        self._add_summary_section(elements, stats)

        # Zone breakdown
        if 'zone_stats' in stats and stats['zone_stats'] is not None:
            self._add_zone_breakdown(elements, stats['zone_stats'])

        # Top violators
        if 'top_violators' in stats:
            self._add_top_violators(elements, stats['top_violators'])

        # Charts
        if charts_path:
            self._add_charts(elements, charts_path)

        # Footer
        self._add_footer(elements)

        # Build PDF
        try:
            doc.build(elements)
            print(f"\n✅ PDF report generated successfully!")
            print(f"📁 Saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"\n❌ Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    """Main entry point."""
    import argparse
    from src.reporting.aggregate_day import DailyAggregator

    parser = argparse.ArgumentParser(description='Generate PDF report')
    parser.add_argument('--date', required=True, help='Date in format YYYY-MM-DD')
    parser.add_argument('--events-dir', default='events', help='Events directory')
    parser.add_argument('--reports-dir', default='reports', help='Reports directory')

    args = parser.parse_args()

    try:
        # Load statistics
        print(f"📊 Loading statistics for {args.date}...")
        aggregator = DailyAggregator(events_dir=args.events_dir, reports_dir=args.reports_dir)

        # Load events
        df = aggregator.load_events(args.date)

        # Calculate statistics
        stats = aggregator.calculate_statistics(df)

        # Charts path
        charts_path = Path(args.reports_dir) / f"report_{args.date}_charts.png"

        # Generate PDF
        pdf_generator = PDFReportGenerator(reports_dir=args.reports_dir)
        pdf_path = pdf_generator.generate_report(args.date, stats, charts_path)

        print(f"\n{'=' * 70}")
        print("✅ PDF Report Generation Complete!")
        print('=' * 70)
        print(f"\n📄 PDF File: {pdf_path}")
        print(f"📊 Charts: {charts_path}")
        print(f"\n💡 Tip: You can email or send this PDF via WhatsApp to supervisors!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
