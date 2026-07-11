from types import SimpleNamespace

from PySide6.QtMultimedia import QMediaPlayer

from app.infrastructure.audio import ActivePlayback, QtAudioEngine


class FakeOutput:
    def __init__(self) -> None:
        self.volume: float | None = None

    def setVolume(self, volume: float) -> None:
        self.volume = volume


def test_finished_overlap_removes_only_its_own_player() -> None:
    engine = QtAudioEngine()
    first = object()
    second = object()
    engine._players[1] = [
        ActivePlayback(first, SimpleNamespace(), 50),
        ActivePlayback(second, SimpleNamespace(), 50),
    ]

    engine._remove_finished(1, first, QMediaPlayer.MediaStatus.EndOfMedia)

    assert [item.player for item in engine._players[1]] == [second]


def test_master_volume_preserves_active_per_sound_volume() -> None:
    engine = QtAudioEngine()
    output = FakeOutput()
    engine._players[1] = [ActivePlayback(object(), output, 50)]

    engine.set_master_volume(80)

    assert output.volume == 0.4
