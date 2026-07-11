from app.domain.models import HotkeyBinding
from app.infrastructure.hotkeys.pynput_service import PynputHotkeyService


class FakeListener:
    def __init__(self, mapping) -> None:
        self.mapping = mapping
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_pynput_backend_registers_and_unregisters_with_injected_listener() -> None:
    listeners: list[FakeListener] = []

    def factory(mapping):
        listener = FakeListener(mapping)
        listeners.append(listener)
        return listener

    service = PynputHotkeyService(
        backend_factory=factory,
        platform_name="win32",
        environment={},
        dependency_available=True,
    )
    binding = HotkeyBinding.parse("Ctrl+1")
    callback_calls: list[int] = []

    result = service.register(binding, lambda: callback_calls.append(1))

    assert result.success is True
    assert listeners[-1].started is True
    assert "<ctrl>+1" in listeners[-1].mapping
    listeners[-1].mapping["<ctrl>+1"]()
    assert callback_calls == [1]

    service.unregister(binding)
    assert listeners[-1].stopped is True


def test_wayland_capability_is_explicitly_unavailable() -> None:
    service = PynputHotkeyService(
        backend_factory=lambda mapping: FakeListener(mapping),
        platform_name="linux",
        environment={"XDG_SESSION_TYPE": "wayland"},
        dependency_available=True,
    )

    capability = service.capability()

    assert capability.available is False
    assert "Wayland" in capability.message


def test_missing_dependency_returns_failure_without_importing_backend() -> None:
    service = PynputHotkeyService(
        backend_factory=None,
        platform_name="win32",
        environment={},
        dependency_available=False,
    )

    result = service.register(HotkeyBinding.parse("Ctrl+1"), lambda: None)

    assert result.success is False
    assert "pynput" in result.message
