"""Ввод кода через реальные сигналы Qt и регрессии синхронизации."""

import pytest
from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtTest import QSignalSpy


@pytest.mark.parametrize(
    "code, char, hex_bytes",
    [
        ("u+0041", "A", "41"),
        ("u+0410", "А", "d0 90"),
        ("u+00e9", "é", "c3 a9"),
        ("u+00E9", "é", "c3 a9"),
        ("u+0000", "\x00", "00"),
        ("u+000A", "\n", "0a"),
        ("u+D7FF", "\ud7ff", "ed 9f bf"),
        ("u+E000", "\ue000", "ee 80 80"),
        ("u+FFFF", "\uffff", "ef bf bf"),
        ("U+000041", "A", "41"),
        ("U+010000", "\U00010000", "f0 90 80 80"),
        ("U+01F600", "😀", "f0 9f 98 80"),
        ("U+10FFFF", "\U0010ffff", "f4 8f bf bf"),
    ],
)
def test_valid_code(window, code, char, hex_bytes):
    print(code)
    window.txt_char_in_utf.setPlainText(code)
    assert window.txt_char_input.toPlainText() == char
    assert window.txt_char_in_byte.toPlainText() == hex_bytes
    assert window.txt_bytes_per_char.text() == str(len(bytes.fromhex(hex_bytes)))
    assert window.txt_char_in_utf.toPlainText() == code
    assert window.txt_char_message.text() == window.char_message_text
    assert window.char_in_utf_2_char_input is False


@pytest.mark.parametrize(
    "code, message",
    [
        ("x+0041", "начинаться"),
        ("u-0041", "начинаться"),
        ("u++410", "формат"),
        ("u+ 041", "формат"),
        ("u+0_41", "формат"),
        ("u+0x41", "формат"),
        ("u+GGGG", "формат"),
        ("u+００４１", "формат"),
        ("u+00410", "ровно 4"),
        ("U+0000410", "ровно 6"),
        ("U+0001F600", "ровно 6"),
        ("u+D800", "суррогат"),
        ("u+DBFF", "суррогат"),
        ("u+DC00", "суррогат"),
        ("u+DFFF", "суррогат"),
        ("U+00D800", "суррогат"),
        ("U+110000", "U+10FFFF"),
        ("U+FFFFFF", "U+10FFFF"),
        ("u+0041, u+0301", "ровно 4"),
    ],
)
def test_invalid_code_clears_previous_result(window, qtbot, code, message):
    window.txt_char_in_utf.setPlainText("u+0041")
    with qtbot.captureExceptions() as errors:
        window.txt_char_in_utf.setPlainText(code)
    assert not errors, f"Unhandled exception in Qt slot: {errors}"
    assert message in window.txt_char_message.text()
    assert "255, 0, 0" in window.txt_char_in_utf.styleSheet()
    assert window.txt_char_input.toPlainText() == ""
    assert window.txt_char_in_byte.toPlainText() == ""
    assert window.txt_char_name.toPlainText() == ""
    assert window.txt_char_category.toPlainText() == ""
    assert window.txt_bytes_per_char.text() == ""
    assert window.char_in_utf_2_char_input is False


@pytest.mark.parametrize(
    "code",
    [
        "",
        "u",
        "U",
        "u+",
        "u+0",
        "u+00",
        "u+004",
        "U+",
        "U+0",
        "U+01",
        "U+01F",
        "U+01F6",
        "U+01F60",
    ],
)
def test_incomplete_code_clears_old_symbol(window, code):
    window.txt_char_in_utf.setPlainText("u+0041")
    window.txt_char_in_utf.setPlainText(code)
    assert window.txt_char_input.toPlainText() == ""
    assert window.txt_char_in_byte.toPlainText() == ""
    assert window.txt_char_message.text() == window.char_message_text


def test_repeat_same_code_after_deleting_digit(window):
    for code in ["u+0041", "u+004", "u+0041"]:
        window.txt_char_in_utf.setPlainText(code)
    assert window.txt_char_input.toPlainText() == "A"
    assert window.txt_char_in_byte.toPlainText() == "41"
    assert window.txt_char_name.toPlainText() == "LATIN CAPITAL LETTER A"
    assert window.char_in_utf_2_char_input is False
    window.txt_char_input.setPlainText("B")
    assert window.txt_char_in_utf.toPlainText() == "u+0042"


def test_back_conversion_blocks_symbol_signals_and_updates_once(window, monkeypatch):
    original = window.on_char_input_changed
    calls = []

    def counted():
        calls.append(True)
        original()

    monkeypatch.setattr(window, "on_char_input_changed", counted)
    spy = QSignalSpy(window.txt_char_input.textChanged)
    window.txt_char_in_utf.setPlainText("u+0041")
    assert len(spy) == 0
    assert len(calls) == 1
    assert window.txt_char_in_byte.toPlainText() == "41"


def test_flag_restored_when_update_raises(window, monkeypatch):
    # Вызываем слот напрямую: исключение не должно выходить через Qt callback.
    with QSignalBlocker(window.txt_char_in_utf):
        window.txt_char_in_utf.setPlainText("u+0041")

    def fail():
        raise RuntimeError("test failure")

    monkeypatch.setattr(window, "on_char_input_changed", fail)
    with pytest.raises(RuntimeError, match="test failure"):
        window.on_char_in_utf_changed()
    assert window.char_in_utf_2_char_input is False
    assert not window.txt_char_input.signalsBlocked()


def test_valid_code_restores_error_style(window):
    window.txt_char_in_utf.setPlainText("u+ZZZZ")
    window.txt_char_in_utf.setPlainText("u+0041")
    assert window.txt_char_in_utf.styleSheet() == window.char_in_utf_sheet
    assert window.txt_char_message.styleSheet() == window.char_message_sheet
