from __future__ import annotations

import sqlite3
from pathlib import Path

from app.domain.errors import BoardNotEmptyError
from app.domain.models import Board, Sound


class SQLiteStore:
    """Small typed repository implementation for local SQLite storage."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL, color TEXT, icon TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS sounds (
                    id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL REFERENCES boards(id),
                    name TEXT NOT NULL, file_path TEXT NOT NULL, source_path TEXT,
                    volume INTEGER NOT NULL DEFAULT 100, loop_enabled INTEGER NOT NULL DEFAULT 0,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                """
            )
            if connection.execute("SELECT COUNT(*) FROM boards").fetchone()[0] == 0:
                connection.execute(
                    "INSERT INTO boards(name, sort_order) VALUES (?, 0)", ("My Sounds",)
                )

    def list_boards(self) -> list[Board]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM boards ORDER BY sort_order, id").fetchall()
        return [
            Board(row["id"], row["name"], row["color"], row["icon"], row["sort_order"])
            for row in rows
        ]

    def create_board(self, name: str) -> Board:
        board = Board(0, name)
        with self._connect() as connection:
            order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM boards"
            ).fetchone()[0]
            cursor = connection.execute(
                "INSERT INTO boards(name, sort_order) VALUES (?, ?)", (board.name, order)
            )
        return Board(cursor.lastrowid, board.name, sort_order=order)

    def rename_board(self, board_id: int, name: str) -> Board:
        board = Board(board_id, name)
        with self._connect() as connection:
            connection.execute("UPDATE boards SET name = ? WHERE id = ?", (board.name, board_id))
        return board

    def delete_board(self, board_id: int) -> None:
        with self._connect() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM sounds WHERE board_id = ?", (board_id,)
            ).fetchone()[0]
            if count:
                raise BoardNotEmptyError("Move or delete all sounds before deleting this board")
            connection.execute("DELETE FROM boards WHERE id = ?", (board_id,))

    def list_sounds(self, board_id: int) -> list[Sound]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM sounds WHERE board_id = ? ORDER BY sort_order, id", (board_id,)
            ).fetchall()
        return [self._to_sound(row) for row in rows]

    def get_sound(self, sound_id: int) -> Sound:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM sounds WHERE id = ?", (sound_id,)).fetchone()
        if row is None:
            raise KeyError(f"Sound {sound_id} does not exist")
        return self._to_sound(row)

    def save_sound(self, sound: Sound) -> Sound:
        with self._connect() as connection:
            if sound.id:
                connection.execute(
                    "UPDATE sounds SET board_id=?, name=?, file_path=?, source_path=?, "
                    "volume=?, loop_enabled=? WHERE id=?",
                    (
                        sound.board_id,
                        sound.name,
                        str(sound.file_path),
                        self._source_value(sound),
                        sound.volume,
                        int(sound.loop_enabled),
                        sound.id,
                    ),
                )
                return sound
            order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM sounds WHERE board_id = ?",
                (sound.board_id,),
            ).fetchone()[0]
            cursor = connection.execute(
                "INSERT INTO sounds(board_id, name, file_path, source_path, volume, "
                "loop_enabled, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    sound.board_id,
                    sound.name,
                    str(sound.file_path),
                    self._source_value(sound),
                    sound.volume,
                    int(sound.loop_enabled),
                    order,
                ),
            )
        return Sound(
            cursor.lastrowid,
            sound.board_id,
            sound.name,
            sound.file_path,
            sound.source_path,
            sound.volume,
            sound.loop_enabled,
            order,
        )

    def delete_sound(self, sound_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM sounds WHERE id = ?", (sound_id,))

    def has_source_path(self, source_path: str) -> bool:
        with self._connect() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM sounds WHERE source_path = ?", (source_path,)
                ).fetchone()
                is not None
            )

    def get_setting(self, key: str, default: str) -> str:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return default if row is None else str(row["value"])

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    @staticmethod
    def _source_value(sound: Sound) -> str | None:
        return None if sound.source_path is None else str(sound.source_path)

    @staticmethod
    def _to_sound(row: sqlite3.Row) -> Sound:
        source = row["source_path"]
        return Sound(
            row["id"],
            row["board_id"],
            row["name"],
            Path(row["file_path"]),
            None if source is None else Path(source),
            row["volume"],
            bool(row["loop_enabled"]),
            row["sort_order"],
        )
