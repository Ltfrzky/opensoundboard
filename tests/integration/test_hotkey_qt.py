from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.presentation.hotkey_bridge import HotkeyBridge
from app.presentation.hotkey_dialog import HotkeyCaptureDialog
from app.presentation.hotkey_settings import HotkeySettingsDialog


def test_hotkey_bridge_delivers_sound_signal_on_qt_loop() -> None:
    application = QApplication.instance() or QApplication([])
    bridge = HotkeyBridge()
    received: list[int] = []
    bridge.sound_triggered.connect(received.append)

    bridge.emit_sound(42)
    application.processEvents()

    assert received == [42]


def test_capture_dialog_records_portable_key_sequence() -> None:
    application = QApplication.instance() or QApplication([])
    dialog = HotkeyCaptureDialog()
    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_1,
        Qt.KeyboardModifier.ControlModifier,
    )

    dialog.keyPressEvent(event)
    application.processEvents()

    assert dialog.binding is not None
    assert dialog.binding.canonical == "Ctrl+1"
    dialog.close()


def test_hotkey_settings_dialog_exposes_capability_and_enable_switch(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    from app.application.hotkeys import HotkeyCoordinator
    from app.application.service import SoundboardService
    from app.infrastructure.database import SQLiteStore
    from app.infrastructure.file_library import FileLibrary
    from app.infrastructure.hotkeys.disabled import DisabledHotkeyService

    store = SQLiteStore(tmp_path / "soundboard.sqlite3")
    service = SoundboardService(store, store, store, FileLibrary(tmp_path / "library"), _Audio())
    dialog = HotkeySettingsDialog(HotkeyCoordinator(service, DisabledHotkeyService()))

    assert dialog.capability_label.text()
    assert not hasattr(dialog, "enabled_checkbox")
    dialog.close()


class _Audio:
    def play(self, sound, lane_id):
        return None

    def active_lanes(self):
        return []

    def stop_lane(self, lane_id):
        return None

    def stop_sound(self, sound_id):
        return None

    def stop_all(self):
        return None

    def set_master_volume(self, volume):
        return None
