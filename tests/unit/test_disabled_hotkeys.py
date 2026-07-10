from __future__ import annotations

from app.infrastructure.hotkeys.disabled import DisabledHotkeyService


def test_disabled_hotkeys_report_an_honest_unavailable_capability() -> None:
    service = DisabledHotkeyService()

    capability = service.capability()

    assert capability.available is False
    assert capability.message == "Global hotkeys are not configured in this prototype."


def test_disabled_hotkeys_reject_registration_without_side_effects() -> None:
    service = DisabledHotkeyService()

    registered = service.register("Ctrl+1", lambda: None)

    assert registered is False
