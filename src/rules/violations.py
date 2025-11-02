"""
Violation detection logic for PPE compliance.

Determines if a person is violating helmet requirements based on:
1. Person location (inside mandatory helmet zone)
2. Helmet detection (overlapping with person's head region)
"""

from typing import List, Tuple, Optional
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.zoning import (
    bbox_centroid,
    head_region,
    bbox_iou,
    point_in_polygons,
    is_valid_bbox
)


def is_violation(
    person_xyxy: Tuple[float, float, float, float],
    helmet_boxes: List[Tuple[float, float, float, float]],
    zone_polygons: List[dict],
    head_iou_thresh: float = 0.05,
    head_ratio: float = 0.35
) -> Tuple[bool, str]:
    """
    Determine if a person is violating helmet safety requirements.

    A violation occurs when:
    1. The person's centroid is inside a mandatory helmet zone, AND
    2. No helmet bounding box overlaps with the person's head region above threshold

    Args:
        person_xyxy: Person bounding box (x1, y1, x2, y2)
        helmet_boxes: List of helmet bounding boxes [(x1, y1, x2, y2), ...]
        zone_polygons: List of zone polygon dicts with 'name', 'points', and optionally 'mandatory_helmet'
        head_iou_thresh: Minimum IoU between helmet and head region to consider helmet detected (default: 0.05)
        head_ratio: Ratio of person bbox height to consider as head region (default: 0.35)

    Returns:
        Tuple of (is_violation: bool, zone_name: str)
        - If violation detected: (True, zone_name)
        - If no violation: (False, zone_name or "")

    Examples:
        >>> person = (100, 100, 200, 400)
        >>> helmets = [(120, 100, 180, 150)]
        >>> zones = [{'name': 'CraneBay', 'points': [[0,0], [300,0], [300,500], [0,500]], 'mandatory_helmet': True}]
        >>> is_violation(person, helmets, zones)
        (False, 'CraneBay')  # Helmet detected, no violation

        >>> is_violation(person, [], zones)
        (True, 'CraneBay')  # No helmet, inside zone -> violation
    """
    # Validate person bbox
    if not is_valid_bbox(person_xyxy):
        return False, ""

    # Check if person is inside any mandatory helmet zone
    centroid = bbox_centroid(person_xyxy)
    inside_zone, zone_name = point_in_polygons(centroid, zone_polygons)

    if not inside_zone:
        # Person not in any zone, no violation
        return False, ""

    # Check if this zone requires helmets
    zone_dict = next((z for z in zone_polygons if z.get('name') == zone_name), None)
    if zone_dict and not zone_dict.get('mandatory_helmet', True):
        # Zone doesn't require helmets
        return False, zone_name

    # Person is in mandatory helmet zone, check if helmet is detected
    head_bbox = head_region(person_xyxy, top_ratio=head_ratio)

    # Check if any helmet overlaps with head region
    helmet_detected = False
    for helmet_bbox in helmet_boxes:
        if not is_valid_bbox(helmet_bbox):
            continue

        iou = bbox_iou(helmet_bbox, head_bbox)
        if iou > head_iou_thresh:
            helmet_detected = True
            break

    # Violation if inside zone but no helmet detected
    is_violating = not helmet_detected
    return is_violating, zone_name


def batch_violations(
    person_boxes: List[Tuple[float, float, float, float]],
    helmet_boxes: List[Tuple[float, float, float, float]],
    zone_polygons: List[dict],
    head_iou_thresh: float = 0.05,
    head_ratio: float = 0.35
) -> List[Tuple[int, bool, str]]:
    """
    Check violations for multiple persons.

    Args:
        person_boxes: List of person bounding boxes
        helmet_boxes: List of helmet bounding boxes
        zone_polygons: List of zone polygon dicts
        head_iou_thresh: Minimum IoU threshold for helmet detection
        head_ratio: Head region ratio

    Returns:
        List of tuples: [(person_idx, is_violation, zone_name), ...]

    Examples:
        >>> persons = [(100, 100, 200, 400), (300, 100, 400, 400)]
        >>> helmets = [(120, 100, 180, 150)]
        >>> zones = [{'name': 'Zone1', 'points': [[0,0], [500,0], [500,500], [0,500]], 'mandatory_helmet': True}]
        >>> batch_violations(persons, helmets, zones)
        [(0, False, 'Zone1'), (1, True, 'Zone1')]
    """
    results = []

    for idx, person_bbox in enumerate(person_boxes):
        is_viol, zone = is_violation(
            person_bbox,
            helmet_boxes,
            zone_polygons,
            head_iou_thresh,
            head_ratio
        )
        results.append((idx, is_viol, zone))

    return results


def get_violation_summary(violations: List[Tuple[int, bool, str]]) -> dict:
    """
    Summarize violation results.

    Args:
        violations: List of (person_idx, is_violation, zone_name) tuples

    Returns:
        Dictionary with summary statistics

    Examples:
        >>> violations = [(0, False, 'Zone1'), (1, True, 'Zone1'), (2, True, 'Zone2')]
        >>> summary = get_violation_summary(violations)
        >>> summary['total_persons']
        3
        >>> summary['total_violations']
        2
    """
    total_persons = len(violations)
    total_violations = sum(1 for _, is_viol, _ in violations if is_viol)
    total_compliant = total_persons - total_violations

    # Violations per zone
    zone_violations = {}
    for _, is_viol, zone in violations:
        if zone:
            if zone not in zone_violations:
                zone_violations[zone] = {'violations': 0, 'compliant': 0, 'total': 0}
            zone_violations[zone]['total'] += 1
            if is_viol:
                zone_violations[zone]['violations'] += 1
            else:
                zone_violations[zone]['compliant'] += 1

    return {
        'total_persons': total_persons,
        'total_violations': total_violations,
        'total_compliant': total_compliant,
        'violation_rate': (total_violations / total_persons * 100) if total_persons > 0 else 0.0,
        'zones': zone_violations
    }
