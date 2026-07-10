# Design Status

The prototype uses a compact desktop layout: a board sidebar, a control toolbar, and a sound-card
grid. Its status bar always states that global hotkeys are not configured. Missing files are
displayed as disabled cards, and importing defaults to copying media into the managed library.

This is a native PySide6 utility interface, not a web application. It includes board rename/delete
actions and per-sound rename, move, volume, loop, and delete controls. Search, list mode, and
reorder remain future work.
