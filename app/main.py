import sys

from PySide6.QtWidgets import QApplication

from app.bootstrap import create_context
from app.presentation.main_window import MainWindow


def main() -> int:
    application = QApplication(sys.argv)
    context = create_context()
    window = MainWindow(context.service, context.hotkeys)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
