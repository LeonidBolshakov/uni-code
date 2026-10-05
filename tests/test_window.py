"""Интеграционные проверки текста, символов, курсора и кнопок."""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QLabel, QPushButton
from window_class import Window


@pytest.mark.parametrize("text, count, byte_count, hex_bytes", [
    ("", 0, 0, ""), ("ABC", 3, 3, "41 42 43"),
    ("Ая", 2, 4, "d0 90 d1 8f"), ("😀", 1, 4, "f0 9f 98 80"),
    ("e\u0301", 1, 3, "65 cc 81"),
    ("👩‍💻", 1, 11, "f0 9f 91 a9 e2 80 8d f0 9f 92 bb"),
    ("A\nB", 3, 3, "41 0a 42"), ("A\tB", 3, 3, "41 09 42"),
    ("🇷🇺", 1, 8, "f0 9f 87 b7 f0 9f 87 ba"),
])
def test_text_statistics(window, text, count, byte_count, hex_bytes):
    window.txt_text_input.setPlainText("old")
    window.txt_text_input.setPlainText(text)
    assert window.txt_total_chars.text() == str(count)
    assert window.txt_total_byts.text() == str(byte_count)
    assert window.txt_text_bytes.toPlainText() == hex_bytes
    assert len(window.graphemes) == count


@pytest.mark.parametrize("symbol, codes, hex_bytes, name, category", [
    ("A", "u+0041", "41", "LATIN CAPITAL LETTER A", "Lu"),
    ("😀", "U+01f600", "f0 9f 98 80", "GRINNING FACE", "So"),
    ("e\u0301", "u+0065, u+0301", "65 cc 81",
     "LATIN SMALL LETTER E, COMBINING ACUTE ACCENT", "Ll, Mn"),
    ("👩‍💻", "U+01f469, u+200d, U+01f4bb",
     "f0 9f 91 a9 e2 80 8d f0 9f 92 bb", "WOMAN, ZERO WIDTH JOINER, PERSONAL COMPUTER", "So, Cf, So"),
])
def test_symbol_details(window, symbol, codes, hex_bytes, name, category):
    window.txt_char_input.setPlainText(symbol)
    assert window.txt_char_in_utf.toPlainText() == codes
    assert window.txt_char_in_byte.toPlainText() == hex_bytes
    assert window.txt_char_name.toPlainText() == name
    assert window.txt_char_category.toPlainText() == category
    assert window.txt_bytes_per_char.text() == str(len(bytes.fromhex(hex_bytes)))
    assert window.txt_char_message.text() == window.char_message_text


@pytest.mark.parametrize("symbol, highlighted", [
    ("A", False), (" ", False), ("👩‍💻", False), ("e\u0301", False),
    ("\n", True), ("\t", True), ("\u200d", True),
    ("\u00a0", False), ("\ufe0f", False), ("", False),
])
def test_printability_rule_and_style_reset(window, symbol, highlighted):
    window.txt_char_input.setPlainText("\u200d")
    window.txt_char_input.setPlainText(symbol)
    assert ("0, 255, 255" in window.txt_char_input.styleSheet()) is highlighted


def test_multiple_graphemes_warn_but_still_show_details(window):
    window.txt_char_input.setPlainText("AB")
    assert "только один символ" in window.txt_char_message.text()
    assert window.txt_char_in_byte.toPlainText() == "41 42"
    window.txt_char_input.setPlainText("A")
    assert window.txt_char_message.text() == window.char_message_text


def test_symbol_to_code_does_not_emit_code_change(window):
    spy = QSignalSpy(window.txt_char_in_utf.textChanged)
    window.txt_char_input.setPlainText("A")
    assert len(spy) == 0
    assert window.txt_char_in_byte.toPlainText() == "41"


def set_cursor(window, position, anchor=None):
    """Установить позиции в единицах UTF-16, как требует QTextCursor."""
    cursor = window.txt_text_input.textCursor()
    cursor.setPosition(position if anchor is None else anchor)
    if anchor is not None:
        cursor.setPosition(position, QTextCursor.MoveMode.KeepAnchor)
    window.txt_text_input.setTextCursor(cursor)


@pytest.mark.parametrize("position, number, char", [
    (0, "1", "A"), (1, "2", "😀"), (3, "3", "e\u0301"),
    (5, "4", "\n"), (6, "5", "B"), (7, "", ""),
])
def test_cursor_on_grapheme_boundaries(window, position, number, char):
    window.txt_text_input.setPlainText("A😀e\u0301\nB")
    set_cursor(window, 7)
    set_cursor(window, position)
    assert window.txt_num_symbol.text() == number
    assert window.txt_char_input.toPlainText() == char


@pytest.mark.parametrize("anchor, position, expected", [(0, 1, "B"), (3, 1, "B"), (0, 3, "")])
def test_selection_uses_active_cursor_and_preserves_selection(window, anchor, position, expected):
    window.txt_text_input.setPlainText("ABC")
    set_cursor(window, position, anchor)
    assert window.txt_char_input.toPlainText() == expected
    cursor = window.txt_text_input.textCursor()
    assert cursor.position() == position
    assert cursor.anchor() == anchor
    assert cursor.hasSelection()


def test_shift_right_selection(qtbot, window):
    window.txt_text_input.setPlainText("ABC")
    set_cursor(window, 0)
    qtbot.keyClick(window.txt_text_input, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    assert window.txt_char_input.toPlainText() == "B"
    assert window.txt_text_input.textCursor().selectedText() == "A"


def test_empty_text_cursor(window):
    window.on_text_input_cursor_changed()
    assert window.get_grapheme_index_at_cursor(0) is None
    assert window.txt_num_symbol.text() == ""
    assert window.txt_char_input.toPlainText() == ""


def test_clear_button_clears_every_output(qtbot, window):
    window.txt_text_input.setPlainText("ABC😀")
    window.txt_char_in_utf.setPlainText("u+ZZZZ")
    qtbot.mouseClick(window.btn_clear, Qt.MouseButton.LeftButton)
    for widget in window.findChildren((QLineEdit, QPlainTextEdit, QLabel)):
        if widget.objectName().startswith("txt_"):
            value = widget.toPlainText() if isinstance(widget, QPlainTextEdit) else widget.text()
            assert value == "", widget.objectName()
    assert window.graphemes == []
    assert window.char_in_utf_2_char_input is False
    window.txt_char_input.setPlainText("A")
    assert window.txt_char_in_byte.toPlainText() == "41"
    assert window.txt_char_message.text() == window.char_message_text


def test_clear_character_fields_preserves_source_and_blocks_signal(window):
    window.txt_char_in_utf.setPlainText("u+0041")
    spy = QSignalSpy(window.txt_char_input.textChanged)
    window.clear_char_fields()
    assert len(spy) == 0
    assert window.txt_char_input.toPlainText() == ""
    assert window.txt_char_in_utf.toPlainText() == "u+0041"
    assert window.txt_char_message.text() == ""
    assert window.txt_char_in_byte.toPlainText() == ""


def test_clear_fields_supports_three_types_and_ignores_other(qtbot):
    fields = [QLineEdit("A"), QPlainTextEdit("B"), QLabel("C"), QPushButton("D")]
    for field in fields:
        qtbot.addWidget(field)
    Window.clear_fields(fields)
    assert fields[0].text() == ""
    assert fields[1].toPlainText() == ""
    assert fields[2].text() == ""
    assert fields[3].text() == "D"


def test_character_bytes_method_reports_encoding_error(window):
    with pytest.raises(UnicodeEncodeError):
        window.create_text_field_bytes("\ud800")


def test_outputs_read_only(window):
    for name in ["txt_text_bytes", "txt_total_chars", "txt_total_byts", "txt_num_symbol",
                 "txt_char_in_byte", "txt_bytes_per_char", "txt_char_name", "txt_char_category"]:
        assert getattr(window, name).isReadOnly(), name
    assert not window.txt_text_input.isReadOnly()
    assert not window.txt_char_input.isReadOnly()
    assert not window.txt_char_in_utf.isReadOnly()


def test_character_input_is_plain_text_edit(window):
    assert isinstance(window.txt_char_input, QPlainTextEdit)


def test_enter_in_character_input_updates_details(window, qtbot):
    window.txt_char_input.setPlainText("A")
    cursor = window.txt_char_input.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    window.txt_char_input.setTextCursor(cursor)
    qtbot.keyClick(window.txt_char_input, Qt.Key.Key_Return)
    assert window.txt_char_input.toPlainText() == "A\n"
    assert window.txt_char_in_utf.toPlainText() == "u+0041, u+000a"
    assert window.txt_char_in_byte.toPlainText() == "41 0a"
    assert window.txt_bytes_per_char.text() == "2"
    assert "только один символ" in window.txt_char_message.text()


@pytest.mark.parametrize("source, expected, hex_bytes", [
    ("\u00a0", " ", "20"),
    ("\r\n", "\n", "0a"),
])
def test_character_input_uses_normalized_plain_text(window, source, expected, hex_bytes):
    """QPlainTextEdit.toPlainText нормализует NBSP и окончания строк."""
    window.txt_char_input.setPlainText(source)
    assert window.txt_char_input.toPlainText() == expected
    assert window.txt_char_in_byte.toPlainText() == hex_bytes
    assert window.txt_bytes_per_char.text() == "1"
