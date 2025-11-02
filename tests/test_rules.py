"""
Unit tests for violation detection rules.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rules.violations import (
    is_violation,
    batch_violations,
    get_violation_summary
)


class TestIsViolation:
    """Test is_violation function."""

    @pytest.fixture
    def simple_zone(self):
        """Simple rectangular zone."""
        return [{'name': 'TestZone', 'points': [[0, 0], [300, 0], [300, 500], [0, 500]], 'mandatory_helmet': True}]

    def test_person_with_helmet_in_zone(self, simple_zone):
        """Person with helmet in zone - no violation."""
        person = (100, 100, 200, 400)  # Person bbox
        helmets = [(120, 100, 180, 150)]  # Helmet overlapping head
        is_viol, zone = is_violation(person, helmets, simple_zone)
        assert is_viol is False
        assert zone == 'TestZone'

    def test_person_without_helmet_in_zone(self, simple_zone):
        """Person without helmet in zone - violation."""
        person = (100, 100, 200, 400)
        helmets = []  # No helmets
        is_viol, zone = is_violation(person, helmets, simple_zone)
        assert is_viol is True
        assert zone == 'TestZone'

    def test_person_outside_zone(self, simple_zone):
        """Person outside zone - no violation regardless of helmet."""
        person = (400, 100, 500, 400)  # Outside zone
        helmets = []
        is_viol, zone = is_violation(person, helmets, simple_zone)
        assert is_viol is False
        assert zone == ""

    def test_helmet_not_on_head(self, simple_zone):
        """Helmet present but not on head region - violation."""
        person = (100, 100, 200, 400)
        # Helmet below head region (head is top 35%)
        helmets = [(120, 250, 180, 300)]
        is_viol, zone = is_violation(person, helmets, simple_zone, head_iou_thresh=0.05)
        assert is_viol is True
        assert zone == 'TestZone'

    def test_helmet_barely_overlaps_head(self, simple_zone):
        """Helmet barely overlaps head - should count if above threshold."""
        person = (100, 100, 200, 400)
        # Helmet slightly overlapping head region
        helmets = [(120, 90, 180, 140)]
        is_viol, zone = is_violation(person, helmets, simple_zone, head_iou_thresh=0.01)
        assert is_viol is False  # Should detect helmet
        assert zone == 'TestZone'

    def test_multiple_helmets_one_matches(self, simple_zone):
        """Multiple helmets, one matches head."""
        person = (100, 100, 200, 400)
        helmets = [
            (50, 50, 80, 80),       # Not on this person
            (120, 100, 180, 150),   # On head
            (250, 250, 280, 280)    # Elsewhere
        ]
        is_viol, zone = is_violation(person, helmets, simple_zone)
        assert is_viol is False
        assert zone == 'TestZone'

    def test_invalid_person_bbox(self, simple_zone):
        """Invalid person bbox - no violation."""
        person = (100, 100, 100, 100)  # Zero area
        helmets = []
        is_viol, zone = is_violation(person, helmets, simple_zone)
        assert is_viol is False
        assert zone == ""

    def test_non_mandatory_zone(self):
        """Zone that doesn't require helmets."""
        zone = [{'name': 'SafeZone', 'points': [[0, 0], [300, 0], [300, 500], [0, 500]], 'mandatory_helmet': False}]
        person = (100, 100, 200, 400)
        helmets = []
        is_viol, zone_name = is_violation(person, helmets, zone)
        assert is_viol is False
        assert zone_name == 'SafeZone'

    def test_custom_head_ratio(self, simple_zone):
        """Test with custom head region ratio."""
        person = (100, 100, 200, 400)  # Height = 300
        # Helmet at position that would match with larger head ratio
        helmets = [(120, 150, 180, 200)]

        # With default 0.35 ratio, head ends at y=205, so helmet doesn't overlap much
        is_viol_default, _ = is_violation(person, helmets, simple_zone, head_ratio=0.35)

        # With 0.5 ratio, head ends at y=250, so helmet overlaps more
        is_viol_larger, _ = is_violation(person, helmets, simple_zone, head_ratio=0.5)

        # Larger head ratio should be more likely to detect helmet
        assert is_viol_larger is False  # Helmet detected


class TestBatchViolations:
    """Test batch_violations function."""

    @pytest.fixture
    def test_zone(self):
        """Test zone configuration."""
        return [{'name': 'Zone1', 'points': [[0, 0], [500, 0], [500, 500], [0, 500]], 'mandatory_helmet': True}]

    def test_multiple_persons(self, test_zone):
        """Test batch processing of multiple persons."""
        persons = [
            (100, 100, 200, 400),  # Person 0
            (300, 100, 400, 400),  # Person 1
        ]
        helmets = [
            (120, 100, 180, 150),  # Helmet for person 0
        ]

        results = batch_violations(persons, helmets, test_zone)

        assert len(results) == 2
        assert results[0] == (0, False, 'Zone1')  # Has helmet
        assert results[1] == (1, True, 'Zone1')   # No helmet

    def test_empty_lists(self, test_zone):
        """Test with empty person list."""
        results = batch_violations([], [], test_zone)
        assert len(results) == 0

    def test_all_compliant(self, test_zone):
        """Test when all persons are compliant."""
        persons = [
            (100, 100, 200, 400),
            (300, 100, 400, 400),
        ]
        helmets = [
            (120, 100, 180, 150),
            (320, 100, 380, 150),
        ]

        results = batch_violations(persons, helmets, test_zone)

        assert all(not is_viol for _, is_viol, _ in results)


class TestGetViolationSummary:
    """Test get_violation_summary function."""

    def test_basic_summary(self):
        """Test basic summary calculation."""
        violations = [
            (0, False, 'Zone1'),
            (1, True, 'Zone1'),
            (2, True, 'Zone2')
        ]

        summary = get_violation_summary(violations)

        assert summary['total_persons'] == 3
        assert summary['total_violations'] == 2
        assert summary['total_compliant'] == 1
        assert summary['violation_rate'] == pytest.approx(66.666, rel=1e-2)

    def test_zone_breakdown(self):
        """Test zone-level breakdown."""
        violations = [
            (0, False, 'Zone1'),
            (1, True, 'Zone1'),
            (2, True, 'Zone1'),
            (3, False, 'Zone2'),
        ]

        summary = get_violation_summary(violations)

        assert summary['zones']['Zone1']['total'] == 3
        assert summary['zones']['Zone1']['violations'] == 2
        assert summary['zones']['Zone1']['compliant'] == 1

        assert summary['zones']['Zone2']['total'] == 1
        assert summary['zones']['Zone2']['violations'] == 0
        assert summary['zones']['Zone2']['compliant'] == 1

    def test_empty_violations(self):
        """Test with empty violations list."""
        summary = get_violation_summary([])

        assert summary['total_persons'] == 0
        assert summary['total_violations'] == 0
        assert summary['violation_rate'] == 0.0

    def test_all_violations(self):
        """Test when all persons are violating."""
        violations = [
            (0, True, 'Zone1'),
            (1, True, 'Zone1'),
            (2, True, 'Zone1'),
        ]

        summary = get_violation_summary(violations)

        assert summary['violation_rate'] == 100.0
        assert summary['total_violations'] == 3


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_tiny_helmet(self):
        """Test with very small helmet bbox."""
        zone = [{'name': 'Zone1', 'points': [[0, 0], [500, 0], [500, 500], [0, 500]], 'mandatory_helmet': True}]
        person = (100, 100, 200, 400)
        # Tiny helmet
        helmets = [(150, 120, 152, 122)]

        is_viol, _ = is_violation(person, helmets, zone, head_iou_thresh=0.001)
        # With very low threshold, tiny helmet should be detected
        assert is_viol is False

    def test_person_near_polygon_edge(self):
        """Test person whose centroid is just inside/outside polygon edge."""
        zone = [{'name': 'Zone1', 'points': [[0, 0], [100, 0], [100, 100], [0, 100]], 'mandatory_helmet': True}]

        # Person mostly inside, centroid inside
        person_inside = (80, 40, 120, 140)  # Centroid at (100, 90) - inside
        is_viol_inside, zone_inside = is_violation(person_inside, [], zone)
        assert zone_inside == 'Zone1'

        # Person mostly inside, centroid outside
        person_outside = (90, 40, 130, 140)  # Centroid at (110, 90) - outside
        is_viol_outside, zone_outside = is_violation(person_outside, [], zone)
        assert zone_outside == ""

    def test_overlapping_persons(self):
        """Test with overlapping person bboxes."""
        zone = [{'name': 'Zone1', 'points': [[0, 0], [500, 0], [500, 500], [0, 500]], 'mandatory_helmet': True}]
        persons = [
            (100, 100, 200, 400),
            (150, 100, 250, 400),  # Overlapping
        ]
        helmets = [(120, 100, 180, 150)]  # Only one helmet

        results = batch_violations(persons, helmets, zone)

        # First person should have helmet
        assert results[0][1] is False
        # Second person likely doesn't (depends on head region overlap)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
