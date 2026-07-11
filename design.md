# Design Status

The prototype uses a compact desktop layout: a board sidebar, a control toolbar, and a sound-card
grid. The status bar reports current global-hotkey capability. Hotkey settings expose a master
enable switch, debounce duration, Panic Stop capture, and re-registration. Sound cards show their
assignment and provide capture/clear actions. Missing files are displayed as disabled cards, and
importing defaults to copying media into the managed library.

This is a native PySide6 utility interface, not a web application. It includes board rename/delete
actions and per-sound rename, move, volume, loop, hotkey, and delete controls. Search, list mode,
reorder, backup, and output-device selection remain future work.
