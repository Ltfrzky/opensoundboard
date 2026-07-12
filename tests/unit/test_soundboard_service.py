from pathlib import Path

import pytest

from app.application.service import SoundboardService
from app.domain.enums.playback import PlaybackMode
from app.domain.errors import BoardNotEmptyError
from app.domain.models import PlaybackSnapshot
from app.infrastructure.database import SQLiteStore
from app.infrastructure.file_library import FileLibrary


class FakeAudioEngine:
    def __init__(self) -> None:
        self.played: list[int] = []
        self.stopped: list[int] = []
        self.lanes: dict[str, PlaybackSnapshot] = {}
        self.master_volume = 100

    def play(self, sound, lane_id: str) -> None:
        self.played.append(sound.id)
        self.lanes[lane_id] = PlaybackSnapshot(lane_id, sound.id)

    def active_lanes(self) -> list[PlaybackSnapshot]:
        return list(self.lanes.values())

    def stop_lane(self, lane_id: str) -> None:
        self.lanes.pop(lane_id, None)

    def stop_sound(self, sound_id: int) -> None:
        self.stopped.append(sound_id)
        self.lanes = {
            lane_id: lane for lane_id, lane in self.lanes.items() if lane.sound_id != sound_id
        }

    def stop_all(self) -> None:
        self.stopped.append(-1)
        self.lanes.clear()

    def set_master_volume(self, volume: int) -> None:
        self.master_volume = volume


@pytest.fixture
def service(tmp_path: Path) -> SoundboardService:
    store = SQLiteStore(tmp_path / "soundboard.sqlite3")
    return SoundboardService(
        store, store, store, FileLibrary(tmp_path / "library"), FakeAudioEngine()
    )


def test_first_launch_creates_my_sounds_board(service: SoundboardService) -> None:
    assert [board.name for board in service.list_boards()] == ["My Sounds"]


def test_update_board_persists_name_and_material_icon(service: SoundboardService) -> None:
    board = service.list_boards()[0]

    updated = service.update_board(board.id, name="  Podcast  ", icon="mic")

    assert (updated.name, updated.icon) == ("Podcast", "mic")
    assert service.list_boards()[0].icon == "mic"


def test_import_copy_creates_managed_sound(service: SoundboardService, tmp_path: Path) -> None:
    source = tmp_path / "airhorn.wav"
    source.write_bytes(b"RIFF")

    result = service.import_files(service.list_boards()[0].id, [source], copy_files=True)

    assert result.imported[0].name == "Airhorn"
    assert result.imported[0].file_path.parent.name == "library"


def test_duplicate_source_is_skipped(service: SoundboardService, tmp_path: Path) -> None:
    source = tmp_path / "ding.wav"
    source.write_bytes(b"RIFF")
    board_id = service.list_boards()[0].id
    service.import_files(board_id, [source], copy_files=False)

    result = service.import_files(board_id, [source], copy_files=False)

    assert result.imported == []
    assert result.skipped == ["ding.wav: already imported"]


def test_missing_reference_file_is_visible(service: SoundboardService, tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"RIFF")
    board_id = service.list_boards()[0].id
    sound = service.import_files(board_id, [source], copy_files=False).imported[0]
    source.unlink()

    assert service.get_sound(sound.id).is_missing


def test_non_empty_board_cannot_be_deleted(service: SoundboardService, tmp_path: Path) -> None:
    board = service.create_board("Live")
    source = tmp_path / "clip.wav"
    source.write_bytes(b"RIFF")
    service.import_files(board.id, [source], copy_files=False)

    with pytest.raises(BoardNotEmptyError):
        service.delete_board(board.id)


def test_stop_previous_stops_before_playing_again(
    service: SoundboardService, tmp_path: Path
) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"RIFF")
    sound = service.import_files(service.list_boards()[0].id, [source], copy_files=False).imported[
        0
    ]
    service.set_playback_mode(PlaybackMode.STOP_PREVIOUS)

    service.play(sound.id)
    service.play(sound.id)

    assert service.audio_engine.stopped == [-1]


def test_overlap_does_not_stop_existing_playback(
    service: SoundboardService, tmp_path: Path
) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"RIFF")
    sound = service.import_files(service.list_boards()[0].id, [source], copy_files=False).imported[
        0
    ]
    service.set_playback_mode(PlaybackMode.OVERLAP)

    service.play(sound.id)
    service.play(sound.id)

    assert service.audio_engine.stopped == []


def test_update_sound_persists_name_board_volume_and_loop(
    service: SoundboardService, tmp_path: Path
) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"RIFF")
    original = service.import_files(
        service.list_boards()[0].id, [source], copy_files=False
    ).imported[0]
    target_board = service.create_board("Live")

    updated = service.update_sound(
        original.id,
        name="  Stinger  ",
        board_id=target_board.id,
        volume=42,
        loop_enabled=True,
    )

    assert (updated.name, updated.board_id, updated.volume, updated.loop_enabled) == (
        "Stinger",
        target_board.id,
        42,
        True,
    )


def test_delete_sound_removes_it_from_the_board(service: SoundboardService, tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"RIFF")
    board_id = service.list_boards()[0].id
    sound = service.import_files(board_id, [source], copy_files=False).imported[0]

    service.delete_sound(sound.id)

    assert service.list_sounds(board_id) == []
