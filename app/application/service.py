from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.domain.enums.playback import PlaybackMode
from app.domain.interfaces import AudioEngine, BoardRepository, SettingsRepository, SoundRepository
from app.domain.models import Board, Sound
from app.infrastructure.file_library import FileLibrary


@dataclass(slots=True)
class ImportResult:
    imported: list[Sound] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class SoundboardService:
    def __init__(
        self,
        boards: BoardRepository,
        sounds: SoundRepository,
        settings: SettingsRepository,
        library: FileLibrary,
        audio_engine: AudioEngine,
    ) -> None:
        self.boards = boards
        self.sounds = sounds
        self.settings = settings
        self.library = library
        self.audio_engine = audio_engine
        self._active_ids: set[int] = set()

    def list_boards(self) -> list[Board]:
        return self.boards.list_boards()

    def create_board(self, name: str) -> Board:
        return self.boards.create_board(name)

    def rename_board(self, board_id: int, name: str) -> Board:
        return self.boards.rename_board(board_id, name)

    def delete_board(self, board_id: int) -> None:
        self.boards.delete_board(board_id)

    def list_sounds(self, board_id: int) -> list[Sound]:
        return self.sounds.list_sounds(board_id)

    def get_sound(self, sound_id: int) -> Sound:
        return self.sounds.get_sound(sound_id)

    def update_sound(
        self,
        sound_id: int,
        *,
        name: str,
        board_id: int,
        volume: int,
        loop_enabled: bool,
    ) -> Sound:
        existing = self.get_sound(sound_id)
        updated = Sound(
            sound_id,
            board_id,
            name,
            existing.file_path,
            existing.source_path,
            volume,
            loop_enabled,
            existing.sort_order,
            existing.hotkey,
        )
        return self.sounds.save_sound(updated)

    def set_sound_hotkey(self, sound_id: int, hotkey: str | None) -> Sound:
        existing = self.get_sound(sound_id)
        updated = Sound(
            existing.id,
            existing.board_id,
            existing.name,
            existing.file_path,
            existing.source_path,
            existing.volume,
            existing.loop_enabled,
            existing.sort_order,
            hotkey,
        )
        return self.sounds.save_sound(updated)

    def delete_sound(self, sound_id: int) -> None:
        self.stop(sound_id)
        self.sounds.delete_sound(sound_id)

    def import_files(self, board_id: int, paths: list[Path], copy_files: bool) -> ImportResult:
        result = ImportResult()
        for raw_path in paths:
            try:
                source = self.library.validate(raw_path)
                normalized = self.library.normalized(source)
                if self.sounds.has_source_path(normalized):
                    result.skipped.append(f"{source.name}: already imported")
                    continue
                stored_path = self.library.store(source, copy_files)
                display_name = source.stem.replace("-", " ").replace("_", " ").title()
                result.imported.append(
                    self.sounds.save_sound(
                        Sound(0, board_id, display_name, stored_path, Path(normalized))
                    )
                )
            except Exception as error:
                result.skipped.append(str(error))
        return result

    def playback_mode(self) -> PlaybackMode:
        return PlaybackMode(
            self.settings.get_setting("playback_mode", PlaybackMode.STOP_PREVIOUS.value)
        )

    def set_playback_mode(self, mode: PlaybackMode) -> None:
        self.settings.set_setting("playback_mode", mode.value)

    def play(self, sound_id: int) -> None:
        sound = self.get_sound(sound_id)
        if self.playback_mode() is PlaybackMode.STOP_PREVIOUS:
            for active_id in tuple(self._active_ids):
                self.audio_engine.stop(active_id)
            self._active_ids.clear()
        self.audio_engine.play(sound, self.playback_mode() is PlaybackMode.OVERLAP)
        self._active_ids.add(sound.id)

    def stop(self, sound_id: int) -> None:
        self.audio_engine.stop(sound_id)
        self._active_ids.discard(sound_id)

    def stop_all(self) -> None:
        self.audio_engine.stop_all()
        self._active_ids.clear()
