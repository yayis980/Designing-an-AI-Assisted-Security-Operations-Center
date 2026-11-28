"""Entry point. Run with:  python main.py"""

import sys

from PySide6.QtWidgets import QApplication

from scanner_ui.main_window import MainWindow
from scanner_ui.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MCP Scanner")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
