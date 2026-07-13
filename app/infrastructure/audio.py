from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from app.domain.models import PlaybackSnapshot, Sound


@dataclass(slots=True)
class ActivePlayback:
    sound_id: int
    player: QMediaPlayer
    output: QAudioOutput
    sound_volume: int
    position_ms: int = 0
    duration_ms: int | None = None


class QtAudioEngine:
    """Qt Multimedia adapter with independently controllable live playback lanes."""

    def __init__(self) -> None:
        self._players: dict[str, ActivePlayback] = {}
        self._master_volume = 100

    def play(self, sound: Sound, lane_id: str) -> None:
        output = QAudioOutput()
        output.setVolume((sound.volume / 100) * (self._master_volume / 100))
        player = QMediaPlayer()
        player.setAudioOutput(output)
        player.setSource(QUrl.fromLocalFile(str(sound.file_path)))
        player.setLoops(QMediaPlayer.Loops.Infinite if sound.loop_enabled else 1)
        self._players[lane_id] = ActivePlayback(
            sound.id, player, output, sound.volume, duration_ms=sound.duration_ms
        )
        player.positionChanged.connect(
            lambda position, identifier=lane_id, source=player: self._update_position(
                identifier, source, position
            )
        )
        player.durationChanged.connect(
            lambda duration, identifier=lane_id, source=player: self._update_duration(
                identifier, source, duration
            )
        )
        player.mediaStatusChanged.connect(
            lambda status, identifier=lane_id, source=player: self._remove_finished(
                identifier, source, status
            )
        )
        player.errorOccurred.connect(
            lambda _error, _message, identifier=lane_id, source=player: self._remove_errored(
                identifier, source
            )
        )
        player.play()

    def active_lanes(self) -> list[PlaybackSnapshot]:
        return [
            PlaybackSnapshot(lane_id, playback.sound_id, playback.position_ms, playback.duration_ms)
            for lane_id, playback in self._players.items()
        ]

    def stop_lane(self, lane_id: str) -> None:
        playback = self._players.pop(lane_id, None)
        if playback is not None:
            playback.player.stop()

    def stop_sound(self, sound_id: int) -> None:
        for lane_id, playback in tuple(self._players.items()):
            if playback.sound_id == sound_id:
                self.stop_lane(lane_id)

    def stop_all(self) -> None:
        for lane_id in tuple(self._players):
            self.stop_lane(lane_id)

    def set_master_volume(self, volume: int) -> None:
        self._master_volume = max(0, min(100, volume))
        for playback in self._players.values():
            playback.output.setVolume(
                (playback.sound_volume / 100) * (self._master_volume / 100)
            )

    def _update_position(self, lane_id: str, player: QMediaPlayer, position: int) -> None:
        playback = self._players.get(lane_id)
        if playback is not None and playback.player is player:
            playback.position_ms = max(0, position)

    def _update_duration(self, lane_id: str, player: QMediaPlayer, duration: int) -> None:
        playback = self._players.get(lane_id)
        if playback is not None and playback.player is player:
            playback.duration_ms = duration if duration > 0 else None

    def _remove_finished(
        self, lane_id: str, player: QMediaPlayer, status: QMediaPlayer.MediaStatus
    ) -> None:
        playback = self._players.get(lane_id)
        if status in {
            QMediaPlayer.MediaStatus.EndOfMedia,
            QMediaPlayer.MediaStatus.InvalidMedia,
        } and playback is not None and playback.player is player:
            self._players.pop(lane_id, None)

    def _remove_errored(self, lane_id: str, player: QMediaPlayer) -> None:
        playback = self._players.get(lane_id)
        if playback is not None and playback.player is player:
            self._players.pop(lane_id, None)
