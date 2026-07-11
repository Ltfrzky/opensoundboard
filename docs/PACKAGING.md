# Packaging

PyInstaller packaging is deferred. When implemented, build Windows, macOS, and Linux bundles on
their respective target operating systems; cross-compilation is not promised. Release builds that
include global hotkeys must install the optional `hotkeys` extra; GUI-only builds may omit it.
