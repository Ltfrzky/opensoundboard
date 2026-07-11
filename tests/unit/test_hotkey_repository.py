from pathlib import Path

import pytest

from app.domain.models import Sound
from app.infrastructure.database import SQLiteStore


def test_existing_database_migrates_and_round_trips_sound_hotkey(tmp_path: Path) -> None:
    database = tmp_path / "soundboard.sqlite3"
    store = SQLiteStore(database)
    board = store.list_boards()[0]
    sound = store.save_sound(Sound(0, board.id, "Horn", tmp_path / "horn.wav", hotkey="Ctrl+1"))

    loaded = store.get_sound(sound.id)

    assert loaded.hotkey == "Ctrl+1"


def test_duplicate_sound_hotkey_is_rejected(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "soundboard.sqlite3")
    board = store.list_boards()[0]
    store.save_sound(Sound(0, board.id, "One", tmp_path / "one.wav", hotkey="Ctrl+1"))

    with pytest.raises(ValueError, match="hotkey"):
        store.save_sound(Sound(0, board.id, "Two", tmp_path / "two.wav", hotkey="Ctrl+1"))
