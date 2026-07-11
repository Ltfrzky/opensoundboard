from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import InvalidHotkeyError


class HotkeyModifier(StrEnum):
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    META = "meta"


_MODIFIER_ALIASES = {
    "ctrl": HotkeyModifier.CTRL,
    "control": HotkeyModifier.CTRL,
    "alt": HotkeyModifier.ALT,
    "option": HotkeyModifier.ALT,
    "shift": HotkeyModifier.SHIFT,
    "meta": HotkeyModifier.META,
    "cmd": HotkeyModifier.META,
    "command": HotkeyModifier.META,
    "win": HotkeyModifier.META,
    "windows": HotkeyModifier.META,
    "super": HotkeyModifier.META,
}
_KEY_ALIASES = {
    "escape": "Esc",
    "esc": "Esc",
    "return": "Enter",
    "enter": "Enter",
    "space": "Space",
    "tab": "Tab",
    "backspace": "Backspace",
    "delete": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
}
_RESERVED = {
    "Alt+F4",
    "Ctrl+Alt+Delete",
    "Ctrl+Esc",
    "Meta+L",
    "Meta+Q",
    "Meta+W",
}
_FUNCTION_KEY = re.compile(r"F(?:[1-9]|1[0-9]|2[0-4])$")


@dataclass(frozen=True, slots=True)
class HotkeyBinding:
    modifiers: frozenset[HotkeyModifier]
    key: str

    def __post_init__(self) -> None:
        if not self.key:
            raise InvalidHotkeyError("A hotkey must include a non-modifier key")
        if not self.modifiers:
            raise InvalidHotkeyError("A global hotkey must include a modifier")
        object.__setattr__(self, "key", _normalize_key(self.key))

    @classmethod
    def parse(cls, value: str) -> HotkeyBinding:
        tokens = [token.strip() for token in value.split("+")]
        if not value.strip() or any(not token for token in tokens):
            raise InvalidHotkeyError("Hotkey cannot be blank")
        modifiers: set[HotkeyModifier] = set()
        key_tokens: list[str] = []
        for token in tokens:
            modifier = _MODIFIER_ALIASES.get(token.casefold())
            if modifier is not None:
                if modifier in modifiers:
                    raise InvalidHotkeyError("A hotkey cannot repeat a modifier")
                modifiers.add(modifier)
            else:
                key_tokens.append(token)
        if len(key_tokens) != 1:
            raise InvalidHotkeyError("A hotkey must contain exactly one non-modifier key")
        binding = cls(frozenset(modifiers), key_tokens[0])
        if binding.canonical in _RESERVED:
            raise InvalidHotkeyError(f"Reserved operating-system shortcut: {binding.canonical}")
        return binding

    @property
    def canonical(self) -> str:
        order = (
            HotkeyModifier.CTRL,
            HotkeyModifier.ALT,
            HotkeyModifier.SHIFT,
            HotkeyModifier.META,
        )
        parts = [modifier.value.title() for modifier in order if modifier in self.modifiers]
        return "+".join([*parts, self.key])

    @property
    def display_label(self) -> str:
        return self.canonical.replace("+", " + ")


def _normalize_key(value: str) -> str:
    token = value.strip()
    alias = _KEY_ALIASES.get(token.casefold())
    if alias is not None:
        return alias
    if len(token) == 1 and token.isalnum():
        return token.upper()
    upper = token.upper()
    if _FUNCTION_KEY.fullmatch(upper):
        return upper
    raise InvalidHotkeyError(f"Unsupported hotkey key: {value}")
