from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.domain.errors import BoardNotEmptyError
from app.domain.models import Board, HotkeyBinding, Sound


class SQLiteStore:
    """Small typed repository implementation for local SQLite storage."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _create_schema(self) -> None:
        with self._transaction() as connection:
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
                    sort_order INTEGER NOT NULL DEFAULT 0, hotkey TEXT, duration_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(sounds)").fetchall()
            }
            if "hotkey" not in columns:
                connection.execute("ALTER TABLE sounds ADD COLUMN hotkey TEXT")
            if "duration_ms" not in columns:
                connection.execute("ALTER TABLE sounds ADD COLUMN duration_ms INTEGER")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_sounds_hotkey "
                "ON sounds(hotkey) WHERE hotkey IS NOT NULL"
            )
            connection.execute("UPDATE boards SET icon = 'equalizer' WHERE icon IS NULL")
            if connection.execute("SELECT COUNT(*) FROM boards").fetchone()[0] == 0:
                connection.execute(
                    "INSERT INTO boards(name, icon, sort_order) VALUES (?, ?, 0)",
                    ("My Sounds", "equalizer"),
                )

    def list_boards(self) -> list[Board]:
        with self._transaction() as connection:
            rows = connection.execute("SELECT * FROM boards ORDER BY sort_order, id").fetchall()
        return [
            Board(row["id"], row["name"], row["color"], row["icon"], row["sort_order"])
            for row in rows
        ]

    def create_board(self, name: str) -> Board:
        board = Board(0, name, icon="equalizer")
        with self._transaction() as connection:
            order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM boards"
            ).fetchone()[0]
            cursor = connection.execute(
                "INSERT INTO boards(name, icon, sort_order) VALUES (?, ?, ?)",
                (board.name, board.icon, order),
            )
        return Board(cursor.lastrowid, board.name, icon=board.icon, sort_order=order)

    def rename_board(self, board_id: int, name: str) -> Board:
        board = Board(board_id, name)
        with self._transaction() as connection:
            connection.execute("UPDATE boards SET name = ? WHERE id = ?", (board.name, board_id))
        return board

    def update_board(self, board_id: int, *, name: str, icon: str) -> Board:
        board = Board(board_id, name, icon=icon)
        with self._transaction() as connection:
            connection.execute(
                "UPDATE boards SET name = ?, icon = ? WHERE id = ?",
                (board.name, board.icon, board_id),
            )
        return board

    def delete_board(self, board_id: int) -> None:
        with self._transaction() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM sounds WHERE board_id = ?", (board_id,)
            ).fetchone()[0]
            if count:
                raise BoardNotEmptyError("Move or delete all sounds before deleting this board")
            connection.execute("DELETE FROM boards WHERE id = ?", (board_id,))

    def list_sounds(self, board_id: int) -> list[Sound]:
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT * FROM sounds WHERE board_id = ? ORDER BY sort_order, id", (board_id,)
            ).fetchall()
        return [self._to_sound(row) for row in rows]

    def get_sound(self, sound_id: int) -> Sound:
        with self._transaction() as connection:
            row = connection.execute("SELECT * FROM sounds WHERE id = ?", (sound_id,)).fetchone()
        if row is None:
            raise KeyError(f"Sound {sound_id} does not exist")
        return self._to_sound(row)

    def save_sound(self, sound: Sound) -> Sound:
        with self._transaction() as connection:
            if sound.id:
                try:
                    connection.execute(
                        "UPDATE sounds SET board_id=?, name=?, file_path=?, source_path=?, "
                        "volume=?, loop_enabled=?, hotkey=?, duration_ms=? WHERE id=?",
                        (
                            sound.board_id,
                            sound.name,
                            str(sound.file_path),
                            self._source_value(sound),
                            sound.volume,
                            int(sound.loop_enabled),
                            sound.hotkey,
                            sound.duration_ms,
                            sound.id,
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    raise self._sound_save_error(error) from error
                return sound
            order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM sounds WHERE board_id = ?",
                (sound.board_id,),
            ).fetchone()[0]
            try:
                cursor = connection.execute(
                    "INSERT INTO sounds(board_id, name, file_path, source_path, volume, "
                    "loop_enabled, sort_order, hotkey, duration_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        sound.board_id,
                        sound.name,
                        str(sound.file_path),
                        self._source_value(sound),
                        sound.volume,
                        int(sound.loop_enabled),
                        order,
                        sound.hotkey,
                        sound.duration_ms,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise self._sound_save_error(error) from error
        return Sound(
            cursor.lastrowid,
            sound.board_id,
            sound.name,
            sound.file_path,
            sound.source_path,
            sound.volume,
            sound.loop_enabled,
            order,
            sound.hotkey,
            sound.duration_ms,
        )

    def delete_sound(self, sound_id: int) -> None:
        with self._transaction() as connection:
            connection.execute("DELETE FROM sounds WHERE id = ?", (sound_id,))

    def has_source_path(self, source_path: str, *, exclude_id: int | None = None) -> bool:
        with self._transaction() as connection:
            query = "SELECT 1 FROM sounds WHERE source_path = ?"
            values: tuple[object, ...] = (source_path,)
            if exclude_id is not None:
                query += " AND id != ?"
                values = (source_path, exclude_id)
            return (
                connection.execute(query, values).fetchone()
                is not None
            )

    def get_setting(self, key: str, default: str) -> str:
        with self._transaction() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return default if row is None else str(row["value"])

    def set_setting(self, key: str, value: str) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    @staticmethod
    def _sound_save_error(error: sqlite3.IntegrityError) -> ValueError:
        if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return ValueError("Sound board does not exist")
        return ValueError("Sound hotkey must be unique")

    @staticmethod
    def _source_value(sound: Sound) -> str | None:
        return None if sound.source_path is None else str(sound.source_path)

    @staticmethod
    def _to_sound(row: sqlite3.Row) -> Sound:
        source = row["source_path"]
        binding = HotkeyBinding.parse_persisted(row["hotkey"])
        return Sound(
            row["id"],
            row["board_id"],
            row["name"],
            Path(row["file_path"]),
            None if source is None else Path(source),
            row["volume"],
            bool(row["loop_enabled"]),
            row["sort_order"],
            binding.canonical if binding else None,
            row["duration_ms"],
        )
