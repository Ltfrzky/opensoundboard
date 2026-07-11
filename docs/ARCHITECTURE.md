# Architecture

`app.domain` contains Qt-free models, errors, enums, and replaceable contracts. `app.application`
coordinates those contracts. `app.infrastructure` provides SQLite, safe-file-library, Qt Multimedia,
and optional `pynput` or disabled-hotkey adapters. `app.application.hotkeys.HotkeyCoordinator`
owns assignment, conflict, debounce, and registration lifecycle. `app.presentation` contains
PySide6 views, hotkey capture/settings dialogs, and a `HotkeyBridge` that routes backend callbacks
into Qt.

Runtime data lives in the operating system's per-user application-data location: SQLite data,
managed media, and rotating logs are kept there rather than in the repository.
