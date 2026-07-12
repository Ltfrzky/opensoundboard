from types import SimpleNamespace

from PySide6.QtMultimedia import QMediaPlayer

from app.infrastructure.audio import ActivePlayback, QtAudioEngine


class FakeOutput:
    def __init__(self) -> None:
        self.volume: float | None = None

    def setVolume(self, volume: float) -> None:
        self.volume = volume


class FakePlayer:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def test_finished_playback_removes_only_its_own_lane() -> None:
    engine = QtAudioEngine()
    first = object()
    second = object()
    engine._players = {
        "first": ActivePlayback(1, first, SimpleNamespace(), 50),
        "second": ActivePlayback(1, second, SimpleNamespace(), 50),
    }

    engine._remove_finished("first", first, QMediaPlayer.MediaStatus.EndOfMedia)

    assert list(engine._players) == ["second"]


def test_master_volume_preserves_active_per_sound_volume() -> None:
    engine = QtAudioEngine()
    output = FakeOutput()
    engine._players = {"lane": ActivePlayback(1, object(), output, 50)}

    engine.set_master_volume(80)

    assert output.volume == 0.4


def test_active_lanes_expose_progress_and_stop_one_lane() -> None:
    engine = QtAudioEngine()
    player = FakePlayer()
    engine._players = {"lane": ActivePlayback(4, player, SimpleNamespace(), 80, 1_500, 5_000)}

    assert engine.active_lanes()[0].progress == 0.3
    engine.stop_lane("lane")

    assert player.stopped
    assert engine.active_lanes() == []
