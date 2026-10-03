"""Контракты преобразований, границы Unicode и составные графемы."""

import pytest
from unicode_class import Unicode


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", b""),
        ("A", b"A"),
        ("А", b"\xd0\x90"),
        ("😀", b"\xf0\x9f\x98\x80"),
        ("e\u0301", b"e\xcc\x81"),
        ("A\n", b"A\n"),
        ("\x00", b"\x00"),
    ],
)
def test_utf8(text, expected):
    assert Unicode.get_unicode_by_characters(text) == expected


@pytest.mark.parametrize("text", ["\ud800", "\udfff", "A\ud800"])
def test_surrogates_cannot_be_utf8(text):
    with pytest.raises(UnicodeEncodeError):
        Unicode.get_unicode_by_characters(text)


@pytest.mark.parametrize(
    "char, name, category",
    [
        ("A", "LATIN CAPITAL LETTER A", "Lu"),
        ("я", "CYRILLIC SMALL LETTER YA", "Ll"),
        ("😀", "GRINNING FACE", "So"),
        ("\u0301", "COMBINING ACUTE ACCENT", "Mn"),
        ("\u200d", "ZERO WIDTH JOINER", "Cf"),
        (" ", "SPACE", "Zs"),
        ("\n", "Без имени", "Cc"),
        ("\x00", "Без имени", "Cc"),
        ("\uffff", "Без имени", "Cn"),
    ],
)
def test_name_and_category(char, name, category):
    assert Unicode.get_name_by_character(char) == name
    assert Unicode.get_category_by_character(char) == category


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", False),
        ("A", True),
        ("AB", False),
        ("e\u0301", True),
        ("👩‍💻", True),
        ("🇷🇺", True),
        ("👍🏽", True),
        ("1️⃣", True),
        ("\r\n", True),
        ("\n", True),
        ("\t", True),
        (" ", True),
        ("  ", False),
        ("😀😀", False),
        ("e\u0301A", False),
    ],
)
def test_one_grapheme(text, expected):
    assert Unicode.is_one_symbol(text) is expected


@pytest.mark.parametrize(
    "char, expected",
    [
        ("\x00", "u+0000"),
        ("A", "u+0041"),
        ("А", "u+0410"),
        ("\uffff", "u+ffff"),
        ("\U00010000", "U+010000"),
        ("😀", "U+01f600"),
        ("\U0010ffff", "U+10ffff"),
    ],
)
def test_code_point_format(char, expected):
    assert Unicode.to_unicode_escape(char) == expected


@pytest.mark.parametrize(
    "method",
    [
        Unicode.to_unicode_escape,
        Unicode.get_name_by_character,
        Unicode.get_category_by_character,
    ],
)
@pytest.mark.parametrize("text", ["", "AB", "e\u0301", "👩‍💻"])
def test_code_point_methods_reject_multiple_points(method, text):
    with pytest.raises(TypeError):
        method(text)
