from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QResizeEvent
from PySide6.QtWidgets import (
    QButtonGroup,
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

from app.domain.enums.playback import PlaybackMode
from app.presentation.material_icons import material_icon


class OperatorStrip(QFrame):
    import_requested = Signal(bool)
    master_volume_changed = Signal(int)
    playback_mode_changed = Signal(object)
    hotkey_toggle_requested = Signal()
    panic_stop_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("operatorStrip")
        self.setFixedHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._compact = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        self.import_button = self._build_import_button()
        layout.addWidget(self.import_button)
        layout.addWidget(self._separator())

        volume_group = self._group("Master Volume")
        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setSpacing(8)
        volume_icon = QLabel()
        volume_icon.setObjectName("volumeIcon")
        volume_icon.setAccessibleName("Master volume")
        volume_icon.setPixmap(material_icon("volume_up").pixmap(16, 16))
        volume_row.addWidget(volume_icon)
        self.master_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.master_volume_slider.setObjectName("masterVolumeSlider")
        self.master_volume_slider.setRange(0, 100)
        self.master_volume_slider.setMinimumWidth(108)
        self.master_volume_slider.setMaximumWidth(164)
        self.master_volume_slider.setAccessibleName("Master volume")
        self.master_volume_slider.valueChanged.connect(self._on_master_volume_changed)
        volume_row.addWidget(self.master_volume_slider, 1)
        self.master_volume_value = QLabel("100%")
        self.master_volume_value.setObjectName("masterVolumeValue")
        self.master_volume_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.master_volume_value.setFixedWidth(38)
        volume_row.addWidget(self.master_volume_value)
        volume_group.layout().addLayout(volume_row)
        layout.addWidget(volume_group, 1)
        layout.addWidget(self._separator())

        playback_group = self._group("Playback Mode")
        segments = QFrame()
        segments.setObjectName("playbackSegments")
        segment_layout = QHBoxLayout(segments)
        segment_layout.setContentsMargins(0, 0, 0, 0)
        segment_layout.setSpacing(0)
        self.playback_button_group = QButtonGroup(self)
        self.playback_button_group.setExclusive(True)
        self.playback_buttons: dict[PlaybackMode, QPushButton] = {}
        segment_specs = (
            (PlaybackMode.OVERLAP, "Overlap", "layers", "playbackModeOverlapButton", 82),
            (
                PlaybackMode.STOP_PREVIOUS,
                "Stop Previous",
                "stop_circle",
                "playbackModeStopPreviousButton",
                104,
            ),
            (
                PlaybackMode.STOP_SAME_SOUND,
                "Stop Same",
                "repeat_one",
                "playbackModeStopSameButton",
                92,
            ),
        )
        for index, (mode, text, icon_name, object_name, width) in enumerate(segment_specs):
            button = QPushButton(text)
            button.setObjectName(object_name)
            button.setIcon(material_icon(icon_name))
            button.setProperty("cssRole", "playbackModeButton")
            button.setProperty(
                "segmentPosition",
                "first" if index == 0 else "last" if index == len(segment_specs) - 1 else "middle",
            )
            button.setCheckable(True)
            button.setMinimumWidth(width)
            button.setMinimumHeight(40)
            button.setAccessibleName(text)
            button.clicked.connect(
                lambda _checked=False, selected=mode: self.playback_mode_changed.emit(selected)
            )
            self.playback_button_group.addButton(button)
            self.playback_buttons[mode] = button
            segment_layout.addWidget(button)
        playback_group.layout().addWidget(segments)
        layout.addWidget(playback_group)

        layout.addStretch(1)

        hotkey_group = self._group("Global")
        self.hotkey_toggle_button = QPushButton("Hotkeys Off")
        self.hotkey_toggle_button.setObjectName("hotkeyToggleButton")
        self.hotkey_toggle_button.setCheckable(True)
        self.hotkey_toggle_button.setMinimumSize(96, 40)
        self.hotkey_toggle_button.setIcon(
            material_icon("keyboard", off_color="#91a1b2", on_color="#38d8ff")
        )
        self.hotkey_toggle_button.clicked.connect(
            lambda _checked=False: self.hotkey_toggle_requested.emit()
        )
        hotkey_group.layout().addWidget(self.hotkey_toggle_button)
        layout.addWidget(hotkey_group)

        self.panic_stop_button = QPushButton("PANIC STOP\nNo hotkey")
        self.panic_stop_button.setObjectName("panicStopButton")
        self.panic_stop_button.setMinimumSize(132, 44)
        self.panic_stop_button.setIcon(material_icon("stop_circle", off_color="#ff626b"))
        self.panic_stop_button.setAccessibleName("Panic Stop")
        self.panic_stop_button.setToolTip("Immediately stop every active playback lane")
        self.panic_stop_button.clicked.connect(
            lambda _checked=False: self.panic_stop_requested.emit()
        )
        layout.addWidget(self.panic_stop_button)

        self.set_master_volume(100)
        self.set_playback_mode(PlaybackMode.STOP_PREVIOUS)
        self.set_hotkey_state(False)

    def _build_import_button(self) -> QToolButton:
        button = QToolButton()
        button.setObjectName("importButton")
        button.setText("Import")
        button.setIcon(material_icon("file_upload"))
        button.setAccessibleName("Import audio")
        button.setToolTip("Import audio into the managed library")
        button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        button.setMinimumSize(108, 40)
        button.clicked.connect(lambda _checked=False: self.import_requested.emit(True))

        menu = QMenu(button)
        copy_action = QAction("Copy into managed library", menu)
        copy_action.setData(True)
        copy_action.triggered.connect(lambda _checked=False: self.import_requested.emit(True))
        reference_action = QAction("Reference originals", menu)
        reference_action.setData(False)
        reference_action.triggered.connect(lambda _checked=False: self.import_requested.emit(False))
        menu.addAction(copy_action)
        menu.addAction(reference_action)
        button.setMenu(menu)
        return button

    @staticmethod
    def _separator() -> QFrame:
        separator = QFrame()
        separator.setObjectName("operatorSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedSize(1, 36)
        return separator

    @staticmethod
    def _group(label: str) -> QWidget:
        group = QWidget()
        group.setProperty("cssRole", "operatorGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        heading = QLabel(label)
        heading.setObjectName("operatorLabel")
        layout.addWidget(heading)
        return group

    def _on_master_volume_changed(self, value: int) -> None:
        self.master_volume_value.setText(f"{value}%")
        self.master_volume_changed.emit(value)

    def set_master_volume(self, value: int) -> None:
        self.master_volume_slider.setValue(value)
        self.master_volume_value.setText(f"{value}%")

    def set_playback_mode(self, mode: PlaybackMode) -> None:
        self.playback_buttons[mode].setChecked(True)

    def set_hotkey_state(self, enabled: bool) -> None:
        self.hotkey_toggle_button.blockSignals(True)
        self.hotkey_toggle_button.setChecked(enabled)
        self.hotkey_toggle_button.blockSignals(False)
        label = "On" if enabled else "Off"
        self.hotkey_toggle_button.setText(label if self._compact else f"Hotkeys {label}")
        self.hotkey_toggle_button.setProperty("hotkeyState", "on" if enabled else "off")
        action = "Disable" if enabled else "Enable"
        description = f"{action} global hotkeys"
        self.hotkey_toggle_button.setToolTip(description)
        self.hotkey_toggle_button.setAccessibleName(description)
        self._refresh_style(self.hotkey_toggle_button)

    def set_panic_shortcut(self, shortcut: str | None) -> None:
        self.panic_stop_button.setText(f"PANIC STOP\n{shortcut or 'No hotkey'}")

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._set_compact(event.size().width() < 1120)

    def _set_compact(self, compact: bool) -> None:
        if compact == self._compact:
            return
        self._compact = compact
        self.import_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
            if compact
            else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.import_button.setMinimumWidth(40 if compact else 108)
        self.hotkey_toggle_button.setMinimumWidth(64 if compact else 96)
        self.set_hotkey_state(self.hotkey_toggle_button.isChecked())
        self.updateGeometry()

    @staticmethod
    def _refresh_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
