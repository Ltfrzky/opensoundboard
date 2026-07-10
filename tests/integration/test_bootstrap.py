import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.bootstrap import create_context
from app.presentation.main_window import MainWindow


def test_bootstrap_creates_a_window_with_default_board(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    context = create_context(tmp_path)
    window = MainWindow(context.service, context.hotkeys)

    assert window.windowTitle() == "OpenSoundboard"
    assert window.board_list.count() == 1
    window.close()
    application.processEvents()


def test_injected_data_path_does_not_install_a_global_file_handler(tmp_path: Path) -> None:
    create_context(tmp_path)

    handlers = logging.getLogger("opensoundboard").handlers

    assert not [handler for handler in handlers if getattr(handler, "baseFilename", "")]
