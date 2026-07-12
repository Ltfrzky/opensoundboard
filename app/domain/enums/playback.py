from enum import StrEnum


class PlaybackMode(StrEnum):
    OVERLAP = "overlap"
    STOP_PREVIOUS = "stop_previous"
    STOP_SAME_SOUND = "stop_same_sound"


class PlaybackState(StrEnum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
