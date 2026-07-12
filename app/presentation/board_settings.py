from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
)

from app.application.service import SoundboardService
from app.domain.models import Board
from app.presentation.material_icons import material_icon

BOARD_ICON_NAMES = ("equalizer", "apps", "mic", "layers", "volume_up")


class BoardSettingsDialog(QDialog):
    def __init__(self, service: SoundboardService, board: Board, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.board = board
        self.setWindowTitle("Board settings")
        layout = QFormLayout(self)
        self.name_input = QLineEdit(board.name)
        self.name_input.setObjectName("boardNameInput")
        self.icon_selector = QComboBox()
        self.icon_selector.setObjectName("boardIconSelector")
        for icon_name in BOARD_ICON_NAMES:
            self.icon_selector.addItem(material_icon(icon_name), icon_name)
        self.icon_selector.setCurrentText(
            board.icon if board.icon in BOARD_ICON_NAMES else "equalizer"
        )
        layout.addRow("Name", self.name_input)
        layout.addRow("Icon", self.icon_selector)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid board name", "Board name cannot be blank")
            return
        self.service.update_board(
            self.board.id,
            name=name,
            icon=self.icon_selector.currentText(),
        )
        self.accept()
