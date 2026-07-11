from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from app.domain.models import Sound


@dataclass(slots=True)
class ActivePlayback:
    player: QMediaPlayer
    output: QAudioOutput
    sound_volume: int


class QtAudioEngine:
    """Qt Multimedia playback adapter that can retain overlapping players."""

    def __init__(self) -> None:
        self._players: dict[int, list[ActivePlayback]] = defaultdict(list)
        self._master_volume = 100

    def play(self, sound: Sound, allow_overlap: bool) -> None:
        if not allow_overlap:
            self.stop_all()
        output = QAudioOutput()
        output.setVolume((sound.volume / 100) * (self._master_volume / 100))
        player = QMediaPlayer()
        player.setAudioOutput(output)
        player.setSource(QUrl.fromLocalFile(str(sound.file_path)))
        player.setLoops(QMediaPlayer.Loops.Infinite if sound.loop_enabled else 1)
        player.mediaStatusChanged.connect(
            lambda status, identifier=sound.id, source=player: self._remove_finished(
                identifier, source, status
            )
        )
        self._players[sound.id].append(ActivePlayback(player, output, sound.volume))
        player.play()

    def stop(self, sound_id: int) -> None:
        for playback in self._players.pop(sound_id, []):
            playback.player.stop()

    def stop_all(self) -> None:
        for sound_id in tuple(self._players):
            self.stop(sound_id)

    def set_master_volume(self, volume: int) -> None:
        self._master_volume = max(0, min(100, volume))
        for players in self._players.values():
            for playback in players:
                playback.output.setVolume(
                    (playback.sound_volume / 100) * (self._master_volume / 100)
                )

    def _remove_finished(
        self, sound_id: int, player: QMediaPlayer, status: QMediaPlayer.MediaStatus
    ) -> None:
        if status is QMediaPlayer.MediaStatus.EndOfMedia:
            active = self._players.get(sound_id, [])
            remaining = [playback for playback in active if playback.player is not player]
            if remaining:
                self._players[sound_id] = remaining
            else:
                self._players.pop(sound_id, None)
