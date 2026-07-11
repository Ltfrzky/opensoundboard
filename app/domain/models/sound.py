from dataclasses import dataclass
from pathlib import Path

from app.domain.errors import InvalidSoundError
from app.domain.models.hotkey import HotkeyBinding


@dataclass(frozen=True, slots=True)
class Sound:
    id: int
    board_id: int
    name: str
    file_path: Path
    source_path: Path | None = None
    volume: int = 100
    loop_enabled: bool = False
    sort_order: int = 0
    hotkey: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise InvalidSoundError("Sound name cannot be blank")
        if not 0 <= self.volume <= 100:
            raise InvalidSoundError("Sound volume must be between 0 and 100")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "file_path", Path(self.file_path))
        if self.source_path is not None:
            object.__setattr__(self, "source_path", Path(self.source_path))
        if self.hotkey is not None:
            object.__setattr__(self, "hotkey", HotkeyBinding.parse(self.hotkey).canonical)

    @property
    def is_missing(self) -> bool:
        return not self.file_path.is_file()
