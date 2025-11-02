"""
Event writer for persisting detection and violation events to CSV files.
"""

import os
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional
from .schema import EVENT_COLUMNS, EventRecord


class EventsWriter:
    """
    Writes event records to daily CSV files.

    Each day gets its own CSV file: events_YYYY-MM-DD.csv
    Files are stored in the configured output directory.
    """

    def __init__(self, out_dir: str = "./events"):
        """
        Initialize events writer.

        Args:
            out_dir: Directory where event CSV files will be stored
        """
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Cache for open file handles (day -> file handle)
        self._file_handles = {}
        self._csv_writers = {}

    def _path_for_day(self, day: str) -> Path:
        """
        Get file path for a specific day.

        Args:
            day: Date string in format YYYY-MM-DD

        Returns:
            Path to CSV file for that day

        Examples:
            >>> writer = EventsWriter("./events")
            >>> writer._path_for_day("2025-11-01")
            PosixPath('events/events_2025-11-01.csv')
        """
        return self.out_dir / f"events_{day}.csv"

    def _get_day_from_timestamp(self, timestamp: float) -> str:
        """
        Extract date string from timestamp.

        Args:
            timestamp: Unix epoch timestamp

        Returns:
            Date string in format YYYY-MM-DD

        Examples:
            >>> writer = EventsWriter()
            >>> writer._get_day_from_timestamp(1730448000.123)
            '2024-11-01'
        """
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d")

    def append(self, record: EventRecord) -> None:
        """
        Append an event record to the appropriate daily CSV file.

        Creates file with header if it doesn't exist.
        Flushes after each write to ensure data persistence.

        Args:
            record: Event record dictionary

        Examples:
            >>> writer = EventsWriter("./events")
            >>> record = {
            ...     'timestamp': 1730448000.123,
            ...     'camera_id': 'cam_1',
            ...     'track_id': 42,
            ...     'zone': 'CraneBay',
            ...     'has_helmet': False,
            ...     'frame_idx': 671,
            ...     'confidence': 0.85,
            ...     'person_bbox': '100,200,300,600'
            ... }
            >>> writer.append(record)
        """
        day = self._get_day_from_timestamp(record["timestamp"])
        file_path = self._path_for_day(day)

        # Check if file exists to determine if we need header
        write_header = not file_path.exists()

        # Open file in append mode
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EVENT_COLUMNS)

            if write_header:
                writer.writeheader()

            writer.writerow(record)

        # Note: We're not caching file handles anymore for thread safety
        # and to ensure immediate flushing

    def append_batch(self, records: list[EventRecord]) -> None:
        """
        Append multiple event records efficiently.

        Groups records by day and writes them in batches.

        Args:
            records: List of event record dictionaries

        Examples:
            >>> writer = EventsWriter("./events")
            >>> records = [
            ...     {'timestamp': 1730448000.0, 'camera_id': 'cam_1', ...},
            ...     {'timestamp': 1730448001.0, 'camera_id': 'cam_1', ...},
            ... ]
            >>> writer.append_batch(records)
        """
        if not records:
            return

        # Group records by day
        records_by_day = {}
        for record in records:
            day = self._get_day_from_timestamp(record["timestamp"])
            if day not in records_by_day:
                records_by_day[day] = []
            records_by_day[day].append(record)

        # Write each day's records
        for day, day_records in records_by_day.items():
            file_path = self._path_for_day(day)
            write_header = not file_path.exists()

            with open(file_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=EVENT_COLUMNS)

                if write_header:
                    writer.writeheader()

                writer.writerows(day_records)

    def get_file_path(self, date_str: Optional[str] = None) -> Path:
        """
        Get the file path for a specific date or today.

        Args:
            date_str: Date string YYYY-MM-DD (default: today)

        Returns:
            Path to CSV file

        Examples:
            >>> writer = EventsWriter("./events")
            >>> path = writer.get_file_path("2025-11-01")
            >>> str(path)
            'events/events_2025-11-01.csv'
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return self._path_for_day(date_str)

    def file_exists(self, date_str: Optional[str] = None) -> bool:
        """
        Check if events file exists for a date.

        Args:
            date_str: Date string YYYY-MM-DD (default: today)

        Returns:
            True if file exists, False otherwise

        Examples:
            >>> writer = EventsWriter("./events")
            >>> writer.file_exists("2025-11-01")
            False
        """
        return self.get_file_path(date_str).exists()

    def close(self) -> None:
        """
        Close any cached file handles.

        Call this when shutting down to ensure all data is flushed.
        """
        for fh in self._file_handles.values():
            if fh and not fh.closed:
                fh.close()

        self._file_handles.clear()
        self._csv_writers.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures files are closed."""
        self.close()
        return False
