from app.application.service import SoundboardService
from app.domain.enums.playback import PlaybackMode


class SoundboardViewModel:
    def __init__(self, service: SoundboardService) -> None:
        self.service = service

    def set_overlap(self, enabled: bool) -> None:
        self.service.set_playback_mode(
            PlaybackMode.OVERLAP if enabled else PlaybackMode.STOP_PREVIOUS
        )
