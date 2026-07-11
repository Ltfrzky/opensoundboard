from pathlib import Path

import pytest

from app.domain.errors import InvalidHotkeyError
from app.domain.models import Sound
from app.domain.models.hotkey import HotkeyBinding, HotkeyModifier


def test_hotkey_binding_normalizes_aliases_and_modifier_order() -> None:
    binding = HotkeyBinding.parse(" shift + command + 1 ")

    assert binding.canonical == "Shift+Meta+1"
    assert binding.display_label == "Shift + Meta + 1"
    assert binding.modifiers == frozenset({HotkeyModifier.SHIFT, HotkeyModifier.META})


@pytest.mark.parametrize("value", ["", "Ctrl", "Ctrl+Ctrl+K", "NotAKey", "Alt+F4"])
def test_hotkey_binding_rejects_invalid_or_reserved_shortcuts(value: str) -> None:
    with pytest.raises(InvalidHotkeyError):
        HotkeyBinding.parse(value)


def test_sound_persists_optional_hotkey_value() -> None:
    sound = Sound(1, 2, "Horn", Path("horn.wav"), hotkey="Ctrl+1")

    assert sound.hotkey == "Ctrl+1"
