"""Интерфейс анализатора Unicode и обработчики сигналов Qt."""

import re
from pathlib import Path

import regex
from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import QFontDatabase, QTextCursor
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QLineEdit,
    QLabel,
    QApplication,
    QWidget,
)
from PyQt6 import uic

from unicode_class import Unicode
from fonts import Fonts

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Window(QMainWindow):
    """Окно анализа текста, графем и UTF-8-байтов.

    Графемы считаются библиотекой regex. Поле кодовой точки принимает
    один код в формате приложения; составная графема выводится списком
    кодов. Текущий символ выбирается справа от курсора.
    """

    btn_clear: QPushButton
    btn_exit: QPushButton
    txt_bytes_per_char: QLineEdit
    txt_char_category: QPlainTextEdit
    txt_char_fonts: QPlainTextEdit
    txt_char_input: QPlainTextEdit
    txt_char_in_byte: QPlainTextEdit
    txt_char_in_utf: QPlainTextEdit
    txt_char_message: QLabel
    txt_char_name: QPlainTextEdit
    txt_num_symbol: QLineEdit
    txt_text_bytes: QPlainTextEdit
    txt_text_input: QPlainTextEdit
    txt_total_byts: QLineEdit
    txt_total_chars: QLineEdit

    def __init__(self, parent=None) -> None:
        """Загрузить форму, подключить сигналы, настроить шрифты и состояние.

        Форма unicode.ui и каталог fonts находятся в корне проекта, над src.
        Требуется заранее созданный QApplication.

        Raises:
            RuntimeError: шрифт не загружен или семейство отсутствует.
        """

        super(Window, self).__init__(parent)

        uic.loadUi(str(PROJECT_ROOT / "unicode.ui"), self)
        self.connects()
        self.loaded_fonts = Fonts(PROJECT_ROOT)
        self.load_fonts()
        self.char_input_sheet = self.txt_char_input.styleSheet()
        self.char_in_utf_sheet = self.txt_char_in_utf.styleSheet()
        self.char_message_sheet = self.txt_char_message.styleSheet()
        self.char_message_text = self.txt_char_message.text()
        self.graphemes: list[str] = []
        self.char_in_utf_2_char_input = False
        self.unicode = Unicode()

    def connects(self):
        """Подключить к обработчикам изменения текста, положения курсора и нажатия кнопок."""

        self.txt_text_input.textChanged.connect(self.on_text_input_changed)
        self.txt_text_input.cursorPositionChanged.connect(
            self.on_text_input_cursor_changed
        )
        self.txt_char_input.textChanged.connect(self.on_char_input_changed)
        self.txt_char_in_utf.textChanged.connect(self.on_char_in_utf_changed)
        self.btn_clear.clicked.connect(self.on_btn_clear)
        self.btn_exit.clicked.connect(self.on_btn_exit)

    def load_fonts(self) -> None:
        """Загрузить шрифты и назначить семейства для эмодзи и основного текста.

        Регистрация семейства эмодзи действует на всё приложение.
        Требуется Qt 6.9 или новее.
        """

        # Установка шрифтов эиодзи
        QFontDatabase.setApplicationEmojiFontFamilies(
            self.loaded_fonts.get_emoji_fonts_name_list()
        )
        # Установка текстовых шрифтов
        fonts_list = self.loaded_fonts.get_text_fonts_name_list()
        self.setting_text_font_widget(self.txt_text_input, fonts_list)
        font = self.txt_text_input.font()

        self.setting_text_font_widget(self.txt_char_input, fonts_list)

    @staticmethod
    def setting_text_font_widget(widget: QWidget, fonts_list: list[str]) -> None:
        font = widget.font()
        font.setFamilies(fonts_list)
        widget.setFont(font)

    def on_text_input_changed(self) -> None:
        """Пересчитать графемы текста, UTF-8-байты и оба счётчика."""
        text = self.txt_text_input.toPlainText()
        self.graphemes = regex.findall(r"\X", text)

        # noinspection argument-equal-default
        utf_bytes = text.encode("utf-8")
        self.txt_text_bytes.setPlainText(utf_bytes.hex(" "))
        self.txt_total_byts.setText(str(len(utf_bytes)))
        self.txt_total_chars.setText(str(len(self.graphemes)))

        self.on_text_input_cursor_changed()

    def on_text_input_cursor_changed(self) -> None:
        """Показать графему справа от курсора и её номер, начиная с единицы.

        Если справа от курсора нет символа (конец текста) очистить поле символа и его номер.
        Выделение пользователя не изменяется.
        """
        text = self.txt_text_input.toPlainText()
        self.graphemes = regex.findall(r"\X", text)
        grapheme_index_at_cursor = self.get_grapheme_index_at_cursor(
            len_grapheme=len(self.graphemes)
        )
        if grapheme_index_at_cursor is None:
            self.txt_char_input.setPlainText("")
            self.txt_num_symbol.setText("")
            return
        self.txt_num_symbol.setText(str(grapheme_index_at_cursor + 1))
        self.txt_char_input.setPlainText(self.graphemes[grapheme_index_at_cursor])

    def on_char_input_changed(self) -> None:
        """Обновить оформление и характеристики содержимого поля символа.

        Проверка нескольких графем показывает предупреждение,
        но не останавливает вывод характеристик.
        """
        symbol = self.txt_char_input.toPlainText()
        self.restore_char_initial_style_values()
        self.create_text_field_utf(symbol)
        self.validate_symbol_input(symbol)
        self.validate_printable(symbol)
        utf_bytes = self.create_text_field_bytes(symbol)
        self.create_text_field_bytes_per_char(utf_bytes)
        self.create_text_field_char_name(symbol)
        self.create_text_field_char_category(symbol)
        self.create_text_field_char_fonts(self.txt_char_input)

    def restore_char_initial_style_values(self):
        """Восстановить исходные подсказку и стили полей символа и кода."""

        self.txt_char_message.setText(self.char_message_text)
        self.txt_char_message.setStyleSheet(self.char_message_sheet)
        self.txt_char_input.setStyleSheet(self.char_input_sheet)
        self.txt_char_in_utf.setStyleSheet(self.char_in_utf_sheet)

    def create_text_field_utf(self, symbol: str) -> None:
        """Вывести коды всех кодовых точек строки, блокируя сигнал поля.

        При активном char_in_utf_2_char_input (блокировка рекурсивного вызова)
        не изменять введённый код.
        """

        if self.char_in_utf_2_char_input:
            return

        list_escape: list[str] = list()

        for char in symbol:
            list_escape.append(self.unicode.to_unicode_escape(char))

        with QSignalBlocker(self.txt_char_in_utf):
            self.txt_char_in_utf.setPlainText(", ".join(list_escape))

    def validate_symbol_input(self, symbol: str) -> None:
        """Показать ошибку, если непустая строка содержит несколько графем.

        Метод не прерывает вызывающий обработчик и не изменяет ввод.
        """
        if not (self.unicode.is_one_symbol(symbol) or symbol == ""):
            self.show_utf_error("Можно вводить только один символ")

    def validate_printable(self, symbol: str) -> None:
        """Подсветить строку без печатных кодовых точек Python.

        Наличие хотя бы одной точки с isprintable() == True отменяет
        подсветку.
        Исходный стиль восстанавливает вызывающий обработчик.
        """
        if not symbol:
            return

        if not any(char.isprintable() for char in symbol):
            self.txt_char_input.setStyleSheet("background-color: rgb(0, 255, 255);")

    def create_text_field_bytes(self, symbol: str) -> bytes:
        """Вывести UTF-8-байты строки в hex через пробел и вернуть bytes.

        Raises:
            UnicodeEncodeError: строка содержит одиночный суррогат.
        """
        # noinspection argument-equal-default
        utf_bytes = symbol.encode("utf-8")
        self.txt_char_in_byte.setPlainText(utf_bytes.hex(" "))
        return utf_bytes

    def create_text_field_bytes_per_char(self, utf_bytes: bytes) -> None:
        """Показать длину переданной UTF-8-последовательности в байтах."""
        bytes_per_char = len(utf_bytes)
        self.txt_bytes_per_char.setText(str(bytes_per_char))

    def create_text_field_char_name(self, symbol: str) -> None:
        """Вывести имена всех кодовых точек строки через запятую."""
        list_name: list[str] = list()
        for char in symbol:
            name = self.unicode.get_name_by_character(char)
            list_name.append(name)
        char_name = ", ".join(list_name)
        self.txt_char_name.setPlainText(char_name)

    def create_text_field_char_category(self, symbol: str) -> None:
        """Вывести категории всех кодовых точек строки через запятую."""
        list_category: list[str] = list()
        for char in symbol:
            list_category.append(self.unicode.get_category_by_character(char))
        char_category = ", ".join(list_category)
        self.txt_char_category.setPlainText(char_category)

    # noinspection GrazieInspection
    def on_char_in_utf_changed(self) -> None:
        """Проверить ввод одного кода и обновить символ с характеристиками.

        Принимаются u+XXXX и U+XXXXXX с hex-цифрами любого регистра.
        Суррогаты и значения выше U+10FFFF отклоняются. Неполный ввод
        остаётся без результата; некоторые ошибки выявляются только
        при достижении полной длины.

        Программное изменение символа блокирует его сигналы, после чего
        характеристики обновляются явно. Временный флаг сбрасывается
        даже при исключении.
        """
        self.clear_char_fields()
        self.restore_char_initial_style_values()
        text = self.txt_char_in_utf.toPlainText()

        if not self.validate_code_point_format(text):
            return

        try:
            code = int(text[2:], 16)
            symbol = chr(code)
        except ValueError:
            self.show_utf_error("Кодовая точка не должна превышать U+10FFFF")
            return
        if 0xD800 <= code <= 0xDFFF:
            self.show_utf_error(
                "Ввод суррогатных кодовых точек в сегменте [0xD800, 0xDFFF] запрещён"
            )
            return

        self.char_in_utf_2_char_input = True

        try:
            with QSignalBlocker(self.txt_char_input):
                self.txt_char_input.setPlainText(symbol)
            self.on_char_input_changed()
        finally:
            self.char_in_utf_2_char_input = False

    def validate_code_point_format(self, text: str) -> bool:
        """Проверяет формат записи кодовой точки: u+XXXX или U+XXXXXX.

        X — шестнадцатеричная цифра в любом регистре.
        Возвращает True только для полной записи правильного формата.
        Для пустого, незавершённого или ошибочного ввода возвращает False.
        При обнаружении ошибки показывает сообщение через show_utf_error.

        Допустимость числового значения в диапазоне Unicode не проверяется.
        """

        if len(text) == 0:
            return False

        if text[0].upper() != "U":
            self.show_utf_error("Код символа должен начинаться с U или u")
            return False

        if len(text) >= 2 and text[1] != "+":
            self.show_utf_error("Код символа должен начинаться с U+ или u+")
            return False

        if len(text) > 6 and text[0] == "u":
            # noinspection SpellCheckingInspection
            self.show_utf_error("После u+ должны быть ровно 4 шестнадцатеричные цифры")
            return False

        if len(text) > 8 and text[0] == "U":
            self.show_utf_error("После U+ должны быть ровно 6 шестнадцатеричных цифр")
            return False
        # fmt: off
        if (len(text) == 6  and text[0] == "u" or
            len(text) == 8 and text[0] == "U"):
            # fmt: on
            if not re.fullmatch(r"(u\+[0-9A-Fa-f]{4}|U\+[0-9A-Fa-f]{6})", text):
                self.show_utf_error("Недопустимый формат строки")
                return False
            return True

        return False

    def get_grapheme_index_at_cursor(self, len_grapheme: int) -> int | None:
        """Вернуть индекс графемы справа от курсора или None если графемы справа откурсора нет (курсор в конеце строки).

        Args:
            len_grapheme: число графем полного текущего текста.

        Подсчёт выполняется по тексту перед курсором. Выделение в тексте пользователя снимается
        (снимается только у копии QTextCursor).
        Для позиции курсора внутри составной графемы
        алгоритм не гарантирует индекс содержащей её графемы.
        """
        cursor = self.txt_text_input.textCursor()
        cursor.clearSelection()
        cursor.setPosition(0, QTextCursor.MoveMode.KeepAnchor)

        text_before = cursor.selection().toPlainText()
        len_text_before = len(regex.findall(r"\X", text_before))

        if len_text_before == len_grapheme:
            return None

        return len_text_before

    def on_btn_clear(self):
        """Очистить текстовые поля и подсказку; сигналы полей не блокируются."""
        all_fields = [
            self.txt_text_input,
            self.txt_char_in_utf,
            self.txt_char_input,
            self.txt_text_bytes,
            self.txt_total_byts,
            self.txt_total_chars,
            self.txt_bytes_per_char,
            self.txt_char_category,
            self.txt_char_in_byte,
            self.txt_char_message,
            self.txt_char_name,
            self.txt_num_symbol,
            self.txt_char_fonts,
        ]

        self.clear_fields(all_fields)

    @staticmethod
    def on_btn_exit():
        """Запросить завершение цикла событий всего приложения."""
        QApplication.quit()

    def show_utf_error(self, msg: str) -> None:
        """Вывести сообщение и окрасить сообщение и поле кода красным."""
        self.txt_char_message.setText(msg)
        self.txt_char_message.setStyleSheet("color: rgb(255, 0, 0);")
        self.txt_char_in_utf.setStyleSheet("color: rgb(255, 0, 0);")

    def clear_char_fields(self):
        """Очистить символ и его характеристики, сохранив ввод кода.

        Сигналы поля символа заблокированы; его обработчик не вызывается.
        """
        all_char_fields = [
            self.txt_bytes_per_char,
            self.txt_char_category,
            self.txt_char_in_byte,
            self.txt_char_message,
            self.txt_char_name,
            self.txt_num_symbol,
            self.txt_char_fonts,
        ]
        with QSignalBlocker(self.txt_char_input):
            self.txt_char_input.clear()

        self.clear_fields(all_char_fields)

    @staticmethod
    def clear_fields(fields_list: list[QWidget]) -> None:
        """Очистить QLineEdit, QPlainTextEdit и QLabel из переданного списка.

        Виджеты прочих типов игнорируются. Сигналы не блокируются.
        """
        for text in fields_list:
            if isinstance(text, QLineEdit):
                text.setText("")
            if isinstance(text, QPlainTextEdit):
                text.setPlainText("")
            if isinstance(text, QLabel):
                text.setText("")

    def create_text_field_char_fonts(self, widget: QPlainTextEdit) -> None:
        fonts = self.loaded_fonts.get_symbol_font_families(widget)
        self.txt_char_fonts.setPlainText(", ".join(fonts or []))
