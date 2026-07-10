from collections.abc import Callable

from app.domain.interfaces import HotkeyCapability


class DisabledHotkeyService:
    def capability(self) -> HotkeyCapability:
        return HotkeyCapability(False, "Global hotkeys are not configured in this prototype.")

    def register(self, hotkey: str, callback: Callable[[], None]) -> bool:
        return False

    def unregister(self, hotkey: str) -> None:
        return None
