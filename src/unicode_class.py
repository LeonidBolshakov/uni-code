"""Независимые от Qt операции с кодовыми точками и графемами."""

from logging import setLogRecordFactory

import unicodedata
import regex


class Unicode:
    """Преобразования Unicode без зависимости от графического интерфейса.

    Методы имени, категории и обозначения принимают одну кодовую точку.
    Проверка is_one_symbol работает с одной расширенной графемой, которая
    может состоять из нескольких кодовых точек.
    """

    @staticmethod
    def get_unicode_by_characters(char: str) -> bytes:
        """Вернуть UTF-8-байты строки.

        Raises:
            UnicodeEncodeError: строка содержит одиночный суррогат.
        """
        # noinspection argument-equal-default
        return char.encode("utf-8")

    @staticmethod
    def get_name_by_character(char: str) -> str:
        """Вернуть имя одной кодовой точки или «Без имени».

        Raises:
            TypeError: передана пустая строка или несколько кодовых точек.
        """
        return unicodedata.name(char, "Без имени")

    @staticmethod
    def is_one_symbol(symbol: str) -> bool:
        """Проверить, что строка содержит ровно одну расширенную графему.

        Пустая строка не считается графемой. Используется шаблон regex \\X.
        """
        return regex.fullmatch(r"\X", symbol) is not None

    @staticmethod
    def to_unicode_escape(char: str) -> str:
        """Вернуть обозначение кодовой точки в формате данного приложения.

        Для BMP используется u+ и четыре строчные hex-цифры, для остальных
        точек — U+ и шесть. Это не escape-последовательность Python
        и не стандартное единообразное обозначение U+XXXX.
        Raises:
            TypeError: строка содержит не одну кодовую точку.
        """
        code_point = ord(char)
        if code_point > 0xFFFF:
            return rf"U+{code_point:06x}"
        return rf"u+{code_point:04x}"

    @staticmethod
    def get_category_by_character(char: str) -> str:
        """Вернуть двухбуквенную категорию одной кодовой точки Unicode.

        Raises:
            TypeError: передана пустая строка или несколько кодовых точек.
        """
        return unicodedata.category(char)
