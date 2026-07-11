from pathlib import Path

import pytest

from app.application.hotkeys import HotkeyCoordinator
from app.application.service import SoundboardService
from app.domain.errors import HotkeyConflictError, HotkeyRegistrationError
from app.domain.interfaces import HotkeyCapability, HotkeyRegistrationResult
from app.domain.models import HotkeyBinding, Sound
from app.infrastructure.database import SQLiteStore
from app.infrastructure.file_library import FileLibrary


class FakeAudioEngine:
    def __init__(self) -> None:
        self.played: list[int] = []
        self.stop_all_calls = 0

    def play(self, sound: Sound, allow_overlap: bool) -> None:
        self.played.append(sound.id)

    def stop(self, sound_id: int) -> None:
        return None

    def stop_all(self) -> None:
        self.stop_all_calls += 1


class FakeHotkeyService:
    def __init__(self) -> None:
        self.callbacks: dict[str, object] = {}
        self.fail = False
        self.unregistered: list[str] = []

    def capability(self) -> HotkeyCapability:
        return HotkeyCapability(True, "Global hotkeys available")

    def register(self, binding, callback) -> HotkeyRegistrationResult:
        if self.fail:
            return HotkeyRegistrationResult(False, "registration failed")
        self.callbacks[binding.canonical] = callback
        return HotkeyRegistrationResult(True, "registered")

    def unregister(self, binding) -> None:
        self.unregistered.append(binding.canonical)
        self.callbacks.pop(binding.canonical, None)

    def unregister_all(self) -> None:
        self.callbacks.clear()

    def trigger(self, value: str) -> None:
        callback = self.callbacks[value]
        callback()


@pytest.fixture
def context(tmp_path: Path):
    store = SQLiteStore(tmp_path / "soundboard.sqlite3")
    audio = FakeAudioEngine()
    service = SoundboardService(store, store, store, FileLibrary(tmp_path / "library"), audio)
    board = store.list_boards()[0]
    sound = store.save_sound(Sound(0, board.id, "Horn", tmp_path / "horn.wav"))
    hotkeys = FakeHotkeyService()
    return service, audio, sound, hotkeys, HotkeyCoordinator(service, hotkeys)


def test_hotkey_triggers_sound_playback(context) -> None:
    service, audio, sound, hotkeys, coordinator = context
    coordinator.set_enabled(True)
    coordinator.assign_sound(sound.id, HotkeyBinding.parse("Ctrl+1"))

    hotkeys.trigger("Ctrl+1")

    assert audio.played == [sound.id]


def test_duplicate_binding_requires_explicit_replacement(context) -> None:
    service, _, sound, hotkeys, coordinator = context
    second = service.sounds.save_sound(Sound(0, sound.board_id, "Other", Path("other.wav")))
    coordinator.set_enabled(True)
    binding = HotkeyBinding.parse("Ctrl+1")
    coordinator.assign_sound(sound.id, binding)

    with pytest.raises(HotkeyConflictError):
        coordinator.assign_sound(second.id, binding)

    coordinator.assign_sound(second.id, binding, replace_existing=True)
    assert service.get_sound(sound.id).hotkey is None
    assert service.get_sound(second.id).hotkey == "Ctrl+1"


def test_registration_failure_preserves_assignment(context) -> None:
    _, _, sound, hotkeys, coordinator = context
    coordinator.set_enabled(True)
    hotkeys.fail = True

    with pytest.raises(HotkeyRegistrationError):
        coordinator.assign_sound(sound.id, HotkeyBinding.parse("Ctrl+1"))

    assert coordinator.service.get_sound(sound.id).hotkey == "Ctrl+1"


def test_panic_stop_and_debounce(context) -> None:
    service, audio, sound, hotkeys, coordinator = context
    coordinator.set_enabled(True)
    coordinator.assign_sound(sound.id, HotkeyBinding.parse("Ctrl+1"))
    coordinator.assign_panic_stop(HotkeyBinding.parse("Ctrl+2"))
    service.settings.set_setting("hotkey_debounce_ms", "10000")

    hotkeys.trigger("Ctrl+1")
    hotkeys.trigger("Ctrl+1")
    hotkeys.trigger("Ctrl+2")

    assert audio.played == [sound.id]
    assert audio.stop_all_calls == 1
