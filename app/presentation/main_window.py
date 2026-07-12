from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.application.hotkeys import HotkeyCoordinator
from app.application.service import ImportResult, SoundboardService
from app.domain.enums.playback import PlaybackMode
from app.domain.errors import HotkeyConflictError, HotkeyRegistrationError
from app.domain.interfaces import HotkeyService
from app.domain.models import HotkeyBinding, PlaybackSnapshot, Sound
from app.presentation.board_settings import BoardSettingsDialog
from app.presentation.hotkey_bridge import HotkeyBridge
from app.presentation.hotkey_dialog import HotkeyCaptureDialog
from app.presentation.material_icons import material_icon
from app.presentation.operator_strip import OperatorStrip
from app.presentation.settings_dialog import SettingsDialog
from app.presentation.sound_pad import SoundPad
from app.presentation.theme import SIGNAL_CONSOLE_STYLESHEET
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
        self.bridge.sound_triggered.connect(self._play)
        self.bridge.panic_stop_requested.connect(self.panic_stop)
        self.board_list = QListWidget()
        self.board_list.currentRowChanged.connect(self.refresh_sounds)
        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(10)
        for column in range(4):
            self._grid.setColumnStretch(column, 1)
        self._active_lanes: list[PlaybackSnapshot] = []
        self._active_sound_ids: set[int] = set()
        self._manage_mode = False
        self._activity_rail_pinned = False
        self.setWindowTitle("OpenSoundboard")
        self.resize(1280, 760)
        self.setMinimumSize(1000, 620)
        self.setAcceptDrops(True)
        self.setStyleSheet(SIGNAL_CONSOLE_STYLESHEET)
        self._build_ui()
        self.refresh_boards()
        self.coordinator.load_and_register_all()
        self._refresh_capability()
        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(100)
        self._playback_timer.timeout.connect(self.refresh_playback)
        self._playback_timer.start()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.operator_strip = OperatorStrip()
        self.operator_strip.import_requested.connect(self.import_files)
        self.operator_strip.master_volume_changed.connect(self._set_master_volume)
        self.operator_strip.playback_mode_changed.connect(self._set_playback_mode)
        self.operator_strip.hotkey_toggle_requested.connect(self.toggle_hotkeys)
        self.operator_strip.panic_stop_requested.connect(self.panic_stop)
        self.operator_strip.set_master_volume(self.service.master_volume())
        self.operator_strip.set_playback_mode(self.service.playback_mode())
        root_layout.addWidget(self.operator_strip)
        workspace = QWidget()
        workspace_layout = QHBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        workspace_layout.addWidget(self._build_board_rail())
        workspace_layout.addWidget(self._build_cue_workspace(), 1)
        workspace_layout.addWidget(self._build_playback_rail())
        root_layout.addWidget(workspace, 1)
        root_layout.addWidget(self._build_capability_bar())
        self.setCentralWidget(root)
        self._sync_activity_rail()

    def _build_board_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName("boardRail")
        rail.setFixedWidth(170)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(8)
        label = QLabel("BOARDS")
        label.setObjectName("eyebrow")
        layout.addWidget(label)
        layout.addWidget(self.board_list, 1)
        add = QPushButton("New Board")
        add.setObjectName("newBoardButton")
        add.setIcon(material_icon("add", off_color="#38d8ff"))
        add.setMinimumHeight(46)
        add.clicked.connect(self.create_board)
        layout.addWidget(add)
        settings = QPushButton("Settings")
        settings.setObjectName("settingsButton")
        settings.setIcon(material_icon("settings", off_color="#b7c4ce"))
        settings.setMinimumHeight(40)
        settings.clicked.connect(self.open_settings)
        layout.addWidget(settings)
        return rail

    def _build_cue_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QFrame()
        header.setObjectName("cueHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(26, 18, 26, 16)
        title_block = QHBoxLayout()
        title_block.setSpacing(8)
        self.board_title = QLabel("My Sounds")
        self.board_title.setObjectName("title")
        title_block.addWidget(self.board_title)
        self.pad_count = QLabel("0 pads")
        self.pad_count.setObjectName("padCount")
        title_block.addWidget(self.pad_count)
        header_layout.addLayout(title_block)
        header_layout.addStretch()
        self.activity_toggle_button = QPushButton("Activity (0)")
        self.activity_toggle_button.setObjectName("activityToggleButton")
        self.activity_toggle_button.setCheckable(True)
        self.activity_toggle_button.setIcon(material_icon("equalizer"))
        self.activity_toggle_button.setMinimumHeight(40)
        self.activity_toggle_button.clicked.connect(self.toggle_activity_rail)
        header_layout.addWidget(self.activity_toggle_button)
        drop = QPushButton("Drop audio here")
        drop.setObjectName("linkButton")
        drop.clicked.connect(self._request_managed_import)
        header_layout.addWidget(drop)
        self.manage_button = QPushButton("Manage sounds")
        self.manage_button.setObjectName("manageButton")
        self.manage_button.setCheckable(True)
        self.manage_button.setIcon(material_icon("edit"))
        self.manage_button.setMinimumHeight(40)
        self.manage_button.setToolTip("Show sound deletion controls")
        self.manage_button.clicked.connect(self.toggle_manage)
        header_layout.addWidget(self.manage_button)
        board_settings = QPushButton("Edit board")
        board_settings.setObjectName("boardSettingsButton")
        board_settings.setToolTip("Board settings")
        board_settings.clicked.connect(self.open_board_settings)
        header_layout.addWidget(board_settings)
        delete = QPushButton("Delete")
        delete.setObjectName("dangerButton")
        delete.clicked.connect(self.delete_current_board)
        header_layout.addWidget(delete)
        layout.addWidget(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("cueContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(26, 20, 26, 20)
        self.grid_host = QWidget()
        self.grid_host.setLayout(self._grid)
        content_layout.addWidget(self.grid_host)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        footer = QLabel("Managed library · files are copied into the local app data directory")
        footer.setObjectName("muted")
        footer.setContentsMargins(26, 10, 26, 10)
        layout.addWidget(footer)
        return workspace

    def _build_playback_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName("activityRail")
        rail.setFixedWidth(240)
        self.activity_rail = rail
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(8)
        heading = QHBoxLayout()
        title = QLabel("ACTIVE PLAYBACK")
        title.setObjectName("eyebrow")
        heading.addWidget(title)
        heading.addStretch()
        self.playback_summary = QLabel("0 lanes")
        self.playback_summary.setObjectName("laneCountLabel")
        heading.addWidget(self.playback_summary)
        layout.addLayout(heading)
        self.lane_host = QWidget()
        self.lane_layout = QVBoxLayout(self.lane_host)
        self.lane_layout.setContentsMargins(0, 0, 0, 0)
        self.lane_layout.setSpacing(8)
        layout.addWidget(self.lane_host)
        layout.addStretch(1)
        return rail

    def _build_capability_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("capabilityBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 8, 18, 8)
        self.capability_label = QLabel()
        self.capability_label.setObjectName("capabilityLabel")
        layout.addWidget(self.capability_label, 1)
        button = QPushButton("Hotkey settings")
        button.setObjectName("capabilityButton")
        button.setIcon(material_icon("arrow_forward"))
        button.clicked.connect(self.open_settings)
        layout.addWidget(button)
        return bar

    def refresh_boards(self) -> None:
        selected_id = self._current_board_id()
        boards = self.service.list_boards()
        self.board_list.blockSignals(True)
        self.board_list.clear()
        selected_row = 0
        for row, board in enumerate(boards):
            item = QListWidgetItem(material_icon(board.icon or "equalizer"), board.name)
            item.setData(Qt.ItemDataRole.UserRole, board.id)
            self.board_list.addItem(item)
            if board.id == selected_id:
                selected_row = row
        self.board_list.setCurrentRow(selected_row if boards else -1)
        self.board_list.blockSignals(False)
        self.refresh_sounds(self.board_list.currentRow())

    def refresh_sounds(self, row: int) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        boards = self.service.list_boards()
        if row < 0 or row >= len(boards):
            return
        board = boards[row]
        self.board_title.setText(board.name)
        sounds = self.service.list_sounds(board.id)
        self.pad_count.setText(f"{len(sounds)} pad{'s' if len(sounds) != 1 else ''}")
        for index, sound in enumerate(sounds):
            self._grid.addWidget(self._sound_pad(sound), index // 4, index % 4)

    def _sound_pad(self, sound: Sound) -> SoundPad:
        pad = SoundPad(
            sound,
            active=sound.id in self._active_sound_ids,
            arrange_mode=self._manage_mode,
        )
        pad.play_requested.connect(self._toggle_sound)
        pad.recover_requested.connect(self.recover_sound)
        pad.delete_requested.connect(self.delete_sound)
        pad.rename_requested.connect(self.rename_sound)
        pad.hotkey_requested.connect(self.assign_hotkey)
        pad.clear_hotkey_requested.connect(self.clear_hotkey)
        pad.move_requested.connect(self.move_sound)
        pad.volume_changed.connect(
            lambda sound_id, volume: self._update_sound(sound_id, volume=volume)
        )
        pad.loop_changed.connect(
            lambda sound_id, loop_enabled: self._update_sound(
                sound_id, loop_enabled=loop_enabled
            )
        )
        return pad

    def refresh_playback(self) -> None:
        lanes = self.service.active_lanes()
        for lane in lanes:
            if lane.duration_ms:
                self.service.record_duration(lane.sound_id, lane.duration_ms)
        active_ids = {lane.sound_id for lane in lanes}
        changed = active_ids != self._active_sound_ids
        self._active_lanes = lanes
        self._active_sound_ids = active_ids
        self._refresh_lanes()
        if changed:
            self.refresh_sounds(self.board_list.currentRow())

    def _refresh_lanes(self) -> None:
        while self.lane_layout.count():
            item = self.lane_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._sync_activity_rail()
        if not self._active_lanes:
            self.playback_summary.setText("0 lanes")
            empty = QLabel("Trigger a card to see live progress here.")
            empty.setObjectName("playbackEmptyLabel")
            empty.setWordWrap(True)
            self.lane_layout.addWidget(empty)
            return
        lane_count = len(self._active_lanes)
        self.playback_summary.setText(f"{lane_count} lane{'s' if lane_count != 1 else ''}")
        for lane in self._active_lanes:
            sound = self.service.get_sound(lane.sound_id)
            row = QFrame()
            row.setObjectName(f"playbackLane-{lane.lane_id}")
            row.setProperty("cssRole", "playbackLane")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 7, 8, 7)
            row_layout.setSpacing(8)
            play = QLabel()
            play.setPixmap(material_icon("play_arrow", size=18, off_color="#38d8ff").pixmap(18, 18))
            play.setFixedSize(32, 32)
            play.setObjectName("playbackLaneIcon")
            row_layout.addWidget(play)
            details = QVBoxLayout()
            details.setContentsMargins(0, 0, 0, 0)
            details.setSpacing(3)
            name = QLabel(sound.name)
            name.setObjectName(f"playbackName-{lane.lane_id}")
            details.addWidget(name)
            elapsed = self._format_clock(lane.position_ms)
            total = self._format_clock(lane.duration_ms) if lane.duration_ms else "--:--"
            timer = QLabel(f"{elapsed} / {total}")
            timer.setObjectName(f"playbackTime-{lane.lane_id}")
            timer.setProperty("cssRole", "playbackTime")
            details.addWidget(timer)
            progress = QProgressBar()
            progress.setObjectName(f"playbackProgress-{lane.lane_id}")
            progress.setRange(0, max(1, lane.duration_ms or 1))
            progress.setValue(min(lane.position_ms, progress.maximum()))
            progress.setTextVisible(False)
            details.addWidget(progress)
            row_layout.addLayout(details, 1)
            stop = QPushButton()
            stop.setObjectName(f"stopLane-{lane.lane_id}")
            stop.setIcon(material_icon("stop"))
            stop.setMinimumSize(40, 40)
            stop.setToolTip(f"Stop {sound.name}")
            stop.clicked.connect(lambda _=False, lane_id=lane.lane_id: self.stop_lane(lane_id))
            row_layout.addWidget(stop)
            self.lane_layout.addWidget(row)

    def toggle_manage(self) -> None:
        self._manage_mode = self.manage_button.isChecked()
        self.manage_button.setText("Done" if self._manage_mode else "Manage sounds")
        self.manage_button.setProperty("managing", self._manage_mode)
        self.manage_button.setToolTip(
            "Hide sound deletion controls" if self._manage_mode else "Show sound deletion controls"
        )
        self.manage_button.style().unpolish(self.manage_button)
        self.manage_button.style().polish(self.manage_button)
        self.refresh_sounds(self.board_list.currentRow())

    def toggle_activity_rail(self) -> None:
        self._activity_rail_pinned = not self._activity_rail_pinned
        self._sync_activity_rail()

    def _sync_activity_rail(self) -> None:
        lane_count = len(self._active_lanes)
        self.activity_rail.setVisible(bool(lane_count) or self._activity_rail_pinned)
        self.activity_toggle_button.blockSignals(True)
        self.activity_toggle_button.setChecked(self._activity_rail_pinned)
        self.activity_toggle_button.blockSignals(False)
        self.activity_toggle_button.setText(f"Activity ({lane_count})")
        self.activity_toggle_button.setToolTip(
            "Allow activity to collapse when idle"
            if self._activity_rail_pinned
            else "Keep activity visible when idle"
        )

    def create_board(self) -> None:
        name, accepted = QInputDialog.getText(self, "Create board", "Board name")
        if accepted and name.strip():
            board = self.service.create_board(name)
            self.refresh_boards()
            self._select_board(board.id)

    def rename_current_board(self) -> None:
        board = self._current_board()
        if board is None:
            return
        name, accepted = QInputDialog.getText(self, "Rename board", "Board name", text=board.name)
        if accepted and name.strip():
            self.service.rename_board(board.id, name)
            self.refresh_boards()

    def open_board_settings(self) -> None:
        board = self._current_board()
        if board is None:
            return
        if BoardSettingsDialog(self.service, board, self).exec():
            self.refresh_boards()

    def delete_current_board(self) -> None:
        board = self._current_board()
        if board is None:
            return
        confirmation = QMessageBox.question(
            self,
            "Delete board",
            f"Delete “{board.name}”? This is only allowed after its sounds have been moved "
            "or deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirmation is not QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_board(board.id)
        except Exception as error:
            QMessageBox.warning(self, "Cannot delete board", str(error))
        self.refresh_boards()

    def rename_sound(self, sound_id: int) -> None:
        sound = self.service.get_sound(sound_id)
        name, accepted = QInputDialog.getText(self, "Rename sound", "Name", text=sound.name)
        if not accepted or not name.strip():
            return
        self.service.update_sound(
            sound.id,
            name=name,
            board_id=sound.board_id,
            volume=sound.volume,
            loop_enabled=sound.loop_enabled,
        )
        self.refresh_sounds(self.board_list.currentRow())

    def move_sound(self, sound_id: int) -> None:
        sound = self.service.get_sound(sound_id)
        boards = self.service.list_boards()
        names = [board.name for board in boards]
        current_name = next(board.name for board in boards if board.id == sound.board_id)
        board_name, accepted = QInputDialog.getItem(
            self, "Move sound", "Board", names, names.index(current_name), False
        )
        if not accepted:
            return
        target = next(board for board in boards if board.name == board_name)
        self.service.update_sound(
            sound.id,
            name=sound.name,
            board_id=target.id,
            volume=sound.volume,
            loop_enabled=sound.loop_enabled,
        )
        self.refresh_sounds(self.board_list.currentRow())

    def delete_sound(self, sound_id: int) -> None:
        sound = self.service.get_sound(sound_id)
        if QMessageBox.question(
            self,
            "Delete sound",
            f"Delete “{sound.name}” and its hotkey assignment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        ) is QMessageBox.StandardButton.Yes:
            self.service.delete_sound(sound_id)
            self.refresh_sounds(self.board_list.currentRow())

    def import_files(self, copy_files: bool | None = None) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Import audio", "", "Audio files (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        board = self._current_board()
        if not paths or board is None:
            return
        if copy_files is None:
            choice, accepted = QInputDialog.getItem(
                self,
                "Import mode",
                "Store files",
                ["Copy into managed library", "Reference originals"],
                0,
                False,
            )
            if not accepted:
                return
            copy_files = choice == "Copy into managed library"
        result = self.service.import_files(board.id, [Path(path) for path in paths], copy_files)
        self._show_import_summary(result)
        self.refresh_sounds(self.board_list.currentRow())

    def _request_managed_import(self) -> None:
        self.import_files(True)

    def _show_import_summary(self, result: ImportResult) -> None:
        lines = [f"{len(result.imported)} imported"]
        if result.duplicates:
            lines.extend([f"Duplicate: {item}" for item in result.duplicates])
        if result.failures:
            lines.extend([f"Failed: {item}" for item in result.failures])
        message = "\n".join(lines)
        if result.failures:
            QMessageBox.warning(self, "Partial import", message)
        else:
            QMessageBox.information(self, "Import summary", message)

    def recover_sound(self, sound_id: int) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Recover media", "", "Audio files (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        if not path:
            return
        try:
            self.service.recover_sound(sound_id, Path(path))
        except Exception as error:
            QMessageBox.warning(self, "Recovery failed", str(error))
            return
        self.refresh_sounds(self.board_list.currentRow())

    def _toggle_sound(self, sound_id: int) -> None:
        if (
            sound_id in self._active_sound_ids
            and self.service.playback_mode() is PlaybackMode.STOP_PREVIOUS
        ):
            self.service.stop(sound_id)
        else:
            self._play(sound_id)
        self.refresh_playback()

    def _play(self, sound_id: int) -> None:
        try:
            self.service.play(sound_id)
        except Exception:
            logging.getLogger("opensoundboard").exception("Playback failed")
            QMessageBox.warning(self, "Playback failed", "This sound could not be played.")
        self.refresh_playback()

    def stop_lane(self, lane_id: str) -> None:
        self.service.stop_lane(lane_id)
        self.refresh_playback()

    def stop_all(self) -> None:
        self.service.stop_all()
        self.refresh_playback()

    def panic_stop(self) -> None:
        self.stop_all()

    def assign_hotkey(self, sound_id: int) -> None:
        binding = HotkeyCaptureDialog.capture(self)
        if binding is None:
            return
        try:
            self.coordinator.assign_sound(sound_id, binding)
        except HotkeyConflictError as error:
            replacement = QMessageBox.question(self, "Replace hotkey?", f"{error}. Replace it?")
            if replacement is not QMessageBox.StandardButton.Yes:
                return
            try:
                self.coordinator.assign_sound(sound_id, binding, replace_existing=True)
            except HotkeyRegistrationError as registration_error:
                QMessageBox.warning(self, "Hotkey registration failed", str(registration_error))
        except HotkeyRegistrationError as error:
            QMessageBox.warning(self, "Hotkey registration failed", str(error))
        self._refresh_capability()
        self.refresh_sounds(self.board_list.currentRow())

    def clear_hotkey(self, sound_id: int) -> None:
        self.coordinator.clear_sound(sound_id)
        self._refresh_capability()
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

    def open_settings(self) -> None:
        SettingsDialog(self.service, self.coordinator, self).exec()
        self._refresh_capability()
        self.refresh_sounds(self.board_list.currentRow())

    def _set_master_volume(self, value: int) -> None:
        self.service.set_master_volume(value)

    def _set_playback_mode(self, mode: PlaybackMode) -> None:
        self.service.set_playback_mode(mode)

    def _refresh_capability(self) -> None:
        status = self.coordinator.status()
        pending = " · assignments pending retry" if status.pending_retry else ""
        self.capability_label.setText(f"{status.headline} — {status.detail}{pending}")
        enabled = self.coordinator.is_enabled()
        self.operator_strip.set_hotkey_state(enabled)
        panic_value = self.service.settings.get_setting("panic_stop_hotkey", "")
        panic_label = HotkeyBinding.parse(panic_value).display_label if panic_value else None
        self.operator_strip.set_panic_shortcut(panic_label)

    def toggle_hotkeys(self) -> None:
        self.coordinator.set_enabled(not self.coordinator.is_enabled())
        self._refresh_capability()

    def _current_board(self):
        boards = self.service.list_boards()
        row = self.board_list.currentRow()
        return boards[row] if 0 <= row < len(boards) else None

    def _current_board_id(self) -> int | None:
        board = self._current_board()
        return board.id if board is not None else None

    def _select_board(self, board_id: int) -> None:
        for row, board in enumerate(self.service.list_boards()):
            if board.id == board_id:
                self.board_list.setCurrentRow(row)
                return

    @staticmethod
    def _format_duration(duration_ms: int | None) -> str:
        if not duration_ms:
            return "Duration unknown"
        seconds = duration_ms // 1000
        return f"{seconds // 60}:{seconds % 60:02d}"

    @staticmethod
    def _format_clock(duration_ms: int | None) -> str:
        seconds = max(0, duration_ms or 0) // 1000
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        board = self._current_board()
        if paths and board is not None:
            result = self.service.import_files(board.id, paths, copy_files=True)
            self._show_import_summary(result)
            self.refresh_sounds(self.board_list.currentRow())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._playback_timer.stop()
        self.coordinator.shutdown()
        super().closeEvent(event)
