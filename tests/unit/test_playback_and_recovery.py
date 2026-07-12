from pathlib import Path

import pytest

from app.application.service import SoundboardService
from app.domain.enums.playback import PlaybackMode
from app.domain.errors import InvalidSoundError
from app.domain.models import PlaybackSnapshot
from app.infrastructure.database import SQLiteStore
from app.infrastructure.file_library import FileLibrary


class LaneAudioEngine:
    def __init__(self) -> None:
        self.lanes: dict[str, PlaybackSnapshot] = {}
        self.master_volume = 100
        self.stopped_lanes: list[str] = []
        self.stopped_sounds: list[int] = []
        self.stop_all_calls = 0

    def play(self, sound, lane_id: str) -> None:
        self.lanes[lane_id] = PlaybackSnapshot(lane_id, sound.id, 0, 5_000)

    def active_lanes(self) -> list[PlaybackSnapshot]:
        return list(self.lanes.values())

    def stop_lane(self, lane_id: str) -> None:
        self.stopped_lanes.append(lane_id)
        self.lanes.pop(lane_id, None)

    def stop_sound(self, sound_id: int) -> None:
        self.stopped_sounds.append(sound_id)
        for lane_id, lane in list(self.lanes.items()):
            if lane.sound_id == sound_id:
                self.lanes.pop(lane_id)

    def stop_all(self) -> None:
        self.stop_all_calls += 1
        self.lanes.clear()

    def set_master_volume(self, volume: int) -> None:
        self.master_volume = volume


@pytest.fixture
def service(tmp_path: Path) -> SoundboardService:
    store = SQLiteStore(tmp_path / "soundboard.sqlite3")
    return SoundboardService(
        store, store, store, FileLibrary(tmp_path / "library"), LaneAudioEngine()
    )


def _import(service: SoundboardService, tmp_path: Path, name: str):
    path = tmp_path / name
    path.write_bytes(b"RIFF")
    board_id = service.list_boards()[0].id
    return service.import_files(board_id, [path], copy_files=False).imported[0]


def test_active_lanes_can_be_stopped_individually(
    service: SoundboardService, tmp_path: Path
) -> None:
    first = _import(service, tmp_path, "first.wav")
    second = _import(service, tmp_path, "second.wav")
    service.set_playback_mode(PlaybackMode.OVERLAP)

    first_lane = service.play(first.id)
    second_lane = service.play(second.id)

    assert [lane.lane_id for lane in service.active_lanes()] == [
        first_lane.lane_id,
        second_lane.lane_id,
    ]
    service.stop_lane(first_lane.lane_id)

    assert [lane.sound_id for lane in service.active_lanes()] == [second.id]


def test_stop_previous_clears_existing_lanes_before_starting_next(
    service: SoundboardService, tmp_path: Path
) -> None:
    first = _import(service, tmp_path, "first.wav")
    second = _import(service, tmp_path, "second.wav")

    service.play(first.id)
    service.play(second.id)

    assert service.audio_engine.stop_all_calls == 1
    assert [lane.sound_id for lane in service.active_lanes()] == [second.id]


def test_stop_same_sound_replaces_all_active_instances_of_triggered_sound(
    service: SoundboardService, tmp_path: Path
) -> None:
    sound = _import(service, tmp_path, "repeat.wav")
    service.set_playback_mode(PlaybackMode.OVERLAP)
    service.play(sound.id)
    service.play(sound.id)

    service.set_playback_mode(PlaybackMode.STOP_SAME_SOUND)
    replacement = service.play(sound.id)

    assert service.audio_engine.stopped_sounds == [sound.id]
    assert [lane.lane_id for lane in service.active_lanes()] == [replacement.lane_id]


def test_stop_same_sound_keeps_other_sounds_playing(
    service: SoundboardService, tmp_path: Path
) -> None:
    first = _import(service, tmp_path, "first.wav")
    second = _import(service, tmp_path, "second.wav")
    service.set_playback_mode(PlaybackMode.STOP_SAME_SOUND)

    service.play(first.id)
    second_lane = service.play(second.id)
    replacement = service.play(first.id)

    assert service.audio_engine.stopped_sounds == [first.id]
    assert {lane.lane_id for lane in service.active_lanes()} == {
        second_lane.lane_id,
        replacement.lane_id,
    }


def test_master_volume_is_persisted_and_applied(service: SoundboardService) -> None:
    service.set_master_volume(42)

    assert service.master_volume() == 42
    assert service.audio_engine.master_volume == 42


def test_import_result_separates_duplicates_from_failures(
    service: SoundboardService, tmp_path: Path
) -> None:
    source = tmp_path / "intro.wav"
    source.write_bytes(b"RIFF")
    invalid = tmp_path / "notes.txt"
    invalid.write_text("not audio", encoding="utf-8")
    board_id = service.list_boards()[0].id
    service.import_files(board_id, [source], copy_files=False)

    result = service.import_files(board_id, [source, invalid], copy_files=False)

    assert result.imported == []
    assert result.duplicates == ["intro.wav: already imported"]
    assert result.failures == ["notes.txt: unsupported audio format"]


def test_recover_reference_sound_preserves_assignment_and_reference_policy(
    service: SoundboardService, tmp_path: Path
) -> None:
    sound = _import(service, tmp_path, "walk-on.wav")
    service.set_sound_hotkey(sound.id, "Ctrl+1")
    sound.file_path.unlink()
    replacement = tmp_path / "walk-on-replacement.wav"
    replacement.write_bytes(b"RIFF")

    recovered = service.recover_sound(sound.id, replacement)

    assert recovered.file_path == replacement.resolve()
    assert recovered.source_path == replacement.resolve()
    assert recovered.hotkey == "Ctrl+1"
    assert not recovered.is_missing


def test_missing_media_is_rejected_before_a_playback_lane_is_created(
    service: SoundboardService, tmp_path: Path
) -> None:
    sound = _import(service, tmp_path, "missing.wav")
    sound.file_path.unlink()

    with pytest.raises(InvalidSoundError, match="file is missing"):
        service.play(sound.id)

    assert service.active_lanes() == []
