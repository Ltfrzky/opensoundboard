# Contributing

Use Python 3.11 or newer and create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,hotkeys]"
.venv\Scripts\ruff check .
.venv\Scripts\python -m pytest
```

Keep domain and application code independent of PySide6. UI widgets call application use cases;
SQLite, audio, filesystem, and hotkeys remain behind explicit interfaces. Add tests for all new
behavior and describe platform limitations honestly. The `hotkeys` extra is optional; GUI playback
must continue to work when it is absent or unsupported.
