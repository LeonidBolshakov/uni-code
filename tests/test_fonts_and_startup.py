"""Контракты загрузки шрифтов и запуска/завершения приложения."""
import importlib
import importlib.util
import runpy
from pathlib import Path
from unittest.mock import Mock
import pytest
import window_class
from window_class import Window

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("font_id, families, error", [
    (-1, [], "Не удалось загрузить"), (17, ["Other"], "нет семейства"),
    (17, [], "нет семейства"), (17, ["Expected", "Other"], None),
])
def test_font_loader(monkeypatch, font_id, families, error):
    database = Mock()
    database.addApplicationFont.return_value = font_id
    database.applicationFontFamilies.return_value = families
    monkeypatch.setattr(window_class, "QFontDatabase", database)
    if error:
        with pytest.raises(RuntimeError, match=error):
            Window.load_font_and_get_family("test.ttf", "Expected")
    else:
        assert Window.load_font_and_get_family("test.ttf", "Expected") == "Expected"
    database.addApplicationFont.assert_called_once_with("test.ttf")
    if font_id == -1:
        database.applicationFontFamilies.assert_not_called()
    else:
        database.applicationFontFamilies.assert_called_once_with(font_id)


def test_tune_widgets_registers_emoji_and_sets_text_font(window, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # Фикстура отключает tune_widgets; выполняем оригинал из исходного класса отдельно.
    source = ROOT / "src" / "window_class.py"
    spec = importlib.util.spec_from_file_location("font_test_module", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loader = Mock(side_effect=["Noto Color Emoji", "JetBrains Mono"])
    monkeypatch.setattr(window, "load_font_and_get_family", loader)
    database = Mock()
    monkeypatch.setattr(module, "QFontDatabase", database)
    module.Window.tune_widgets(window)
    database.addApplicationEmojiFontFamily.assert_called_once_with("Noto Color Emoji")
    assert window.txt_text_input.font().family() == "JetBrains Mono"
    assert loader.call_count == 2
    assert [call.args for call in loader.call_args_list] == [
        (str(ROOT / "fonts" / "NotoColorEmoji.ttf"), "Noto Color Emoji"),
        (str(ROOT / "fonts" / "JetBrainsMono-Regular.ttf"), "JetBrains Mono"),
    ]


@pytest.mark.parametrize("filename, family", [
    ("NotoColorEmoji.ttf", "Noto Color Emoji"),
    ("JetBrainsMono-Regular.ttf", "JetBrains Mono"),
])
def test_real_bundled_font(qapp, filename, family):
    path = ROOT / "fonts" / filename
    if not path.is_file():
        pytest.skip(f"Не приложен файл шрифта: {path.name}")
    assert Window.load_font_and_get_family(str(path), family) == family


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


def test_window_initializes_with_real_fonts(qtbot, monkeypatch):
    missing = [name for name in ["NotoColorEmoji.ttf", "JetBrainsMono-Regular.ttf"]
               if not (ROOT / "fonts" / name).is_file()]
    if missing:
        pytest.skip("Не приложены шрифты: " + ", ".join(missing))
    monkeypatch.chdir(ROOT)
    widget = Window()
    qtbot.addWidget(widget)
    assert widget.txt_text_input.font().family() == "JetBrains Mono"


def test_window_loads_ui_from_another_working_directory(qtbot, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Window, "tune_widgets", lambda self: None)
    widget = Window()
    qtbot.addWidget(widget)
    widget.txt_char_in_utf.setPlainText("U+01F600")
    assert widget.txt_char_input.text() == "😀"
