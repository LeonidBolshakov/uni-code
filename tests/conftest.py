"""Подключение src и общая фикстура окна; pytest.ini не требуется."""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ["PYTEST_QT_API"] = "pyqt6"
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from window_class import Window


@pytest.fixture
def window(qtbot, monkeypatch):
    """Создать окно без зависимости тестов интерфейса от файлов шрифтов."""
    monkeypatch.setattr(Window, "tune_widgets", lambda self: None)
    widget = Window()
    qtbot.addWidget(widget)
    return widget
