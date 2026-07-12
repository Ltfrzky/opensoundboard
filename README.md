# OpenSoundboard

OpenSoundboard is an offline-first, cross-platform desktop soundboard built with
Python and PySide6. This repository currently contains the functional prototype
described in the project documentation.

## Development

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,hotkeys]"
.venv\Scripts\python -m app.main
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check .
```

The prototype supports local board and sound persistence, safe file imports, local
playback, and configurable global hotkeys. Install only `.[dev]` to run GUI playback
without global hooks; install `.[dev,hotkeys]` to enable the optional `pynput` backend.
Backups, packaging, output-device selection, and advanced organization tools remain
deferred.

## Windows beta packaging

The current beta artifact is an unsigned portable Windows x64 ZIP with optional global-hotkey
support included. Build and validate it using [the packaging guide](docs/PACKAGING.md) and the
[Windows beta QA gate](docs/WINDOWS_BETA_QA.md). Windows may show a trust warning for this unsigned
build.
