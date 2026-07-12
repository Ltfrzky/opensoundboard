from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.application.hotkeys import HotkeyCoordinator
from app.application.service import SoundboardService
from app.domain.errors import HotkeyConflictError, HotkeyRegistrationError
from app.domain.models import HotkeyBinding
from app.presentation.hotkey_dialog import HotkeyCaptureDialog


class SettingsDialog(QDialog):
    def __init__(
        self, service: SoundboardService, coordinator: HotkeyCoordinator, parent=None
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.coordinator = coordinator
        self.setWindowTitle("Settings")
        self.resize(540, 360)

        layout = QHBoxLayout(self)
        self.category_list = QListWidget()
        self.category_list.setObjectName("settingsCategories")
        self.category_list.addItems(["General", "Hotkeys"])
        self.category_list.setFixedWidth(120)
        layout.addWidget(self.category_list)

        content = QVBoxLayout()
        self.pages = QStackedWidget()
        self.general_page, self.general_page_text = self._build_general_page()
        self.hotkey_page = self._build_hotkey_page()
        self.pages.addWidget(self.general_page)
        self.pages.addWidget(self.hotkey_page)
        content.addWidget(self.pages)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        content.addWidget(buttons)
        layout.addLayout(content, 1)
        self.category_list.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.category_list.setCurrentRow(0)

    def _build_general_page(self) -> tuple[QWidget, QLabel]:
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("General")
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)
        text = QLabel(
            "OpenSoundboard stores its database and managed audio locally.\n\n"
            f"Library location\n{self.service.library.library_path}"
        )
        text.setObjectName("generalSettingsInfo")
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()
        return page, text

    def _build_hotkey_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Hotkeys")
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)
        self.hotkey_capability_label = QLabel(self._status_text())
        self.hotkey_capability_label.setWordWrap(True)
        layout.addWidget(self.hotkey_capability_label)
        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(0, 2000)
        self.debounce_spin.setSuffix(" ms debounce")
        self.debounce_spin.setValue(
            int(self.service.settings.get_setting("hotkey_debounce_ms", "150"))
        )
        layout.addWidget(self.debounce_spin)
        self.panic_binding = self._current_panic()
        self.panic_label = QLabel(
            self.panic_binding.display_label if self.panic_binding else "Not assigned"
        )
        capture = QPushButton("Capture Panic Stop")
        capture.clicked.connect(self.capture_panic)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_panic)
        self.reregister_button = QPushButton("Re-register all")
        self.reregister_button.setObjectName("reRegisterHotkeysButton")
        self.reregister_button.clicked.connect(self.reregister)
        row = QHBoxLayout()
        row.addWidget(self.panic_label)
        row.addWidget(capture)
        row.addWidget(clear)
        layout.addLayout(row)
        layout.addWidget(self.reregister_button)
        layout.addStretch()
        return page

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
        self.hotkey_capability_label.setText(
            "Re-registered all hotkeys." if not errors else " | ".join(errors)
        )

    def save(self) -> None:
        self.service.settings.set_setting("hotkey_debounce_ms", str(self.debounce_spin.value()))
        try:
            self.coordinator.assign_panic_stop(self.panic_binding)
            errors = self.coordinator.re_register_all() if self.coordinator.is_enabled() else []
        except (HotkeyConflictError, HotkeyRegistrationError) as error:
            QMessageBox.warning(self, "Hotkey registration failed", str(error))
            return
        self.hotkey_capability_label.setText("Saved." if not errors else " | ".join(errors))
        self.accept()

    def _status_text(self) -> str:
        status = self.coordinator.status()
        pending = " Assignments are pending retry." if status.pending_retry else ""
        return f"{status.headline}. {status.detail}{pending}"

    def _current_panic(self) -> HotkeyBinding | None:
        value = self.service.settings.get_setting("panic_stop_hotkey", "")
        return HotkeyBinding.parse(value) if value else None
