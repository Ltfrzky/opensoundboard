# Packaging

OpenSoundboard's first distribution artifact is an unsigned, portable Windows x64 ZIP. Build it on
Windows; cross-compilation and macOS/Linux packages are not provided.

## Build a beta archive

```powershell
.venv\Scripts\python -m pip install -e ".[dev,hotkeys,package]"
.\scripts\build_windows.ps1 -PythonExecutable .\.venv\Scripts\python.exe
```

The archive is written to `dist\OpenSoundboard-<version>-windows-x64.zip`. Extract the complete
`OpenSoundboard` folder before launching `OpenSoundboard.exe`; do not run it inside the ZIP.

The build includes the optional `pynput` backend for global hotkeys and the bundled Material Symbols
assets. SQLite data, managed media, and logs are deliberately excluded and remain in the user's
per-user AppData location. Because the build is unsigned, Windows may display a trust warning.

Run the complete [Windows beta QA gate](WINDOWS_BETA_QA.md) before distribution.
