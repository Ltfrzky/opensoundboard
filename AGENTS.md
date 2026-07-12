## Product and direction

OpenSoundboard is an offline-first, cross-platform desktop soundboard built with Python and PySide6. It lets a user organize local audio into boards, trigger playback from a native desktop UI, and optionally control playback with global hotkeys.

The current goal is a reliable functional prototype. Keep it a native PySide6 utility, with a board sidebar, transport controls, sound-card grid, and status feedback. Treat `product.md`, `design.md`, and `docs/ARCHITECTURE.md` as the product and design references.

The delivered scope includes local SQLite persistence, managed-copy or source-reference imports, duplicate and missing-file handling, Qt Multimedia playback, master volume, Stop All, playback modes, and optional global hotkeys. Backups, output-device selection, search, sorting, list view, reordering, packaging, themes, and advanced settings are deferred. Do not add deferred capabilities unless the task explicitly asks for them.

## Architecture

Keep the dependency direction strict:

- `app.domain` holds Qt-free models, errors, enums, and protocol contracts.
- `app.application` coordinates domain contracts and owns use cases.
- `app.infrastructure` implements SQLite, the file library, Qt Multimedia, and hotkey adapters.
- `app.presentation` contains PySide6 widgets and bridges application actions to the GUI.

Do not import PySide6 in `app.domain` or `app.application`. Presentation code calls application services; infrastructure details stay behind the contracts in `app.domain.interfaces`.

`app.bootstrap.create_context()` composes the production application. Runtime SQLite data, managed media, and rotating logs belong in the OS per-user application-data directory, not the repository.

## Behavior to preserve

- Support WAV, MP3, OGG, FLAC, and M4A imports. Default imports copy media into the managed library; source-reference imports retain the original path.
- Normalize source paths before duplicate checks. Surface import failures and duplicates to the user rather than silently discarding them.
- Show missing media as recoverable and disabled for playback. Do not create a playback lane for a missing file.
- Keep sound deletion and board deletion safe: stop a sound before deleting it, and reject deletion of a non-empty board.
- Preserve the three playback modes: overlap, stop previous, and stop same sound. Active playback uses lane IDs so callers can stop an individual concurrent lane.
- Keep global hotkeys optional and disabled by default. GUI playback must work without `pynput`, on unsupported platforms, and on Linux Wayland.
- Persist hotkey assignments even when registration cannot succeed. Reject duplicate bindings unless the user explicitly chooses replacement, preserve assignments when disabling hotkeys, and debounce rapid triggers.
- Route global-hotkey callbacks through `HotkeyBridge` queued Qt signals before updating UI or playback state.

## Dev environment setup

Use Python 3.11 or newer. The project uses pip and setuptools through `pyproject.toml`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,hotkeys]"
```

Use `.[dev]` for GUI-only development. The `hotkeys` extra installs optional `pynput` support.

## Build and run

Run the desktop application:

```powershell
.venv\Scripts\python -m app.main
```

PyInstaller packaging is deferred. When packaging is introduced, build each Windows, macOS, or Linux bundle on that target OS. A hotkey-enabled release requires the `hotkeys` extra.

## Testing instructions

Run the full test suite:

```powershell
.venv\Scripts\python -m pytest
```

Run one test:

```powershell
.venv\Scripts\python -m pytest tests\unit\test_audio_engine.py::test_active_lanes_expose_progress_and_stop_one_lane
```

Add focused unit tests for domain, service, and adapter behavior. Use integration tests for PySide6 bootstrap, widget, and signal behavior.

## Code style

Run Ruff before committing:

```powershell
.venv\Scripts\ruff check .
```

Ruff configuration in `pyproject.toml` targets Python 3.11, uses a 100-character line limit, and checks `E`, `F`, `I`, and `UP` rules. Follow existing dataclass and type-annotation patterns.

## PR and commit instructions

Use concise conventional commit subjects, such as `feat: add configurable global hotkeys`. Before committing, run:

```powershell
.venv\Scripts\ruff check .
.venv\Scripts\python -m pytest
```

Describe platform limitations honestly, especially hotkey support and permission requirements.

## Security and safety notes

Do not commit runtime SQLite files, managed media, logs, build artifacts, virtual environments, or secrets. The project has no required `.env` file.

Do not manually alter users' runtime databases. Evolve the SQLite schema in `SQLiteStore._create_schema()` with backward-compatible migrations and tests for existing databases.
