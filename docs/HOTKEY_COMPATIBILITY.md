# Hotkey Compatibility

Global hotkeys are implemented through an optional `pynput` adapter. They are disabled by
default and can be enabled from Hotkeys settings. Assignments are persisted even when the
current platform cannot register them, so they can be retried later.

- Windows: supported when the optional dependency is installed.
- macOS: supported when the optional dependency is installed; Accessibility/Input Monitoring
  permission may be required by the operating system.
- Linux/X11: supported when an X11 display is available.
- Linux/Wayland: explicitly unsupported by this backend; GUI playback remains available.
- Missing `pynput`, unsupported platforms, conflicts, and registration failures are shown in the
  status bar or Hotkeys settings without crashing the application.

The backend callback runs outside the Qt GUI thread. `HotkeyBridge` emits queued Qt signals for
sound playback and Panic Stop. A master enable switch unregisters all bindings while preserving
their assignments. Hotkeys are canonicalized as `Ctrl+Alt+Shift+Meta+Key`, duplicate assignments
require explicit replacement, and rapid repeats are debounced.
