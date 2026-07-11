from __future__ import annotations

import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from app.application.service import SoundboardService
from app.infrastructure.audio import QtAudioEngine
from app.infrastructure.database import SQLiteStore
from app.infrastructure.file_library import FileLibrary
from app.infrastructure.hotkeys.pynput_service import PynputHotkeyService


@dataclass(frozen=True, slots=True)
class AppContext:
    service: SoundboardService
    hotkeys: PynputHotkeyService


def create_context(data_path: Path | None = None) -> AppContext:
    root = data_path or Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    root.mkdir(parents=True, exist_ok=True)
    if data_path is None:
        _configure_logging(root)
    store = SQLiteStore(root / "opensoundboard.sqlite3")
    service = SoundboardService(store, store, store, FileLibrary(root / "library"), QtAudioEngine())
    return AppContext(service, PynputHotkeyService())


def _configure_logging(root: Path) -> None:
    logger = logging.getLogger("opensoundboard")
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        root / "opensoundboard.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    logger.addHandler(handler)
