"""Требования к обновлению символа при неизменной позиции курсора."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor


def test_delete_updates_character_at_unchanged_cursor(window, qtbot):
    """После Delete справа от курсора уже B; подробности должны обновиться."""
    window.txt_text_input.setPlainText("ABC")
    cursor = window.txt_text_input.textCursor()
    cursor.setPosition(0)
    window.txt_text_input.setTextCursor(cursor)
    window.on_text_input_cursor_changed()
    assert window.txt_char_input.toPlainText() == "A"
    qtbot.keyClick(window.txt_text_input, Qt.Key.Key_Delete)
    assert window.txt_text_input.toPlainText() == "BC"
    assert window.txt_total_chars.text() == "2"
    assert window.txt_char_input.toPlainText() == "B"
    assert window.txt_char_in_byte.toPlainText() == "42"


def test_programmatic_edit_without_cursor_movement(window):
    """Изменение документа отдельным курсором обновляет текущий символ."""
    window.txt_text_input.setPlainText("ABC")
    cursor = window.txt_text_input.textCursor()
    cursor.setPosition(0)
    window.txt_text_input.setTextCursor(cursor)
    window.on_text_input_cursor_changed()
    editor = QTextCursor(window.txt_text_input.document())
    editor.setPosition(0)
    editor.deleteChar()
    assert window.txt_text_input.textCursor().position() == 0
    assert window.txt_char_input.toPlainText() == "B"
