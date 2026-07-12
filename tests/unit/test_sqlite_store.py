from pathlib import Path

import pytest

from app.domain.models import Sound
from app.infrastructure.database import SQLiteStore


def test_save_sound_rejects_a_nonexistent_board(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "soundboard.sqlite3")

    with pytest.raises(ValueError, match="board does not exist"):
        store.save_sound(Sound(0, 999, "Horn", tmp_path / "horn.wav"))


def test_store_operations_release_the_database_file(tmp_path: Path) -> None:
    database = tmp_path / "soundboard.sqlite3"
    store = SQLiteStore(database)

    store.set_setting("master_volume", "80")
    renamed = tmp_path / "renamed.sqlite3"
    database.rename(renamed)

    assert renamed.is_file()


def test_transaction_rolls_back_failed_writes_and_releases_database_file(tmp_path: Path) -> None:
    database = tmp_path / "soundboard.sqlite3"
    store = SQLiteStore(database)

    with pytest.raises(RuntimeError, match="abort"):
        with store._transaction() as connection:
            connection.execute("INSERT INTO settings(key, value) VALUES (?, ?)", ("theme", "dark"))
            raise RuntimeError("abort")

    assert store.get_setting("theme", "system") == "system"
    database.rename(tmp_path / "renamed.sqlite3")
