from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from app.domain.enums.playback import PlaybackMode
from app.domain.errors import InvalidSoundError
from app.domain.interfaces import AudioEngine, BoardRepository, SettingsRepository, SoundRepository
from app.domain.models import Board, PlaybackSnapshot, Sound
from app.infrastructure.file_library import FileLibrary


@dataclass(slots=True)
class ImportResult:
    imported: list[Sound] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def skipped(self) -> list[str]:
        """Compatibility view for callers that previously rendered one skipped list."""
        return [*self.duplicates, *self.failures]


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
        self._active_lanes: dict[str, PlaybackSnapshot] = {}
        self.set_master_volume(self.master_volume())

    def list_boards(self) -> list[Board]:
        return self.boards.list_boards()

    def create_board(self, name: str) -> Board:
        return self.boards.create_board(name)

    def rename_board(self, board_id: int, name: str) -> Board:
        return self.boards.rename_board(board_id, name)

    def update_board(self, board_id: int, *, name: str, icon: str) -> Board:
        return self.boards.update_board(board_id, name=name, icon=icon)

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
            existing.duration_ms,
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
            existing.duration_ms,
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
                    result.duplicates.append(f"{source.name}: already imported")
                    continue
                stored_path = self.library.store(source, copy_files)
                display_name = source.stem.replace("-", " ").replace("_", " ").title()
                result.imported.append(
                    self.sounds.save_sound(
                        Sound(0, board_id, display_name, stored_path, Path(normalized))
                    )
                )
            except Exception as error:
                result.failures.append(str(error))
        return result

    def playback_mode(self) -> PlaybackMode:
        return PlaybackMode(
            self.settings.get_setting("playback_mode", PlaybackMode.STOP_PREVIOUS.value)
        )

    def set_playback_mode(self, mode: PlaybackMode | str) -> None:
        self.settings.set_setting("playback_mode", PlaybackMode(mode).value)

    def play(self, sound_id: int) -> PlaybackSnapshot:
        sound = self.get_sound(sound_id)
        if sound.is_missing:
            raise InvalidSoundError(f"{sound.name}: file is missing and cannot be played")
        mode = self.playback_mode()
        if mode is PlaybackMode.STOP_PREVIOUS and self.active_lanes():
            self.stop_all()
        elif mode is PlaybackMode.STOP_SAME_SOUND:
            if any(lane.sound_id == sound.id for lane in self.active_lanes()):
                self.stop(sound.id)
        lane = PlaybackSnapshot(uuid4().hex, sound.id, 0, sound.duration_ms)
        self.audio_engine.play(sound, lane.lane_id)
        self._active_lanes[lane.lane_id] = lane
        return lane

    def stop(self, sound_id: int) -> None:
        stopper = getattr(self.audio_engine, "stop_sound", None)
        if stopper is not None:
            stopper(sound_id)
        else:
            self.audio_engine.stop(sound_id)  # type: ignore[attr-defined]
        self._active_lanes = {
            lane_id: lane
            for lane_id, lane in self._active_lanes.items()
            if lane.sound_id != sound_id
        }

    def stop_lane(self, lane_id: str) -> None:
        lane = next((item for item in self.active_lanes() if item.lane_id == lane_id), None)
        if lane is None:
            return
        stopper = getattr(self.audio_engine, "stop_lane", None)
        if stopper is not None:
            stopper(lane_id)
        else:
            self.stop(lane.sound_id)
        self._active_lanes.pop(lane_id, None)

    def stop_all(self) -> None:
        self.audio_engine.stop_all()
        self._active_lanes.clear()

    def active_lanes(self) -> list[PlaybackSnapshot]:
        reader = getattr(self.audio_engine, "active_lanes", None)
        if reader is None:
            return list(self._active_lanes.values())
        lanes = reader()
        self._active_lanes = {lane.lane_id: lane for lane in lanes}
        return lanes

    def master_volume(self) -> int:
        return max(0, min(100, int(self.settings.get_setting("master_volume", "100"))))

    def set_master_volume(self, volume: int) -> None:
        normalized = max(0, min(100, int(volume)))
        self.settings.set_setting("master_volume", str(normalized))
        self.audio_engine.set_master_volume(normalized)

    def record_duration(self, sound_id: int, duration_ms: int | None) -> Sound:
        sound = self.get_sound(sound_id)
        if duration_ms is None or duration_ms <= 0 or sound.duration_ms == duration_ms:
            return sound
        return self.sounds.save_sound(
            Sound(
                sound.id,
                sound.board_id,
                sound.name,
                sound.file_path,
                sound.source_path,
                sound.volume,
                sound.loop_enabled,
                sound.sort_order,
                sound.hotkey,
                duration_ms,
            )
        )

    def recover_sound(self, sound_id: int, replacement: Path) -> Sound:
        existing = self.get_sound(sound_id)
        source = self.library.validate(replacement)
        normalized = self.library.normalized(source)
        if self.sounds.has_source_path(normalized, exclude_id=sound_id):
            raise InvalidSoundError(f"{source.name}: already imported")
        stored = self.library.store(source, self.library.is_managed(existing.file_path))
        return self.sounds.save_sound(
            Sound(
                existing.id,
                existing.board_id,
                existing.name,
                stored,
                Path(normalized),
                existing.volume,
                existing.loop_enabled,
                existing.sort_order,
                existing.hotkey,
                existing.duration_ms,
            )
        )
