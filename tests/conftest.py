"""Подключение src и общая фикстура окна; pytest.ini не требуется."""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ["PYTEST_QT_API"] = "pyqt6"
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")



@pytest.fixture
def window(qtbot, monkeypatch):
    """Создать окно без зависимости тестов интерфейса от файлов шрифтов."""
    from window_class import Window

    monkeypatch.setattr(Window, "load_fonts", lambda self: None)
    widget = Window()
    qtbot.addWidget(widget)
    return widget
