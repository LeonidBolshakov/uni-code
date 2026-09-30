import regex
from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import QFont, QFontDatabase, QTextCursor
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QLineEdit,
    QLabel,
    QApplication,
)
from PyQt6 import uic

from unicode_class import Unicode


class Window(QMainWindow):
    btn_clear: QPushButton
    btn_exit: QPushButton
    txt_bytes_per_char: QLineEdit
    txt_char_category: QPlainTextEdit
    txt_char_in_byte: QPlainTextEdit
    txt_char_in_utf: QPlainTextEdit
    txt_char_input: QLineEdit
    txt_char_message: QLabel
    txt_char_name: QPlainTextEdit
    txt_num_symbol: QLineEdit
    txt_text_bytes: QPlainTextEdit
    txt_text_input: QPlainTextEdit
    txt_total_byts: QLineEdit
    txt_total_chars: QLineEdit

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        uic.loadUi("unicode.ui", self)
        self.connects()
        self.tune_widgets()
        self.char_input_sheet = self.txt_char_input.styleSheet()
        self.char_in_utf_sheet = self.txt_char_in_utf.styleSheet()
        self.char_message_sheet = self.txt_char_message.styleSheet()
        self.char_message_text = self.txt_char_message.text()
        self.utf_bytes = b""
        self.graphemes = ""
        self.char_in_utf_call_char_input = False
        self.unicode = Unicode()

    def connects(self):
        self.txt_text_input.textChanged.connect(self.on_txt_input_changed)
        self.txt_text_input.cursorPositionChanged.connect(
            self.on_txt_input_cursor_changed
        )
        self.txt_char_input.textChanged.connect(self.on_char_input_changed)
        self.txt_char_in_utf.textChanged.connect(self.on_char_in_utf_changed)
        self.btn_clear.clicked.connect(self.on_btn_clear)
        self.btn_exit.clicked.connect(self.on_btn_exit)

    def tune_widgets(self) -> None:
        family = self.load_font_family("fonts/NotoColorEmoji.ttf", "Noto Color Emoji")
        QFontDatabase.addApplicationEmojiFontFamily(family)

        family = self.load_font_family(
            "fonts/JetBrainsMono-Regular.ttf", "JetBrains Mono"
        )
        self.txt_text_input.setFont(QFont(family))

    @staticmethod
    def load_font_family(font_path: str, font_family_name: str) -> str:
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            raise RuntimeError(f"Не удалось загрузить шрифт {font_path}")
        families = QFontDatabase.applicationFontFamilies(font_id)
        if font_family_name not in families:
            raise RuntimeError(f"В загруженном файле нет семейства {font_family_name}")

        return font_family_name

    def on_txt_input_changed(self) -> None:
        txt = self.txt_text_input.toPlainText()
        # noinspection argument-equal-default
        utf_bytes = txt.encode("utf-8")
        self.txt_text_bytes.setPlainText(utf_bytes.hex(" "))
        self.txt_total_byts.setText(str(len(utf_bytes)))
        self.txt_total_chars.setText(str(len(self.graphemes)))

    def on_txt_input_cursor_changed(self):
        text = self.txt_text_input.toPlainText()
        self.graphemes = regex.findall(r"\X", text)
        grapheme_index_at_cursor = self.get_grapheme_index_at_cursor(
            len_grapheme=len(self.graphemes)
        )
        if grapheme_index_at_cursor is None:
            self.txt_char_input.setText("")
            self.txt_num_symbol.setText("")
            return
        self.txt_num_symbol.setText(str(grapheme_index_at_cursor + 1))
        self.txt_char_input.setText(self.graphemes[grapheme_index_at_cursor])

    def on_char_input_changed(self) -> None:
        symbol = self.txt_char_input.text()
        self.restore_char_initial_style_values()
        self.create_txt_field_utf(symbol)
        self.validate_symbol_input(symbol)
        self.validate_printable(symbol)
        self.create_txt_field_bytes(symbol)
        self.create_txt_field_bytes_per_char(symbol)
        self.create_txt_field_char_name(symbol)
        self.create_txt_field_char_category(symbol)

    # noinspection GrazieInspection
    def on_char_in_utf_changed(self) -> None:
        self.clear_char_fields()
        self.restore_char_initial_style_values()
        text = self.txt_char_in_utf.toPlainText()

        if len(text) == 0:
            return

        if not (text[0].upper() == "U"):
            self.show_char_in_utf_error("Код символа должен начинаться с U или u")
            return

        if len(text) >= 2:
            if not (text[1] == "+"):
                self.show_char_in_utf_error("Код символа должен начинаться с U+ или u+")
                return

        if len(text) > 6 and text[0] == "u":
            # noinspection SpellCheckingInspection
            self.show_char_in_utf_error(
                "При первом маленьком символе u код символа должен ровно быть 2 байта"
            )
            return

        if len(text) > 10 and text[0] == "U":
            self.show_char_in_utf_error(
                "При первом большом символе U код символа должен ровно быть 4 байта"
            )
            return
        # fmt: off
        if (len(text) == 6  and text[0] == "u" or
            len(text) == 10 and text[0] == "U"):
            # fmt: on
            try:
                symbol = chr(int(text[2:], 16))
            except ValueError:
                self.show_char_in_utf_error(
                    "Код символа должен содержать только 16 цифры и быть не больше 0x10FFFF"
                )
                return
            self.char_in_utf_call_char_input=True
            self.txt_char_input.setText(symbol)

    def get_grapheme_index_at_cursor(self, len_grapheme: int) -> int | None:
        cursor = self.txt_text_input.textCursor()
        cursor.setPosition(0, QTextCursor.MoveMode.KeepAnchor)

        text_before = cursor.selection().toPlainText()
        len_text_before = len(regex.findall(r"\X", text_before))

        if len_text_before == len_grapheme:
            return None

        return len_text_before

    def restore_char_initial_style_values(self):
        self.txt_char_message.setText(self.char_message_text)
        self.txt_char_message.setStyleSheet(self.char_message_sheet)
        self.txt_char_input.setStyleSheet(self.char_input_sheet)
        self.txt_char_in_utf.setStyleSheet(self.char_in_utf_sheet)

    def validate_symbol_input(self, symbol: str) -> None:
        if not (self.unicode.is_one_symbol(symbol) or symbol == ""):
            self.show_char_in_utf_error("Можно вводить только один символ")

    def validate_printable(self, symbol: str) -> None:
        if not symbol.isprintable():
            self.txt_char_input.setStyleSheet("background-color: rgb(0, 255, 255);")

    def create_txt_field_utf(self, symbol: str) -> None:
        if self.char_in_utf_call_char_input:
            self.char_in_utf_call_char_input = False
            return

        list_escape: list[str] = list()

        for char in symbol:
            list_escape.append(self.unicode.to_unicode_escape(char))
        with QSignalBlocker(self.txt_char_in_utf):
            self.txt_char_in_utf.setPlainText(", ".join(list_escape))

    def create_txt_field_bytes(self, symbol: str) -> None:
        # noinspection argument-equal-default
        self.utf_bytes = symbol.encode("utf-8")
        self.txt_char_in_byte.setPlainText(self.utf_bytes.hex(" "))

    def create_txt_field_bytes_per_char(self, symbol: str) -> None:
        bytes_per_char = len(self.utf_bytes)
        self.txt_bytes_per_char.setText(str(bytes_per_char))

    def create_txt_field_char_name(self, symbol: str) -> None:
        list_name: list[str] = list()
        for char in symbol:
            name = self.unicode.get_name_by_character(char)
            list_name.append(name)
        char_name = ", ".join(list_name)
        self.txt_char_name.setPlainText(char_name)

    def create_txt_field_char_category(self, symbol: str) -> None:
        list_categoty: list[str] = list()
        for char in symbol:
            list_categoty.append(self.unicode.get_category_by_character(char))
        char_category = ", ".join(list_categoty)
        self.txt_char_category.setPlainText(char_category)

    def on_btn_clear(self):
        all_txt = [
            self.txt_text_input,
            self.txt_text_bytes,
            self.txt_total_byts,
            self.txt_total_chars,
            self.txt_char_in_utf,
            self.txt_char_input,
        ]

        self.clear_char_fields()

        for txt in all_txt:
            if isinstance(txt, QLineEdit):
                txt.setText("")
            if isinstance(txt, QPlainTextEdit):
                txt.setPlainText("")

    @staticmethod
    def on_btn_exit():
        QApplication.quit()

    def show_char_in_utf_error(self, msg: str) -> None:
        self.txt_char_message.setText(msg)
        self.txt_char_message.setStyleSheet("color: rgb(255, 0, 0);")
        self.txt_char_in_utf.setStyleSheet("color: rgb(255, 0, 0);")

    def clear_char_fields(self):
        all_txt = [
            self.txt_bytes_per_char,
            self.txt_char_category,
            self.txt_char_in_byte,
            self.txt_char_message,
            self.txt_char_name,
            self.txt_num_symbol,
        ]

        for txt in all_txt:
            if isinstance(txt, QLineEdit):
                txt.setText("")
            if isinstance(txt, QPlainTextEdit):
                txt.setPlainText("")
