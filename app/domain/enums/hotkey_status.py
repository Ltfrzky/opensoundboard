from enum import StrEnum


class HotkeyStatusState(StrEnum):
    READY = "ready"
    DISABLED_BY_USER = "disabled_by_user"
    MISSING_DEPENDENCY = "missing_dependency"
    WAYLAND_UNSUPPORTED = "wayland_unsupported"
    X11_DISPLAY_MISSING = "x11_display_missing"
    MACOS_PERMISSION_REQUIRED = "macos_permission_required"
    REGISTRATION_FAILED = "registration_failed"
    PENDING_RETRY = "pending_retry"
    UNSUPPORTED = "unsupported"
