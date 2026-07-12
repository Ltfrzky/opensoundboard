from pathlib import Path

import pytest

from app.application.hotkeys import HotkeyCoordinator
from app.application.service import SoundboardService
from app.domain.enums.hotkey_status import HotkeyStatusState
from app.domain.errors import HotkeyRegistrationError
from app.domain.interfaces import HotkeyCapability, HotkeyRegistrationResult
from app.domain.models import HotkeyBinding, PlaybackSnapshot, Sound
from app.infrastructure.database import SQLiteStore
from app.infrastructure.file_library import FileLibrary


class SilentAudio:
    def play(self, sound: Sound, lane_id: str) -> None:
        return None

    def active_lanes(self) -> list[PlaybackSnapshot]:
        return []

    def stop_lane(self, lane_id: str) -> None:
        return None

    def stop_sound(self, sound_id: int) -> None:
        return None

    def stop_all(self) -> None:
        return None

    def set_master_volume(self, volume: int) -> None:
        return None


class StatusHotkeys:
    def __init__(self, capability: HotkeyCapability, *, fail: bool = False) -> None:
        self._capability = capability
        self.fail = fail

    def capability(self) -> HotkeyCapability:
        return self._capability

    def register(self, binding, callback) -> HotkeyRegistrationResult:
        if self.fail:
            return HotkeyRegistrationResult(False, "keyboard hook refused registration")
        return HotkeyRegistrationResult(True, "registered")

    def unregister(self, binding) -> None:
        return None

    def unregister_all(self) -> None:
        return None


def _coordinator(
    tmp_path: Path, hotkeys: StatusHotkeys
) -> tuple[SoundboardService, HotkeyCoordinator, Sound]:
    store = SQLiteStore(tmp_path / "soundboard.sqlite3")
    service = SoundboardService(
        store, store, store, FileLibrary(tmp_path / "library"), SilentAudio()
    )
    sound = store.save_sound(Sound(0, service.list_boards()[0].id, "Cue", tmp_path / "cue.wav"))
    return service, HotkeyCoordinator(service, hotkeys), sound


def test_status_reports_when_user_has_disabled_hotkeys(tmp_path: Path) -> None:
    _, coordinator, _ = _coordinator(
        tmp_path, StatusHotkeys(HotkeyCapability(True, "Global hotkeys available"))
    )

    status = coordinator.status()

    assert status.state is HotkeyStatusState.DISABLED_BY_USER
    assert "Assignments remain saved" in status.detail


def test_status_preserves_documented_platform_capability(tmp_path: Path) -> None:
    _, coordinator, _ = _coordinator(
        tmp_path,
        StatusHotkeys(
            HotkeyCapability.wayland("Global hotkeys are unavailable on Linux Wayland sessions.")
        ),
    )
    coordinator.set_enabled(True)

    status = coordinator.status()

    assert status.state is HotkeyStatusState.WAYLAND_UNSUPPORTED
    assert not status.available


def test_failed_registration_is_visible_as_pending_retry(tmp_path: Path) -> None:
    _, coordinator, sound = _coordinator(
        tmp_path, StatusHotkeys(HotkeyCapability(True, "Global hotkeys available"), fail=True)
    )
    coordinator.set_enabled(True)

    with pytest.raises(HotkeyRegistrationError):
        coordinator.assign_sound(sound.id, HotkeyBinding.parse("Ctrl+1"))

    status = coordinator.status()

    assert status.state is HotkeyStatusState.REGISTRATION_FAILED
    assert status.pending_retry
    assert "keyboard hook refused registration" in status.detail


def test_macos_permission_capability_remains_visible_when_enabled(tmp_path: Path) -> None:
    _, coordinator, _ = _coordinator(
        tmp_path,
        StatusHotkeys(
            HotkeyCapability(
                True,
                "Accessibility or Input Monitoring permission may be required.",
                HotkeyStatusState.MACOS_PERMISSION_REQUIRED,
            )
        ),
    )
    coordinator.set_enabled(True)

    status = coordinator.status()

    assert status.state is HotkeyStatusState.MACOS_PERMISSION_REQUIRED
    assert status.available
