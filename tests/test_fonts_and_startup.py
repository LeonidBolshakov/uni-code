"""Назначение произвольных семейств Qt и запуск/завершение приложения."""

import importlib
import json
import runpy
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit

import fonts as fonts_module
import window_class
from fonts import Fonts
from window_class import Window

ROOT = Path(__file__).resolve().parents[1]
# Общая фикстура window отключает загрузку шрифтов, но здесь нужен оригинал.
LOAD_FONTS = Window.load_fonts


@pytest.mark.parametrize("widget_class", [QLineEdit, QPlainTextEdit])
def test_setting_text_font_preserves_size_and_style(qtbot, widget_class):
    widget = widget_class()
    qtbot.addWidget(widget)
    font = widget.font()
    font.setPointSize(19)
    font.setBold(True)
    font.setItalic(True)
    widget.setFont(font)
    families = ["User Text", "Bundled Text", "Fallback Text"]

    Window.setting_text_font_widget(widget, families)

    actual = widget.font()
    assert actual.families() == families
    assert actual.pointSize() == 19
    assert actual.bold()
    assert actual.italic()


def test_load_fonts_assigns_all_families_to_both_inputs(window, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    loaded = Mock(spec=Fonts)
    text = ["User Text", "Bundled Text", "Extra Text"]
    emoji = ["User Emoji", "Bundled Emoji"]
    loaded.get_text_fonts_name_list.return_value = text
    loaded.get_emoji_fonts_name_list.return_value = emoji
    factory = Mock(return_value=loaded)
    database = Mock()
    monkeypatch.setattr(window_class, "Fonts", factory)
    monkeypatch.setattr(window_class, "QFontDatabase", database)

    LOAD_FONTS(window)

    factory.assert_called_once_with(window_class.PROJECT_ROOT)
    loaded.get_text_fonts_name_list.assert_called_once_with()
    loaded.get_emoji_fonts_name_list.assert_called_once_with()
    database.setApplicationEmojiFontFamilies.assert_called_once_with(emoji)
    assert window.txt_text_input.font().families() == text
    assert window.txt_char_input.font().families() == text


def test_configured_families_reach_widgets_and_emoji_registry(window, monkeypatch, tmp_path):
    """Настоящий Fonts читает JSON; подменяется только регистрация файлов в Qt."""
    records = [
        dict(font_family="Bundled Text", font_name="bundled.ttf"),
        dict(font_family="User Text", font_name="custom.otf", is_main=True),
        dict(font_family="Bundled Emoji", font_name="emoji.ttf", is_emoji=True),
        dict(font_family="User Emoji", font_name="custom-emoji.otf", is_emoji=True, is_main=True),
    ]
    directory = tmp_path / "fonts"
    directory.mkdir()
    (directory / "fonts_list.txt").write_text(json.dumps(records), encoding="utf-8")
    loader_database = Mock()
    loader_database.addApplicationFont.side_effect = [10, 11, 12, 13]
    loader_database.applicationFontFamilies.side_effect = [[r["font_family"]] for r in records]
    emoji_database = Mock()
    monkeypatch.setattr(fonts_module, "QFontDatabase", loader_database)
    monkeypatch.setattr(window_class, "QFontDatabase", emoji_database)
    monkeypatch.setattr(window_class, "PROJECT_ROOT", tmp_path)

    LOAD_FONTS(window)

    emoji_database.setApplicationEmojiFontFamilies.assert_called_once_with(
        ["User Emoji", "Bundled Emoji"]
    )
    for widget in (window.txt_text_input, window.txt_char_input):
        assert widget.font().families() == ["User Text", "Bundled Text"]


def test_constructor_calls_load_fonts(qtbot, monkeypatch):
    loader = Mock()
    monkeypatch.setattr(Window, "load_fonts", loader)
    widget = Window()
    qtbot.addWidget(widget)
    loader.assert_called_once_with()


@pytest.fixture
def preserve_font_database(qapp, monkeypatch):
    """Реальные проверки не оставляют зарегистрированные шрифты после себя."""
    original_add = QFontDatabase.addApplicationFont
    emoji_families = QFontDatabase.applicationEmojiFontFamilies()
    registered = []

    def register(path):
        font_id = original_add(path)
        if font_id != -1:
            registered.append(font_id)
        return font_id

    monkeypatch.setattr(QFontDatabase, "addApplicationFont", register)
    try:
        yield
    finally:
        QFontDatabase.setApplicationEmojiFontFamilies(emoji_families)
        for font_id in registered:
            QFontDatabase.removeApplicationFont(font_id)


def test_window_initializes_with_real_configured_fonts(qtbot, preserve_font_database):
    """Не привязан к поставке: проверяет все записи текущей конфигурации.

    Без конфигурации проверка пропускается. Если конфигурация есть, отсутствие
    или повреждение любого указанного файла считается ошибкой.
    """
    config = ROOT / "fonts" / "fonts_list.txt"
    if not config.is_file():
        pytest.skip("Не приложен fonts/fonts_list.txt для проверки реальных шрифтов")
    records = json.loads(config.read_text())

    def expected_families(is_emoji):
        selected = [r for r in records if r.get("is_emoji", False) == is_emoji]
        assert selected
        assert sum(bool(r.get("is_main", False)) for r in selected) == 1
        return [r["font_family"] for r in sorted(
            selected, key=lambda r: not r.get("is_main", False)
        )]

    widget = Window()
    qtbot.addWidget(widget)
    text = expected_families(False)
    assert widget.txt_text_input.font().families() == text
    assert widget.txt_char_input.font().families() == text
    assert QFontDatabase.applicationEmojiFontFamilies() == expected_families(True)


def test_main_creates_shows_and_exits(monkeypatch):
    module = importlib.import_module("unicode")
    app = Mock()
    app.exec.return_value = 7
    app_factory = Mock(return_value=app)
    window = Mock()
    window_factory = Mock(return_value=window)
    monkeypatch.setattr(module, "QApplication", app_factory)
    monkeypatch.setattr(module, "Window", window_factory)
    monkeypatch.setattr(module.sys, "argv", ["unicode.py"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 7
    app_factory.assert_called_once_with(["unicode.py"])
    window_factory.assert_called_once_with()
    window.show.assert_called_once_with()
    app.exec.assert_called_once_with()


def test_exit_button_requests_quit(window, monkeypatch, qtbot):
    from PyQt6.QtCore import Qt

    app = Mock()
    monkeypatch.setattr(window_class, "QApplication", app)
    qtbot.mouseClick(window.btn_exit, Qt.MouseButton.LeftButton)
    app.quit.assert_called_once_with()


def test_script_entrypoint(monkeypatch):
    from PyQt6 import QtWidgets

    app = Mock()
    app.exec.return_value = 0
    factory = Mock(return_value=Mock())
    monkeypatch.setattr(QtWidgets, "QApplication", Mock(return_value=app))
    monkeypatch.setattr(window_class, "Window", factory)
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "src" / "unicode.py"), run_name="__main__")
    assert exc.value.code == 0
    factory.return_value.show.assert_called_once_with()


def test_window_loads_ui_from_another_working_directory(qtbot, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Window, "load_fonts", lambda self: None)
    widget = Window()
    qtbot.addWidget(widget)
    widget.txt_char_in_utf.setPlainText("U+01F600")
    assert widget.txt_char_input.text() == "😀"
