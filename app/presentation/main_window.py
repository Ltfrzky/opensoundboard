from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.application.hotkeys import HotkeyCoordinator
from app.application.service import SoundboardService
from app.domain.errors import HotkeyConflictError, HotkeyRegistrationError
from app.domain.interfaces import HotkeyService
from app.presentation.hotkey_bridge import HotkeyBridge
from app.presentation.hotkey_dialog import HotkeyCaptureDialog
from app.presentation.hotkey_settings import HotkeySettingsDialog
from app.presentation.viewmodel import SoundboardViewModel


class MainWindow(QMainWindow):
    def __init__(self, service: SoundboardService, hotkeys: HotkeyService) -> None:
        super().__init__()
        self.service = service
        self.viewmodel = SoundboardViewModel(service)
        self.hotkeys = hotkeys
        self.bridge = HotkeyBridge()
        self.coordinator = HotkeyCoordinator(
            service,
            hotkeys,
            sound_trigger=self.bridge.emit_sound,
            panic_trigger=self.bridge.emit_panic_stop,
        )
        self.bridge.sound_triggered.connect(self.service.play)
        self.bridge.panic_stop_requested.connect(self.service.stop_all)
        self.board_list = QListWidget()
        self.board_list.currentRowChanged.connect(self.refresh_sounds)
        self._grid = QGridLayout()
        self.setWindowTitle("OpenSoundboard")
        self.resize(1080, 680)
        self.setAcceptDrops(True)
        self._build_ui()
        self.refresh_boards()
        self.coordinator.load_and_register_all()

    def _build_ui(self) -> None:
        toolbar = QToolBar("Controls")
        self.addToolBar(toolbar)
        import_button = QPushButton("Import")
        import_button.clicked.connect(self.import_files)
        toolbar.addWidget(import_button)
        self.overlap_toggle = QCheckBox("Allow overlap")
        self.overlap_toggle.setChecked(self.service.playback_mode().value == "overlap")
        self.overlap_toggle.toggled.connect(self.viewmodel.set_overlap)
        toolbar.addWidget(self.overlap_toggle)
        toolbar.addWidget(QLabel(" Master volume"))
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(100)
        volume.valueChanged.connect(self._set_master_volume)
        toolbar.addWidget(volume)
        stop_all = QPushButton("Stop All")
        stop_all.clicked.connect(self.service.stop_all)
        toolbar.addWidget(stop_all)
        hotkey_settings = QPushButton("Hotkeys")
        hotkey_settings.clicked.connect(self.open_hotkey_settings)
        toolbar.addWidget(hotkey_settings)

        central = QWidget()
        layout = QHBoxLayout(central)
        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("BOARDS"))
        sidebar.addWidget(self.board_list)
        add_board = QPushButton("New board")
        add_board.clicked.connect(self.create_board)
        sidebar.addWidget(add_board)
        rename_board = QPushButton("Rename board")
        rename_board.clicked.connect(self.rename_current_board)
        sidebar.addWidget(rename_board)
        delete_board = QPushButton("Delete board")
        delete_board.clicked.connect(self.delete_current_board)
        sidebar.addWidget(delete_board)
        layout.addLayout(sidebar, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setLayout(self._grid)
        scroll.setWidget(content)
        layout.addWidget(scroll, 4)
        self.setCentralWidget(central)
        self.statusBar().showMessage(self.hotkeys.capability().message)

    def refresh_boards(self) -> None:
        self.board_list.clear()
        for board in self.service.list_boards():
            self.board_list.addItem(board.name)
        if self.board_list.count():
            self.board_list.setCurrentRow(0)

    def refresh_sounds(self, row: int) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        boards = self.service.list_boards()
        if row < 0 or row >= len(boards):
            return
        for index, sound in enumerate(self.service.list_sounds(boards[row].id)):
            self._grid.addWidget(self._sound_card(sound), index // 3, index % 3)
        self.statusBar().showMessage(
            f"{self.hotkeys.capability().message}  |  {self._grid.count()} sounds"
        )

    def _sound_card(self, sound) -> QWidget:
        card = QWidget()
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(f"<b>{sound.name}</b>"))
        layout.addWidget(QLabel(f"Hotkey: {sound.hotkey or 'Not assigned'}"))
        state = "Missing file" if sound.is_missing else sound.file_path.suffix.upper().lstrip(".")
        layout.addWidget(QLabel(state))
        controls = QHBoxLayout()
        play = QPushButton("Play")
        play.setEnabled(not sound.is_missing)
        play.clicked.connect(lambda: self._play(sound.id))
        controls.addWidget(play)
        stop = QPushButton("Stop")
        stop.clicked.connect(lambda: self.service.stop(sound.id))
        controls.addWidget(stop)
        layout.addLayout(controls)
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(sound.volume)
        volume.valueReleased.connect(lambda: self._update_sound(sound.id, volume=volume.value()))
        layout.addWidget(volume)
        loop = QCheckBox("Loop")
        loop.setChecked(sound.loop_enabled)
        loop.toggled.connect(lambda enabled: self._update_sound(sound.id, loop_enabled=enabled))
        layout.addWidget(loop)
        edit = QPushButton("Edit")
        edit.clicked.connect(lambda: self.edit_sound(sound.id))
        layout.addWidget(edit)
        delete = QPushButton("Delete")
        delete.clicked.connect(lambda: self.delete_sound(sound.id))
        layout.addWidget(delete)
        hotkey = QPushButton("Set hotkey")
        hotkey.clicked.connect(lambda: self.assign_hotkey(sound.id))
        layout.addWidget(hotkey)
        if sound.hotkey:
            clear_hotkey = QPushButton("Clear hotkey")
            clear_hotkey.clicked.connect(lambda: self.clear_hotkey(sound.id))
            layout.addWidget(clear_hotkey)
        return card

    def create_board(self) -> None:
        name, accepted = QInputDialog.getText(self, "New board", "Board name")
        if accepted and name.strip():
            self.service.create_board(name)
            self.refresh_boards()

    def rename_current_board(self) -> None:
        row = self.board_list.currentRow()
        boards = self.service.list_boards()
        if row < 0 or row >= len(boards):
            return
        board = boards[row]
        name, accepted = QInputDialog.getText(self, "Rename board", "Board name", text=board.name)
        if accepted and name.strip():
            self.service.rename_board(board.id, name)
            self.refresh_boards()

    def delete_current_board(self) -> None:
        row = self.board_list.currentRow()
        boards = self.service.list_boards()
        if row < 0 or row >= len(boards):
            return
        if (
            QMessageBox.question(self, "Delete board", "Delete this empty board?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.service.delete_board(boards[row].id)
        except Exception as error:
            QMessageBox.warning(self, "Cannot delete board", str(error))
        self.refresh_boards()

    def edit_sound(self, sound_id: int) -> None:
        sound = self.service.get_sound(sound_id)
        names = [board.name for board in self.service.list_boards()]
        name, accepted = QInputDialog.getText(self, "Edit sound", "Name", text=sound.name)
        if not accepted or not name.strip():
            return
        board_name, accepted = QInputDialog.getItem(
            self,
            "Move sound",
            "Board",
            names,
            names.index(
                next(
                    board.name for board in self.service.list_boards() if board.id == sound.board_id
                )
            ),
            False,
        )
        if not accepted:
            return
        board_id = next(
            board.id for board in self.service.list_boards() if board.name == board_name
        )
        self.service.update_sound(
            sound.id,
            name=name,
            board_id=board_id,
            volume=sound.volume,
            loop_enabled=sound.loop_enabled,
        )
        self.refresh_sounds(self.board_list.currentRow())

    def delete_sound(self, sound_id: int) -> None:
        if (
            QMessageBox.question(self, "Delete sound", "Delete this sound?")
            == QMessageBox.StandardButton.Yes
        ):
            self.service.delete_sound(sound_id)
            self.refresh_sounds(self.board_list.currentRow())

    def _update_sound(
        self, sound_id: int, *, volume: int | None = None, loop_enabled: bool | None = None
    ) -> None:
        sound = self.service.get_sound(sound_id)
        self.service.update_sound(
            sound.id,
            name=sound.name,
            board_id=sound.board_id,
            volume=sound.volume if volume is None else volume,
            loop_enabled=sound.loop_enabled if loop_enabled is None else loop_enabled,
        )

    def import_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Import audio", "", "Audio files (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        if not paths or self.board_list.currentRow() < 0:
            return
        choice, accepted = QInputDialog.getItem(
            self,
            "Import mode",
            "Store files",
            ["Copy into library", "Reference originals"],
            0,
            False,
        )
        if not accepted:
            return
        board = self.service.list_boards()[self.board_list.currentRow()]
        result = self.service.import_files(
            board.id, [Path(path) for path in paths], choice == "Copy into library"
        )
        if result.skipped:
            QMessageBox.warning(self, "Import summary", "\n".join(result.skipped))
        self.refresh_sounds(self.board_list.currentRow())

    def _play(self, sound_id: int) -> None:
        try:
            self.service.play(sound_id)
        except Exception:
            logging.getLogger("opensoundboard").exception("Playback failed")
            QMessageBox.warning(self, "Playback failed", "This sound could not be played.")

    def assign_hotkey(self, sound_id: int) -> None:
        binding = HotkeyCaptureDialog.capture(self)
        if binding is None:
            return
        try:
            self.coordinator.assign_sound(sound_id, binding)
        except HotkeyConflictError as error:
            if (
                QMessageBox.question(self, "Replace hotkey?", f"{error}. Replace it?")
                != QMessageBox.StandardButton.Yes
            ):
                return
            try:
                self.coordinator.assign_sound(sound_id, binding, replace_existing=True)
            except HotkeyRegistrationError as registration_error:
                QMessageBox.warning(self, "Hotkey registration failed", str(registration_error))
                return
        except HotkeyRegistrationError as error:
            QMessageBox.warning(self, "Hotkey registration failed", str(error))
            return
        self.refresh_sounds(self.board_list.currentRow())

    def clear_hotkey(self, sound_id: int) -> None:
        self.coordinator.clear_sound(sound_id)
        self.refresh_sounds(self.board_list.currentRow())

    def open_hotkey_settings(self) -> None:
        HotkeySettingsDialog(self.coordinator, self).exec()
        self.refresh_sounds(self.board_list.currentRow())

    def _set_master_volume(self, value: int) -> None:
        setter = getattr(self.service.audio_engine, "set_master_volume", None)
        if setter:
            setter(value)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if paths and self.board_list.currentRow() >= 0:
            board = self.service.list_boards()[self.board_list.currentRow()]
            self.service.import_files(board.id, paths, copy_files=True)
            self.refresh_sounds(self.board_list.currentRow())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.coordinator.shutdown()
        super().closeEvent(event)
