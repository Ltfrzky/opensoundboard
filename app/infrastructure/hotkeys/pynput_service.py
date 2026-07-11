from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.domain.interfaces import HotkeyCapability, HotkeyRegistrationResult
from app.domain.models import HotkeyBinding, HotkeyModifier
from app.infrastructure.hotkeys.capability import detect_capability


class PynputHotkeyService:
    def __init__(
        self,
        *,
        backend_factory: Callable[[dict[str, Callable[[], None]]], Any] | None = None,
        platform_name: str | None = None,
        environment: dict[str, str] | None = None,
        dependency_available: bool | None = None,
    ) -> None:
        if dependency_available is None:
            dependency_available = self._dependency_available()
        self._capability = detect_capability(
            platform_name=platform_name,
            environment=environment,
            dependency_available=dependency_available,
        )
        self._backend_factory = backend_factory
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._listener: Any = None

    def capability(self) -> HotkeyCapability:
        return self._capability

    def register(
        self, binding: HotkeyBinding, callback: Callable[[], None]
    ) -> HotkeyRegistrationResult:
        if not self._capability.available:
            return HotkeyRegistrationResult(False, self._capability.message)
        callbacks = dict(self._callbacks)
        callbacks[binding.canonical] = callback
        try:
            self._restart(callbacks)
        except Exception as error:
            return HotkeyRegistrationResult(
                False, f"Could not register {binding.display_label}: {error}"
            )
        self._callbacks = callbacks
        return HotkeyRegistrationResult(True, f"Registered {binding.display_label}")

    def unregister(self, binding: HotkeyBinding) -> None:
        callbacks = dict(self._callbacks)
        callbacks.pop(binding.canonical, None)
        self._restart(callbacks)
        self._callbacks = callbacks

    def unregister_all(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._callbacks.clear()

    def _restart(self, callbacks: dict[str, Callable[[], None]]) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if not callbacks:
            return
        factory = self._backend_factory or self._default_factory()
        mapping = {self._pynput_value(key): callback for key, callback in callbacks.items()}
        listener = factory(mapping)
        listener.start()
        self._listener = listener

    @staticmethod
    def _pynput_value(canonical: str) -> str:
        binding = HotkeyBinding.parse(canonical)
        order = (
            HotkeyModifier.CTRL,
            HotkeyModifier.ALT,
            HotkeyModifier.SHIFT,
            HotkeyModifier.META,
        )
        parts = [f"<{modifier.value}>" for modifier in order if modifier in binding.modifiers]
        key = binding.key.casefold()
        if len(key) > 1:
            key = f"<{key}>"
        return "+".join([*parts, key])

    @staticmethod
    def _dependency_available() -> bool:
        try:
            import pynput.keyboard  # noqa: F401
        except ImportError:
            return False
        return True

    @staticmethod
    def _default_factory() -> Callable[[dict[str, Callable[[], None]]], Any]:
        from pynput import keyboard

        return keyboard.GlobalHotKeys
