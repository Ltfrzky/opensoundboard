# OpenSoundboard

OpenSoundboard is an offline-first, cross-platform desktop soundboard built with
Python and PySide6. This repository currently contains the functional prototype
described in the project documentation.

## Development

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m app.main
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check .
```

The prototype supports local board and sound persistence, safe file imports, and
local playback. Global hotkeys, backups, packaging, output-device selection, and
advanced organization tools are intentionally deferred.
