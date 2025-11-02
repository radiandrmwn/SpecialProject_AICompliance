"""
Zoning utilities for point-in-polygon checks and bbox operations.
"""

from typing import Tuple, List, Optional
from shapely.geometry import Point, Polygon


def bbox_centroid(xyxy: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """
    Calculate centroid (center point) of a bounding box.

    Args:
        xyxy: Bounding box coordinates (x1, y1, x2, y2)

    Returns:
        Tuple of (cx, cy) centroid coordinates

    Examples:
        >>> bbox_centroid((0, 0, 100, 100))
        (50.0, 50.0)
        >>> bbox_centroid((10, 20, 30, 40))
        (20.0, 30.0)
    """
    x1, y1, x2, y2 = xyxy
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def head_region(
    xyxy: Tuple[float, float, float, float],
    top_ratio: float = 0.35
) -> Tuple[float, float, float, float]:
    """
    Extract the head region (top portion) of a person bounding box.

    Args:
        xyxy: Person bounding box coordinates (x1, y1, x2, y2)
        top_ratio: Fraction of the bbox height to consider as head region (default: 0.35)

    Returns:
        Head region bounding box (x1, y1, x2, y2_head)

    Examples:
        >>> head_region((0, 0, 100, 100), 0.35)
        (0, 0, 100, 35)
        >>> head_region((10, 20, 50, 120), 0.35)
        (10, 20, 50, 55)
    """
    x1, y1, x2, y2 = xyxy
    height = y2 - y1
    head_bottom = y1 + int(height * top_ratio)
    return (x1, y1, x2, head_bottom)


def bbox_iou(
    box_a: Tuple[float, float, float, float],
    box_b: Tuple[float, float, float, float]
) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.

    Args:
        box_a: First bounding box (x1, y1, x2, y2)
        box_b: Second bounding box (x1, y1, x2, y2)

    Returns:
        IoU value between 0 and 1

    Examples:
        >>> bbox_iou((0, 0, 10, 10), (5, 5, 15, 15))
        0.14285714285714285
        >>> bbox_iou((0, 0, 10, 10), (0, 0, 10, 10))
        1.0
        >>> bbox_iou((0, 0, 10, 10), (20, 20, 30, 30))
        0.0
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    # Calculate intersection
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    # Calculate union
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union_area = area_a + area_b - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


def point_in_polygons(
    point: Tuple[float, float],
    polygons: List[dict]
) -> Tuple[bool, str]:
    """
    Check if a point is inside any of the given polygons.

    Args:
        point: Point coordinates (x, y)
        polygons: List of polygon dicts with 'name' and 'points' keys
                  Example: [{'name': 'CraneBay', 'points': [[x1,y1], [x2,y2], ...]}]

    Returns:
        Tuple of (is_inside: bool, zone_name: str)
        If point is inside a polygon, returns (True, zone_name)
        If point is outside all polygons, returns (False, "")

    Examples:
        >>> polys = [{'name': 'Zone1', 'points': [[0,0], [100,0], [100,100], [0,100]]}]
        >>> point_in_polygons((50, 50), polys)
        (True, 'Zone1')
        >>> point_in_polygons((150, 150), polys)
        (False, '')
    """
    pt = Point(*point)

    for poly_dict in polygons:
        try:
            polygon = Polygon(poly_dict['points'])
            if polygon.is_valid and polygon.contains(pt):
                return True, poly_dict.get('name', 'unknown')
        except Exception as e:
            # Log error but continue checking other polygons
            print(f"Warning: Invalid polygon {poly_dict.get('name', 'unknown')}: {e}")
            continue

    return False, ""


def bbox_area(xyxy: Tuple[float, float, float, float]) -> float:
    """
    Calculate the area of a bounding box.

    Args:
        xyxy: Bounding box coordinates (x1, y1, x2, y2)

    Returns:
        Area of the bounding box

    Examples:
        >>> bbox_area((0, 0, 10, 10))
        100.0
        >>> bbox_area((0, 0, 0, 0))
        0.0
    """
    x1, y1, x2, y2 = xyxy
    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    return width * height


def is_valid_bbox(xyxy: Tuple[float, float, float, float], min_area: float = 1.0) -> bool:
    """
    Check if a bounding box is valid (non-zero area and proper format).

    Args:
        xyxy: Bounding box coordinates (x1, y1, x2, y2)
        min_area: Minimum area threshold (default: 1.0)

    Returns:
        True if bbox is valid, False otherwise

    Examples:
        >>> is_valid_bbox((0, 0, 10, 10))
        True
        >>> is_valid_bbox((0, 0, 0, 0))
        False
        >>> is_valid_bbox((10, 10, 5, 5))
        False
    """
    x1, y1, x2, y2 = xyxy

    # Check if coordinates are in correct order
    if x2 <= x1 or y2 <= y1:
        return False

    # Check if area meets minimum threshold
    area = bbox_area(xyxy)
    return area >= min_area
