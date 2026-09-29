import regex
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
        self.char_message_sheet = self.txt_char_message.styleSheet()
        self.char_message_text = self.txt_char_message.text()
        self.utf_bytes = b""
        self.graphemes = ""
        self.unicode = Unicode()

    def connects(self):
        self.txt_text_input.textChanged.connect(self.on_text_input_changed)
        self.txt_text_input.cursorPositionChanged.connect(
            self.on_text_input_cursor_changed
        )
        self.txt_char_input.textChanged.connect(self.on_char_input_changed)
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

    def on_text_input_changed(self) -> None:
        txt = self.txt_text_input.toPlainText()
        # noinspection argument-equal-default
        utf_bytes = txt.encode("utf-8")
        self.txt_text_bytes.setPlainText(utf_bytes.hex(" "))
        self.txt_total_byts.setText(str(len(utf_bytes)))
        self.txt_total_chars.setText(str(len(txt)))

    def on_text_input_cursor_changed(self):
        text = self.txt_text_input.toPlainText()
        self.graphemes = regex.findall(r"\X", text)

        grapheme_index_at_cursor = self.get_grapheme_index_at_cursor(
            len_grapheme=len(self.graphemes)
        )
        if grapheme_index_at_cursor is None:
            return

        self.txt_num_symbol.setText(str(grapheme_index_at_cursor + 1))
        self.txt_char_input.setText(self.graphemes[grapheme_index_at_cursor])

    def on_char_input_changed(self) -> None:
        symbol = self.txt_char_input.text()
        self.validate_symbol_input(symbol)
        self.create_text_field_utf(symbol)
        self.create_text_field_bytes(symbol)
        self.create_text_field_bytes_per_char(symbol)
        self.create_text_field_char_name(symbol)
        self.create_text_field_char_category(symbol)

    def get_grapheme_index_at_cursor(self, len_grapheme: int) -> int | None:
        cursor = self.txt_text_input.textCursor()
        cursor.setPosition(0, QTextCursor.MoveMode.KeepAnchor)

        text_before = cursor.selection().toPlainText()
        len_text_before = len(regex.findall(r"\X", text_before))

        if len_text_before == len_grapheme:
            return None

        return len_text_before

    def validate_symbol_input(self, symbol: str) -> None:
        self.txt_char_message.setText(self.char_message_text)
        self.txt_char_message.setStyleSheet(self.char_message_sheet)
        self.txt_char_input.setStyleSheet(self.char_input_sheet)
        if not (self.unicode.is_one_symbol(symbol) or symbol == ""):
            self.txt_char_message.setText("Можно вводить только один видимый символ")
            self.txt_char_message.setStyleSheet("color: rgb(255, 0, 0);")
            self.txt_char_input.setStyleSheet("color: rgb(255, 0, 0);")

    def create_text_field_utf(self, symbol: str) -> None:
        list_escape: list[str] = list()

        for char in symbol:
            list_escape.append(self.unicode.to_unicode_escape(char))

        self.txt_char_in_utf.setPlainText(", ".join(list_escape))

    def create_text_field_bytes(self, symbol: str) -> None:
        # noinspection argument-equal-default
        self.utf_bytes = symbol.encode("utf-8")
        self.txt_char_in_byte.setPlainText(self.utf_bytes.hex(" "))

    def create_text_field_bytes_per_char(self, symbol: str) -> None:
        bytes_per_char = len(self.utf_bytes)
        self.txt_bytes_per_char.setText(str(bytes_per_char))

    def create_text_field_char_name(self, symbol: str) -> None:
        list_name: list[str] = list()
        for char in symbol:
            list_name.append(self.unicode.get_name_by_character(char))
        char_name = ", ".join(list_name)
        self.txt_char_name.setPlainText(char_name)

    def create_text_field_char_category(self, symbol: str) -> None:
        list_categoty: list[str] = list()
        for char in symbol:
            list_categoty.append(self.unicode.get_category_by_character(char))
        char_category = ", ".join(list_categoty)
        self.txt_char_category.setPlainText(char_category)

    def on_btn_clear(self):
        all_txt = [
            self.txt_text_input,
            self.txt_char_input,
            self.txt_bytes_per_char,
            self.txt_char_category,
            self.txt_char_in_byte,
            self.txt_char_in_utf,
            self.txt_char_message,
            self.txt_char_name,
            self.txt_num_symbol,
            self.txt_text_bytes,
            self.txt_total_byts,
            self.txt_total_chars,
        ]

        for txt in all_txt:
            if isinstance(txt, QLineEdit):
                txt.setText("")
            if isinstance(txt, QPlainTextEdit):
                txt.setPlainText("")

    @staticmethod
    def on_btn_exit():
        QApplication.quit()
