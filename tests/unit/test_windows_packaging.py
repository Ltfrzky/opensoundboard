from __future__ import annotations

import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def test_windows_packaging_declares_portable_hotkey_enabled_build() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    build_script = (PROJECT_ROOT / "scripts" / "build_windows.ps1").read_text(encoding="utf-8")

    assert pyproject["project"]["optional-dependencies"]["package"] == ["PyInstaller>=6.21,<7"]
    assert "--onedir" in build_script
    assert "--windowed" in build_script
    assert "--collect-data app.presentation" in build_script
    assert "--collect-all pynput" in build_script
