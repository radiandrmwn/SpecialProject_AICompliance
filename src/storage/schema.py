"""
Data schemas for event logging and storage.
"""

from typing import TypedDict, Optional
from datetime import datetime


# CSV column definitions
EVENT_COLUMNS = [
    "timestamp",
    "camera_id",
    "track_id",
    "zone",
    "has_helmet",
    "frame_idx",
    "confidence",
    "person_bbox",
]


class EventRecord(TypedDict):
    """
    Event record structure for logging detections and violations.

    Fields:
        timestamp: Unix epoch timestamp (seconds.milliseconds)
        camera_id: Identifier for camera/video source
        track_id: Unique track ID from tracker
        zone: Zone name where person is detected (empty string if outside zones)
        has_helmet: Boolean indicating if helmet was detected
        frame_idx: Frame number in video
        confidence: Detection confidence score (0-1)
        person_bbox: Person bounding box as "x1,y1,x2,y2" string
    """
    timestamp: float
    camera_id: str
    track_id: int
    zone: str
    has_helmet: bool
    frame_idx: int
    confidence: float
    person_bbox: str


class ViolationSummary(TypedDict):
    """
    Daily violation summary structure.

    Fields:
        date: Date string (YYYY-MM-DD)
        camera_id: Camera identifier
        zone: Zone name
        total_persons: Unique persons (tracks) detected
        with_helmet: Count of persons with helmets
        without_helmet: Count of violations
        violation_rate: Percentage of violations
        first_violation_time: Timestamp of first violation
        last_violation_time: Timestamp of last violation
    """
    date: str
    camera_id: str
    zone: str
    total_persons: int
    with_helmet: int
    without_helmet: int
    violation_rate: float
    first_violation_time: Optional[float]
    last_violation_time: Optional[float]


def create_event_record(
    timestamp: float,
    camera_id: str,
    track_id: int,
    zone: str,
    has_helmet: bool,
    frame_idx: int,
    confidence: float,
    person_bbox: tuple
) -> EventRecord:
    """
    Create an event record with validation.

    Args:
        timestamp: Unix epoch timestamp
        camera_id: Camera identifier
        track_id: Track ID from tracker
        zone: Zone name (can be empty string)
        has_helmet: Whether helmet was detected
        frame_idx: Frame index
        confidence: Detection confidence (0-1)
        person_bbox: Tuple of (x1, y1, x2, y2)

    Returns:
        EventRecord dictionary

    Examples:
        >>> record = create_event_record(
        ...     timestamp=1730448000.123,
        ...     camera_id='cam_1',
        ...     track_id=42,
        ...     zone='CraneBay',
        ...     has_helmet=False,
        ...     frame_idx=671,
        ...     confidence=0.85,
        ...     person_bbox=(100, 200, 300, 600)
        ... )
        >>> record['zone']
        'CraneBay'
        >>> record['has_helmet']
        False
    """
    x1, y1, x2, y2 = person_bbox
    bbox_str = f"{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}"

    return EventRecord(
        timestamp=timestamp,
        camera_id=camera_id,
        track_id=track_id,
        zone=zone if zone else "",
        has_helmet=has_helmet,
        frame_idx=frame_idx,
        confidence=confidence,
        person_bbox=bbox_str
    )


def format_timestamp(ts: float) -> str:
    """
    Format Unix timestamp to human-readable string.

    Args:
        ts: Unix epoch timestamp

    Returns:
        Formatted timestamp string

    Examples:
        >>> format_timestamp(1730448000.123)
        '2024-11-01 06:00:00.123'
    """
    dt = datetime.fromtimestamp(ts)
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Keep milliseconds


def parse_bbox_string(bbox_str: str) -> tuple:
    """
    Parse bbox string back to tuple.

    Args:
        bbox_str: Bbox string in format "x1,y1,x2,y2"

    Returns:
        Tuple of (x1, y1, x2, y2)

    Examples:
        >>> parse_bbox_string("100.0,200.0,300.0,600.0")
        (100.0, 200.0, 300.0, 600.0)
    """
    parts = bbox_str.split(',')
    return tuple(float(p) for p in parts)
