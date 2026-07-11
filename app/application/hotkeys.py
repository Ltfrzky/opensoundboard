from __future__ import annotations

import logging
import time
from collections.abc import Callable

from app.application.service import SoundboardService
from app.domain.errors import HotkeyConflictError, HotkeyRegistrationError
from app.domain.interfaces import HotkeyCapability, HotkeyService
from app.domain.models import HotkeyBinding


class HotkeyCoordinator:
    """Coordinates persisted assignments, backend registration, and playback callbacks."""

    def __init__(
        self,
        service: SoundboardService,
        hotkeys: HotkeyService,
        *,
        sound_trigger: Callable[[int], None] | None = None,
        panic_trigger: Callable[[], None] | None = None,
    ) -> None:
        self.service = service
        self.hotkeys = hotkeys
        self._last_triggered: dict[str, float] = {}
        self._logger = logging.getLogger("opensoundboard")
        self._sound_trigger = sound_trigger
        self._panic_trigger = panic_trigger

    def capability(self) -> HotkeyCapability:
        return self.hotkeys.capability()

    def is_enabled(self) -> bool:
        return self.service.settings.get_setting("hotkeys_enabled", "0") == "1"

    def set_enabled(self, enabled: bool) -> list[str]:
        self.service.settings.set_setting("hotkeys_enabled", "1" if enabled else "0")
        if not enabled:
            self.hotkeys.unregister_all()
            return []
        return self.load_and_register_all()

    def load_and_register_all(self) -> list[str]:
        if not self.is_enabled():
            return []
        self.hotkeys.unregister_all()
        errors: list[str] = []
        for sound in self._all_sounds():
            if sound.hotkey is None:
                continue
            error = self._register(
                HotkeyBinding.parse(sound.hotkey),
                lambda sound_id=sound.id: self._trigger_sound(sound_id),
            )
            if error:
                errors.append(f"{sound.name}: {error}")
        panic = self._panic_binding()
        if panic is not None:
            error = self._register(panic, self._trigger_panic)
            if error:
                errors.append(f"Panic Stop: {error}")
        return errors

    def re_register_all(self) -> list[str]:
        return self.load_and_register_all()

    def assign_sound(
        self, sound_id: int, binding: HotkeyBinding, *, replace_existing: bool = False
    ) -> None:
        canonical = binding.canonical
        sound = self.service.get_sound(sound_id)
        owner = self._sound_for_hotkey(canonical, exclude_id=sound_id)
        if owner is not None and not replace_existing:
            raise HotkeyConflictError(f"{canonical} is already assigned to {owner.name}")
        if self._panic_binding() is not None and self._panic_binding().canonical == canonical:
            raise HotkeyConflictError("This hotkey is assigned to Panic Stop")

        old = HotkeyBinding.parse(sound.hotkey) if sound.hotkey else None
        if self.is_enabled():
            if old is not None:
                self.hotkeys.unregister(old)
            if owner is not None:
                self.hotkeys.unregister(binding)
            result = self.hotkeys.register(
                binding, lambda sound_id=sound_id: self._trigger_sound(sound_id)
            )
            if not result.success:
                if old is not None:
                    self.hotkeys.register(
                        old, lambda sound_id=sound_id: self._trigger_sound(sound_id)
                    )
                if owner is not None:
                    self.hotkeys.register(
                        binding, lambda sound_id=owner.id: self._trigger_sound(sound_id)
                    )
                if owner is None:
                    self.service.set_sound_hotkey(sound_id, canonical)
                raise HotkeyRegistrationError(result.message)

        if owner is not None:
            self.service.set_sound_hotkey(owner.id, None)
        self.service.set_sound_hotkey(sound_id, canonical)

    def clear_sound(self, sound_id: int) -> None:
        sound = self.service.get_sound(sound_id)
        if sound.hotkey and self.is_enabled():
            self.hotkeys.unregister(HotkeyBinding.parse(sound.hotkey))
        self.service.set_sound_hotkey(sound_id, None)

    def assign_panic_stop(
        self, binding: HotkeyBinding | None, *, replace_existing: bool = False
    ) -> None:
        current = self._panic_binding()
        if binding is None:
            if current is not None and self.is_enabled():
                self.hotkeys.unregister(current)
            self.service.settings.set_setting("panic_stop_hotkey", "")
            return
        owner = self._sound_for_hotkey(binding.canonical)
        if owner is not None and not replace_existing:
            raise HotkeyConflictError(f"{binding.canonical} is already assigned to {owner.name}")
        if owner is not None and self.is_enabled():
            self.hotkeys.unregister(binding)
        if current is not None and self.is_enabled():
            self.hotkeys.unregister(current)
        if self.is_enabled():
            result = self.hotkeys.register(binding, self._trigger_panic)
            if not result.success:
                if current is not None:
                    self.hotkeys.register(current, self._trigger_panic)
                if owner is not None:
                    self.hotkeys.register(
                        binding, lambda sound_id=owner.id: self._trigger_sound(sound_id)
                    )
                else:
                    self.service.settings.set_setting("panic_stop_hotkey", binding.canonical)
                raise HotkeyRegistrationError(result.message)
        if owner is not None:
            self.service.set_sound_hotkey(owner.id, None)
        self.service.settings.set_setting("panic_stop_hotkey", binding.canonical)

    def shutdown(self) -> None:
        self.hotkeys.unregister_all()

    def _register(self, binding: HotkeyBinding, callback: Callable[[], None]) -> str | None:
        result = self.hotkeys.register(binding, callback)
        return None if result.success else result.message

    def _trigger_sound(self, sound_id: int) -> None:
        if self._debounced(str(sound_id)):
            return
        try:
            if self._sound_trigger is not None:
                self._sound_trigger(sound_id)
            else:
                self.service.play(sound_id)
        except Exception:
            self._logger.exception("Hotkey playback failed for sound %s", sound_id)

    def _trigger_panic(self) -> None:
        if self._debounced("panic"):
            return
        if self._panic_trigger is not None:
            self._panic_trigger()
        else:
            self.service.stop_all()

    def _debounced(self, key: str) -> bool:
        now = time.monotonic()
        interval = int(self.service.settings.get_setting("hotkey_debounce_ms", "150")) / 1000
        previous = self._last_triggered.get(key)
        self._last_triggered[key] = now
        return previous is not None and now - previous < interval

    def _all_sounds(self):
        for board in self.service.list_boards():
            yield from self.service.list_sounds(board.id)

    def _sound_for_hotkey(self, hotkey: str, *, exclude_id: int | None = None):
        return next(
            (
                sound
                for sound in self._all_sounds()
                if sound.hotkey == hotkey and sound.id != exclude_id
            ),
            None,
        )

    def _panic_binding(self) -> HotkeyBinding | None:
        value = self.service.settings.get_setting("panic_stop_hotkey", "")
        return HotkeyBinding.parse(value) if value else None
