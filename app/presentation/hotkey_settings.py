from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.application.hotkeys import HotkeyCoordinator
from app.domain.errors import HotkeyRegistrationError
from app.domain.models import HotkeyBinding
from app.presentation.hotkey_dialog import HotkeyCaptureDialog


class HotkeySettingsDialog(QDialog):
    def __init__(self, coordinator: HotkeyCoordinator, parent=None) -> None:
        super().__init__(parent)
        self.coordinator = coordinator
        self.setWindowTitle("Hotkey settings")
        self.panic_binding = self._current_panic()
        self.capability_label = QLabel(coordinator.capability().message)
        self.enabled_checkbox = QCheckBox("Enable global hotkeys")
        self.enabled_checkbox.setChecked(coordinator.is_enabled())
        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(0, 2000)
        self.debounce_spin.setSuffix(" ms debounce")
        self.debounce_spin.setValue(
            int(coordinator.service.settings.get_setting("hotkey_debounce_ms", "150"))
        )
        self.panic_label = QLabel(
            self.panic_binding.display_label if self.panic_binding else "Not assigned"
        )
        capture = QPushButton("Capture Panic Stop")
        capture.clicked.connect(self.capture_panic)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_panic)
        re_register = QPushButton("Re-register all")
        re_register.clicked.connect(self.reregister)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.capability_label)
        layout.addWidget(self.enabled_checkbox)
        layout.addWidget(self.debounce_spin)
        panic_row = QHBoxLayout()
        panic_row.addWidget(self.panic_label)
        panic_row.addWidget(capture)
        panic_row.addWidget(clear)
        layout.addLayout(panic_row)
        layout.addWidget(re_register)
        layout.addWidget(buttons)

    def capture_panic(self) -> None:
        binding = HotkeyCaptureDialog.capture(self)
        if binding is not None:
            self.panic_binding = binding
            self.panic_label.setText(binding.display_label)

    def clear_panic(self) -> None:
        self.panic_binding = None
        self.panic_label.setText("Not assigned")

    def reregister(self) -> None:
        errors = self.coordinator.re_register_all()
        self.capability_label.setText(
            "Re-registered all hotkeys." if not errors else " | ".join(errors)
        )

    def save(self) -> None:
        self.coordinator.service.settings.set_setting(
            "hotkey_debounce_ms", str(self.debounce_spin.value())
        )
        try:
            self.coordinator.assign_panic_stop(self.panic_binding)
            errors = self.coordinator.set_enabled(self.enabled_checkbox.isChecked())
        except HotkeyRegistrationError as error:
            QMessageBox.warning(self, "Hotkey registration failed", str(error))
            return
        self.capability_label.setText("Saved." if not errors else " | ".join(errors))
        self.accept()

    def _current_panic(self) -> HotkeyBinding | None:
        value = self.coordinator.service.settings.get_setting("panic_stop_hotkey", "")
        return HotkeyBinding.parse(value) if value else None
