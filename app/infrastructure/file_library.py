from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from app.domain.errors import InvalidSoundError

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}


class FileLibrary:
    def __init__(self, library_path: Path) -> None:
        self.library_path = Path(library_path)
        self.library_path.mkdir(parents=True, exist_ok=True)

    def validate(self, path: Path) -> Path:
        candidate = Path(path)
        if candidate.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            raise InvalidSoundError(f"{candidate.name}: unsupported audio format")
        if not candidate.is_file():
            raise InvalidSoundError(f"{candidate.name}: file cannot be read")
        return candidate.resolve()

    def store(self, source: Path, copy_file: bool) -> Path:
        source = self.validate(source)
        if not copy_file:
            return source
        target = self.library_path / f"{uuid.uuid4().hex}_{source.name}"
        shutil.copy2(source, target)
        return target

    @staticmethod
    def normalized(path: Path) -> str:
        return os.path.normcase(str(Path(path).resolve()))
