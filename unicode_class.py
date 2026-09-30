import unicodedata
import regex


class Unicode:
    @staticmethod
    def get_unicode_by_character(char: str) -> bytes:
        # noinspection argument-equal-default
        return char.encode("utf-8")

    @staticmethod
    def get_name_by_character(char: str) -> str:
        return unicodedata.name(char, "Без имени")

    @staticmethod
    def is_one_symbol(symbol: str) -> bool:
        regex.fullmatch(r"\X", symbol)
        return regex.fullmatch(r"\X", symbol) is not None

    @staticmethod
    def to_unicode_escape(char: str) -> str:
        code_point = ord(char)
        if code_point > 0xFFFF:
            return rf"U+{code_point:08x}"
        return rf"u+{code_point:04x}"

    @staticmethod
    def get_category_by_character(char: str) -> str:
        return unicodedata.category(char)
