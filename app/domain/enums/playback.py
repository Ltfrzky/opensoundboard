from enum import StrEnum


class PlaybackMode(StrEnum):
    OVERLAP = "overlap"
    STOP_PREVIOUS = "stop_previous"


class PlaybackState(StrEnum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
