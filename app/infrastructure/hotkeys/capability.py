from __future__ import annotations

import os
import sys

from app.domain.enums import HotkeyStatusState
from app.domain.interfaces import HotkeyCapability


def detect_capability(
    *,
    platform_name: str | None = None,
    environment: dict[str, str] | None = None,
    dependency_available: bool = True,
) -> HotkeyCapability:
    platform_name = platform_name or sys.platform
    environment = environment or os.environ
    if not dependency_available:
        return HotkeyCapability(
            False,
            "Install pynput via the optional 'hotkeys' extra to enable global hotkeys.",
            HotkeyStatusState.MISSING_DEPENDENCY,
        )
    if platform_name.startswith("linux"):
        session = environment.get("XDG_SESSION_TYPE", "").casefold()
        if session == "wayland" or environment.get("WAYLAND_DISPLAY"):
            return HotkeyCapability.wayland(
                "Global hotkeys are unavailable on Linux Wayland sessions."
            )
        if not environment.get("DISPLAY") and session != "x11":
            return HotkeyCapability(
                False,
                "An X11 display is required for Linux global hotkeys.",
                HotkeyStatusState.X11_DISPLAY_MISSING,
            )
        return HotkeyCapability(True, "Global hotkeys available through Linux/X11.")
    if platform_name == "darwin":
        return HotkeyCapability(
            True,
            "Global hotkeys available; macOS Accessibility or Input Monitoring permission may "
            "be required.",
            HotkeyStatusState.MACOS_PERMISSION_REQUIRED,
        )
    if platform_name.startswith("win"):
        return HotkeyCapability(True, "Global hotkeys available through Windows keyboard hooks.")
    return HotkeyCapability(
        False,
        f"Global hotkeys are not supported on platform {platform_name}.",
        HotkeyStatusState.UNSUPPORTED,
    )
