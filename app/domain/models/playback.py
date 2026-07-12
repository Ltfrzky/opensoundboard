from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlaybackSnapshot:
    """Qt-free state for one independently controllable playback lane."""

    lane_id: str
    sound_id: int
    position_ms: int = 0
    duration_ms: int | None = None

    @property
    def progress(self) -> float | None:
        if not self.duration_ms or self.duration_ms <= 0:
            return None
        return min(1.0, max(0.0, self.position_ms / self.duration_ms))
