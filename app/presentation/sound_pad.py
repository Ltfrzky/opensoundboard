from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import HotkeyBinding, Sound
from app.presentation.material_icons import material_icon


class SoundPad(QFrame):
    """A compact cue pad that emits intent while MainWindow owns application actions."""

    play_requested = Signal(int)
    recover_requested = Signal(int)
    delete_requested = Signal(int)
    rename_requested = Signal(int)
    hotkey_requested = Signal(int)
    clear_hotkey_requested = Signal(int)
    move_requested = Signal(int)
    volume_changed = Signal(int, int)
    loop_changed = Signal(int, bool)

    def __init__(
        self,
        sound: Sound,
        *,
        active: bool,
        arrange_mode: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.sound = sound
        self.setObjectName(f"soundPad-{sound.id}")
        self.setProperty("cssRole", "soundPad")
        self.setProperty("active", active)
        self.setProperty("missing", sound.is_missing)
        self.setProperty("arranging", arrange_mode)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName(f"padDelete-{sound.id}")
        self.delete_button.setProperty("cssRole", "padDelete")
        self.delete_button.setIcon(material_icon("delete", off_color="#ffdfe2"))
        self.delete_button.setMinimumHeight(40)
        self.delete_button.setVisible(arrange_mode)
        self.delete_button.setToolTip(f"Delete {sound.name}")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(sound.id))
        delete_row = QHBoxLayout()
        delete_row.setContentsMargins(0, 0, 0, 0)
        delete_row.addStretch()
        delete_row.addWidget(self.delete_button)
        layout.addLayout(delete_row)

        self.trigger = QToolButton()
        self.trigger.setObjectName(f"padTrigger-{sound.id}")
        self.trigger.setProperty("cssRole", "padTrigger")
        self.trigger.setText(sound.name)
        self.trigger.setIcon(
            material_icon("equalizer" if active else "volume_up", size=32, off_color="#dfe9ef")
        )
        self.trigger.setIconSize(QSize(32, 32))
        self.trigger.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.trigger.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.trigger.setMinimumHeight(92)
        self.trigger.setEnabled(not sound.is_missing and not arrange_mode)
        self.trigger.setToolTip(f"Play {sound.name}")
        self.trigger.setAccessibleName(f"Play {sound.name}")
        self.trigger.clicked.connect(lambda: self.play_requested.emit(sound.id))
        self.trigger.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.trigger.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.trigger, 1)

        if sound.is_missing:
            missing = QLabel("File missing")
            missing.setObjectName(f"padMissing-{sound.id}")
            missing.setProperty("cssRole", "padMissing")
            missing.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(missing)
            self.recover_button = QPushButton("Recover")
            self.recover_button.setObjectName(f"recoverButton-{sound.id}")
            self.recover_button.setProperty("cssRole", "padRecover")
            self.recover_button.setIcon(material_icon("restore", off_color="#f4b84a"))
            self.recover_button.setMinimumHeight(40)
            self.recover_button.clicked.connect(lambda: self.recover_requested.emit(sound.id))
            layout.addWidget(self.recover_button)
        else:
            mix = QHBoxLayout()
            mix.setContentsMargins(0, 0, 0, 0)
            mix.setSpacing(8)
            volume_label = QLabel("VOL")
            volume_label.setObjectName(f"padVolumeLabel-{sound.id}")
            volume_label.setProperty("cssRole", "padControlLabel")
            mix.addWidget(volume_label)
            self.volume_slider = QSlider(Qt.Orientation.Horizontal)
            self.volume_slider.setObjectName(f"padVolume-{sound.id}")
            self.volume_slider.setProperty("cssRole", "padVolume")
            self.volume_slider.setRange(0, 100)
            self.volume_slider.setValue(sound.volume)
            self.volume_slider.setAccessibleName(f"Volume for {sound.name}")
            self.volume_slider.sliderReleased.connect(
                lambda: self.volume_changed.emit(sound.id, self.volume_slider.value())
            )
            mix.addWidget(self.volume_slider, 1)
            self.loop_button = QPushButton("Loop")
            self.loop_button.setObjectName(f"padLoop-{sound.id}")
            self.loop_button.setProperty("cssRole", "padLoop")
            self.loop_button.setCheckable(True)
            self.loop_button.setChecked(sound.loop_enabled)
            self.loop_button.setMinimumSize(58, 40)
            self.loop_button.setAccessibleName(f"Loop {sound.name}")
            self.loop_button.toggled.connect(
                lambda enabled: self.loop_changed.emit(sound.id, enabled)
            )
            mix.addWidget(self.loop_button)
            layout.addLayout(mix)

        hotkey = HotkeyBinding.parse(sound.hotkey).display_label if sound.hotkey else "Unassigned"
        self.hotkey_button = QPushButton(hotkey)
        self.hotkey_button.setObjectName(f"padHotkey-{sound.id}")
        self.hotkey_button.setProperty("cssRole", "hotkeyKeycap")
        self.hotkey_button.setMinimumHeight(40)
        self.hotkey_button.setToolTip(
            "Change assigned hotkey" if sound.hotkey else "Assign a hotkey"
        )
        self.hotkey_button.setAccessibleName(f"Hotkey for {sound.name}")
        self.hotkey_button.clicked.connect(lambda: self.hotkey_requested.emit(sound.id))
        layout.addWidget(self.hotkey_button, alignment=Qt.AlignmentFlag.AlignHCenter)

    def context_menu(self) -> QMenu:
        menu = QMenu(self)
        rename = menu.addAction("Rename")
        rename.triggered.connect(lambda: self.rename_requested.emit(self.sound.id))
        hotkey = menu.addAction("Change hotkey")
        hotkey.triggered.connect(lambda: self.hotkey_requested.emit(self.sound.id))
        if self.sound.hotkey:
            clear = menu.addAction("Clear hotkey")
            clear.triggered.connect(lambda: self.clear_hotkey_requested.emit(self.sound.id))
        move = menu.addAction("Move to board…")
        move.triggered.connect(lambda: self.move_requested.emit(self.sound.id))
        return menu

    def _show_context_menu(self, position: QPoint) -> None:
        self.context_menu().exec(self.mapToGlobal(position))
