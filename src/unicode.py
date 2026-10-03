"""Точка запуска графического анализатора Unicode."""

import sys

from PyQt6.QtWidgets import QApplication

from window_class import Window


def main():
    """Создать приложение и окно, запустить цикл Qt и завершить процесс его кодом."""
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
