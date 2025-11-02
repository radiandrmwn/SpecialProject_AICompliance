"""
Unit tests for zoning utilities.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from inference.zoning import (
    bbox_centroid,
    head_region,
    bbox_iou,
    point_in_polygons,
    bbox_area,
    is_valid_bbox
)


class TestBboxCentroid:
    """Test bbox_centroid function."""

    def test_square_bbox(self):
        """Test centroid of square bbox."""
        assert bbox_centroid((0, 0, 100, 100)) == (50.0, 50.0)

    def test_rectangle_bbox(self):
        """Test centroid of rectangular bbox."""
        assert bbox_centroid((10, 20, 30, 40)) == (20.0, 30.0)

    def test_offset_bbox(self):
        """Test centroid with offset coordinates."""
        assert bbox_centroid((100, 200, 300, 400)) == (200.0, 300.0)


class TestHeadRegion:
    """Test head_region function."""

    def test_default_ratio(self):
        """Test with default top_ratio of 0.35."""
        result = head_region((0, 0, 100, 100))
        assert result == (0, 0, 100, 35)

    def test_custom_ratio(self):
        """Test with custom top_ratio."""
        result = head_region((0, 0, 100, 100), top_ratio=0.5)
        assert result == (0, 0, 100, 50)

    def test_tall_person(self):
        """Test with tall person bbox."""
        result = head_region((10, 20, 50, 120), top_ratio=0.35)
        # Height = 100, top 35% = 35
        assert result == (10, 20, 50, 55)

    def test_offset_bbox(self):
        """Test with offset coordinates."""
        result = head_region((100, 200, 200, 600), top_ratio=0.3)
        # Height = 400, top 30% = 120
        assert result == (100, 200, 200, 320)


class TestBboxIoU:
    """Test bbox_iou function."""

    def test_identical_boxes(self):
        """Test IoU of identical boxes."""
        box = (0, 0, 10, 10)
        assert bbox_iou(box, box) == 1.0

    def test_no_overlap(self):
        """Test IoU of non-overlapping boxes."""
        box_a = (0, 0, 10, 10)
        box_b = (20, 20, 30, 30)
        assert bbox_iou(box_a, box_b) == 0.0

    def test_partial_overlap(self):
        """Test IoU of partially overlapping boxes."""
        box_a = (0, 0, 10, 10)
        box_b = (5, 5, 15, 15)
        # Intersection: 5x5 = 25
        # Union: 100 + 100 - 25 = 175
        # IoU: 25/175 ≈ 0.1429
        iou = bbox_iou(box_a, box_b)
        assert 0.14 < iou < 0.15

    def test_contained_box(self):
        """Test IoU when one box contains another."""
        box_a = (0, 0, 20, 20)
        box_b = (5, 5, 15, 15)
        # Intersection: 10x10 = 100
        # Union: 400 + 100 - 100 = 400
        # IoU: 100/400 = 0.25
        iou = bbox_iou(box_a, box_b)
        assert iou == 0.25

    def test_edge_touching(self):
        """Test IoU when boxes touch at edge (no overlap)."""
        box_a = (0, 0, 10, 10)
        box_b = (10, 0, 20, 10)
        assert bbox_iou(box_a, box_b) == 0.0


class TestPointInPolygons:
    """Test point_in_polygons function."""

    def test_point_inside_square(self):
        """Test point inside a square polygon."""
        polygons = [{'name': 'Zone1', 'points': [[0, 0], [100, 0], [100, 100], [0, 100]]}]
        is_inside, zone = point_in_polygons((50, 50), polygons)
        assert is_inside is True
        assert zone == 'Zone1'

    def test_point_outside_square(self):
        """Test point outside polygon."""
        polygons = [{'name': 'Zone1', 'points': [[0, 0], [100, 0], [100, 100], [0, 100]]}]
        is_inside, zone = point_in_polygons((150, 150), polygons)
        assert is_inside is False
        assert zone == ""

    def test_point_on_edge(self):
        """Test point on polygon edge."""
        polygons = [{'name': 'Zone1', 'points': [[0, 0], [100, 0], [100, 100], [0, 100]]}]
        # Point on edge at (50, 0)
        is_inside, zone = point_in_polygons((50, 0), polygons)
        # Shapely considers boundary as inside
        assert is_inside is True
        assert zone == 'Zone1'

    def test_multiple_polygons_first_match(self):
        """Test with multiple polygons, point in first."""
        polygons = [
            {'name': 'Zone1', 'points': [[0, 0], [100, 0], [100, 100], [0, 100]]},
            {'name': 'Zone2', 'points': [[200, 200], [300, 200], [300, 300], [200, 300]]}
        ]
        is_inside, zone = point_in_polygons((50, 50), polygons)
        assert is_inside is True
        assert zone == 'Zone1'

    def test_multiple_polygons_second_match(self):
        """Test with multiple polygons, point in second."""
        polygons = [
            {'name': 'Zone1', 'points': [[0, 0], [100, 0], [100, 100], [0, 100]]},
            {'name': 'Zone2', 'points': [[200, 200], [300, 200], [300, 300], [200, 300]]}
        ]
        is_inside, zone = point_in_polygons((250, 250), polygons)
        assert is_inside is True
        assert zone == 'Zone2'

    def test_irregular_polygon(self):
        """Test with irregular polygon shape."""
        polygons = [{'name': 'IrregularZone', 'points': [[0, 0], [100, 50], [50, 100], [0, 50]]}]
        is_inside, zone = point_in_polygons((40, 40), polygons)
        assert is_inside is True
        assert zone == 'IrregularZone'


class TestBboxArea:
    """Test bbox_area function."""

    def test_square(self):
        """Test area of square."""
        assert bbox_area((0, 0, 10, 10)) == 100.0

    def test_rectangle(self):
        """Test area of rectangle."""
        assert bbox_area((0, 0, 20, 10)) == 200.0

    def test_zero_area(self):
        """Test zero-area bbox."""
        assert bbox_area((0, 0, 0, 0)) == 0.0

    def test_negative_coords(self):
        """Test with negative coordinates (invalid)."""
        # Should still calculate area correctly
        assert bbox_area((10, 10, 5, 5)) == 0.0


class TestIsValidBbox:
    """Test is_valid_bbox function."""

    def test_valid_bbox(self):
        """Test valid bbox."""
        assert is_valid_bbox((0, 0, 10, 10)) is True

    def test_zero_area(self):
        """Test zero-area bbox (invalid)."""
        assert is_valid_bbox((0, 0, 0, 0)) is False

    def test_inverted_coords(self):
        """Test inverted coordinates (invalid)."""
        assert is_valid_bbox((10, 10, 5, 5)) is False

    def test_min_area_threshold(self):
        """Test minimum area threshold."""
        # 2x2 bbox, area = 4
        assert is_valid_bbox((0, 0, 2, 2), min_area=1.0) is True
        assert is_valid_bbox((0, 0, 2, 2), min_area=10.0) is False

    def test_single_pixel(self):
        """Test single pixel bbox."""
        assert is_valid_bbox((0, 0, 1, 1), min_area=1.0) is True
        assert is_valid_bbox((0, 0, 1, 1), min_area=2.0) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
