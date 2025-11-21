"""
Tracking state management to prevent double-counting violations.

Uses track IDs from YOLO tracker (ByteTrack/OC-SORT) to ensure each person
is only counted once per zone per day.
"""

import time
from typing import Dict, Set, Tuple, Optional
from datetime import datetime, date
from collections import defaultdict


class TrackState:
    """
    Manages tracking state to prevent double-counting violations.

    Tracks which track_id has been seen in which zones to ensure:
    - One violation per track per zone per day
    - Proper handling of tracks moving between zones
    - Daily reset of tracking state
    """

    def __init__(self, reset_hour: int = 0):
        """
        Initialize tracking state.

        Args:
            reset_hour: Hour of day (0-23) when tracking state resets (default: midnight)
        """
        self.reset_hour = reset_hour

        # track_id -> set of zones where violation was already counted today
        self._violation_zones: Dict[int, Set[str]] = defaultdict(set)

        # track_id -> last seen timestamp
        self._last_seen: Dict[int, float] = {}

        # track_id -> last zone
        self._last_zone: Dict[int, str] = {}

        # track_id -> PPE status history (for occlusion handling)
        # Stores last known PPE status: {'has_helmet': bool, 'has_vest': bool, 'frame': int}
        self._ppe_history: Dict[int, Dict] = {}

        # track_id -> violation frame counter (require violations in multiple frames)
        self._violation_frames: Dict[int, int] = defaultdict(int)

        # Current tracking date
        self._current_date: date = datetime.now().date()

    def _check_date_reset(self) -> None:
        """Check if we need to reset tracking state for new day."""
        current_date = datetime.now().date()
        if current_date > self._current_date:
            self.reset()
            self._current_date = current_date

    def reset(self) -> None:
        """Reset all tracking state (typically called at start of new day)."""
        self._violation_zones.clear()
        self._last_seen.clear()
        self._last_zone.clear()
        print(f"TrackState reset at {datetime.now()}")

    def should_count(
        self,
        track_id: int,
        zone: str,
        is_violation: bool = True
    ) -> bool:
        """
        Determine if this track should be counted as a violation in this zone.

        Returns True if:
        - This is the first time seeing this track_id in this zone today, AND
        - is_violation is True

        Args:
            track_id: Unique track identifier from tracker
            zone: Zone name where person is detected
            is_violation: Whether this is a violation (default: True)

        Returns:
            True if violation should be counted, False otherwise

        Examples:
            >>> state = TrackState()
            >>> state.should_count(1, 'CraneBay', is_violation=True)
            True
            >>> state.should_count(1, 'CraneBay', is_violation=True)
            False  # Already counted in this zone
            >>> state.should_count(1, 'LoadingDock', is_violation=True)
            True  # Different zone
        """
        self._check_date_reset()

        # Update last seen
        self._last_seen[track_id] = time.time()
        self._last_zone[track_id] = zone

        # If not a violation, don't count
        if not is_violation:
            return False

        # Check if already counted in this zone
        if zone in self._violation_zones[track_id]:
            return False

        # Mark as counted in this zone
        self._violation_zones[track_id].add(zone)
        return True

    def update_seen(
        self,
        track_id: int,
        zone: str,
        timestamp: Optional[float] = None
    ) -> None:
        """
        Update that a track was seen in a zone (without counting violation).

        Useful for tracking compliant persons or updating tracking state
        without incrementing violation count.

        Args:
            track_id: Unique track identifier
            zone: Zone name
            timestamp: Optional timestamp (default: current time)
        """
        self._check_date_reset()

        ts = timestamp if timestamp is not None else time.time()
        self._last_seen[track_id] = ts
        self._last_zone[track_id] = zone

    def get_track_info(self, track_id: int) -> Dict:
        """
        Get information about a specific track.

        Args:
            track_id: Track identifier

        Returns:
            Dictionary with track information

        Examples:
            >>> state = TrackState()
            >>> state.should_count(1, 'CraneBay')
            True
            >>> info = state.get_track_info(1)
            >>> info['violation_zones']
            {'CraneBay'}
        """
        return {
            'track_id': track_id,
            'violation_zones': self._violation_zones.get(track_id, set()).copy(),
            'last_seen': self._last_seen.get(track_id),
            'last_zone': self._last_zone.get(track_id),
            'violation_count': len(self._violation_zones.get(track_id, set()))
        }

    def get_stats(self) -> Dict:
        """
        Get overall tracking statistics.

        Returns:
            Dictionary with tracking stats

        Examples:
            >>> state = TrackState()
            >>> state.should_count(1, 'Zone1')
            >>> state.should_count(2, 'Zone1')
            >>> state.should_count(2, 'Zone2')
            >>> stats = state.get_stats()
            >>> stats['unique_tracks']
            2
            >>> stats['total_violations']
            3
        """
        total_violations = sum(len(zones) for zones in self._violation_zones.values())
        unique_tracks = len(self._violation_zones)

        # Violations per zone
        zone_counts = defaultdict(int)
        for zones in self._violation_zones.values():
            for zone in zones:
                zone_counts[zone] += 1

        return {
            'unique_tracks': unique_tracks,
            'total_violations': total_violations,
            'violations_per_zone': dict(zone_counts),
            'active_tracks': len(self._last_seen),
            'current_date': self._current_date.isoformat()
        }

    def cleanup_old_tracks(self, max_age_seconds: float = 300) -> int:
        """
        Remove tracks that haven't been seen recently.

        Helps prevent memory buildup from tracks that are no longer active.
        Note: This doesn't reset violation counts for active tracks.

        Args:
            max_age_seconds: Maximum age in seconds before track is considered stale (default: 300 = 5 min)

        Returns:
            Number of tracks removed

        Examples:
            >>> state = TrackState()
            >>> state.update_seen(1, 'Zone1', timestamp=time.time() - 400)
            >>> state.update_seen(2, 'Zone1', timestamp=time.time())
            >>> removed = state.cleanup_old_tracks(max_age_seconds=300)
            >>> removed
            1
        """
        self._check_date_reset()

        current_time = time.time()
        stale_tracks = []

        for track_id, last_seen in self._last_seen.items():
            if current_time - last_seen > max_age_seconds:
                stale_tracks.append(track_id)

        for track_id in stale_tracks:
            # Remove from last_seen and last_zone, but keep violation history
            self._last_seen.pop(track_id, None)
            self._last_zone.pop(track_id, None)

        return len(stale_tracks)

    def export_state(self) -> Dict:
        """
        Export tracking state for persistence or debugging.

        Returns:
            Dictionary with complete tracking state
        """
        return {
            'current_date': self._current_date.isoformat(),
            'violation_zones': {
                track_id: list(zones)
                for track_id, zones in self._violation_zones.items()
            },
            'last_seen': dict(self._last_seen),
            'last_zone': dict(self._last_zone),
            'stats': self.get_stats()
        }

    def import_state(self, state_dict: Dict) -> None:
        """
        Import tracking state from exported dictionary.

        Args:
            state_dict: Dictionary from export_state()
        """
        self._current_date = datetime.fromisoformat(state_dict['current_date']).date()

        self._violation_zones = defaultdict(
            set,
            {int(k): set(v) for k, v in state_dict['violation_zones'].items()}
        )

        self._last_seen = {int(k): float(v) for k, v in state_dict['last_seen'].items()}
        self._last_zone = {int(k): str(v) for k, v in state_dict['last_zone'].items()}

    def update_ppe_status(self, track_id: int, has_helmet: bool, has_vest: bool, frame_idx: int, confidence: float = 1.0):
        """
        Update PPE status history for a track.

        Used to handle occlusion - if we can't detect PPE due to occlusion,
        we can use the last known status.

        Args:
            track_id: Track identifier
            has_helmet: Whether helmet is detected
            has_vest: Whether vest is detected
            frame_idx: Current frame number
            confidence: Confidence in this detection (1.0 = full visibility, <1.0 = partial occlusion)
        """
        if confidence > 0.7:  # Only update history if we're confident (person clearly visible)
            self._ppe_history[track_id] = {
                'has_helmet': has_helmet,
                'has_vest': has_vest,
                'frame': frame_idx,
                'confidence': confidence
            }

    def get_ppe_status(self, track_id: int, frame_idx: int, max_frame_gap: int = 30) -> Dict:
        """
        Get last known PPE status for a track.

        Returns the last known PPE status if it's recent (within max_frame_gap frames).
        Useful for handling temporary occlusion.

        Args:
            track_id: Track identifier
            frame_idx: Current frame number
            max_frame_gap: Maximum frames since last status update (default: 30 = ~1 second at 30fps)

        Returns:
            Dictionary with 'has_helmet', 'has_vest', or None if no recent history
        """
        if track_id not in self._ppe_history:
            return None

        last_status = self._ppe_history[track_id]
        frame_gap = frame_idx - last_status['frame']

        # Only use history if it's recent (within max_frame_gap)
        if frame_gap <= max_frame_gap:
            return last_status

        return None
