from PySide6.QtCore import QObject, Signal


class HotkeyBridge(QObject):
    sound_triggered = Signal(int)
    panic_stop_requested = Signal()
    status_changed = Signal(str)

    def emit_sound(self, sound_id: int) -> None:
        self.sound_triggered.emit(sound_id)

    def emit_panic_stop(self) -> None:
        self.panic_stop_requested.emit()
