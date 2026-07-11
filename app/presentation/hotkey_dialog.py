from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from app.domain.errors import InvalidHotkeyError
from app.domain.models import HotkeyBinding


class HotkeyCaptureDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Capture hotkey")
        self.binding: HotkeyBinding | None = None
        self._label = QLabel("Press a key combination…")
        self._hint = QLabel("Use at least one modifier such as Ctrl, Alt, Shift, or Meta.")
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._hint)
        layout.addWidget(buttons)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.isAutoRepeat():
            return
        if event.key() in {
            Qt.Key.Key_Control,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Meta,
        }:
            self._hint.setText("Add a non-modifier key to complete the shortcut.")
            return
        sequence = QKeySequence(event.modifiers().value | int(event.key())).toString(
            QKeySequence.SequenceFormat.PortableText
        )
        try:
            self.binding = HotkeyBinding.parse(sequence)
        except InvalidHotkeyError as error:
            self.binding = None
            self._hint.setText(str(error))
            return
        self._label.setText(self.binding.display_label)
        self._hint.setText("Shortcut captured.")

    @classmethod
    def capture(cls, parent=None) -> HotkeyBinding | None:
        dialog = cls(parent)
        return dialog.binding if dialog.exec() == QDialog.DialogCode.Accepted else None
