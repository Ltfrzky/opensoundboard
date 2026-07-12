from collections.abc import Callable

from app.domain.enums import HotkeyStatusState
from app.domain.interfaces import HotkeyCapability, HotkeyRegistrationResult
from app.domain.models import HotkeyBinding


class DisabledHotkeyService:
    def capability(self) -> HotkeyCapability:
        return HotkeyCapability(
            False,
            "Global hotkeys are not configured in this prototype.",
            HotkeyStatusState.UNSUPPORTED,
        )

    def register(
        self, binding: HotkeyBinding, callback: Callable[[], None]
    ) -> HotkeyRegistrationResult:
        return HotkeyRegistrationResult(False, "Global hotkeys are unavailable on this platform")

    def unregister(self, binding: HotkeyBinding) -> None:
        return None

    def unregister_all(self) -> None:
        return None
