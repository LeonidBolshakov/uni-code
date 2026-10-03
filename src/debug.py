import unicodedata
import random


def ya_with_point(prn: bool = True) -> str:
    composite_char = "я" + "\u0308"

    if prn:
        print("Разбор строки: ", composite_char, "\n")
    for i, char in enumerate(composite_char):
        name = unicodedata.name(char)
        category = unicodedata.category(char)
        combining_class = unicodedata.combining(char)

        if prn:
            print(f"Часть {i}: '{char}'")
            print(f"  Официальное имя:     {name}")
            print(
                f"  Категория (Поле 3):  {category} -> {'Non-spacing Mark (над/под буквой)' 
                if category == 'Mn' else 'Обычный символ'}"
            )
            print(
                f"  Класс связи (Поле 4): {combining_class} -> {'Крепится СВЕРХУ (Above)' 
                if combining_class == 230 else 'Базовая линия (0)'}"
            )
            print("-" * 50)

    return composite_char


def normalize() -> None:
    char_nfc = "ё"

    char_nfd = "е" + "\u0308"

    print(f"Визуально на экране: {char_nfc} и {char_nfd}")
    print(f"Равны ли они для Python напрямую? {char_nfc == char_nfd}")  # False!
    print(f"Длина NFC: {len(char_nfc)}, Длина NFD: {len(char_nfd)}")  # 1 и 2

    print("-" * 50)

    # РЕШЕНИЕ: Приводим обе строки к единому стандарту NFC (схлопываем)
    normalized_nfc_1 = unicodedata.normalize("NFC", char_nfc)
    normalized_nfc_2 = unicodedata.normalize("NFC", char_nfd)

    print("После нормализации к NFC:")
    print(f"Равны ли строки теперь? {normalized_nfc_1 == normalized_nfc_2}")  # True!
    print(f"Длина второй строки стала: {len(normalized_nfc_2)}")  # Сжалась до 1

    print("-" * 50)

    # Интересный факт про созданную букву 'я̈':
    ya_composite = "я" + "\u0308"
    ya_normal = unicodedata.normalize("NFC", ya_composite)
    print(f"Попытка сжать 'я̈' через NFC. Длина: {len(ya_normal)}")
    # Останется 2! Потому что готовой 'я' с двоеточием в таблице Unicode просто нет.


def flags() -> None:
    char_1 = "J"
    char_2 = "P"

    # Магическая константа — расстояние от обычных букв до региональных индикаторов
    OFFSET = 0x1F1A5  # (в десятичной системе это 127397)

    # Получаем коды индикаторов, просто прибавляя сдвиг к кодам букв
    code_j = ord(char_1) + OFFSET
    code_p = ord(char_2) + OFFSET

    print(f"Для '{char_1}' вычислен код: {hex(code_j)}")  # 0x1f1ef
    print(f"Для '{char_2}' вычислен код: {hex(code_p)}")  # 0x1f1f5

    # Собираем флаг
    flag_jp = chr(code_j) + chr(code_p)
    print(f"Результат: {flag_jp}")


def zalgo() -> None:
    # Списки кодов комбинируемых символов Unicode (класс Mn)
    # Эти символы прилипают к предыдущей букве
    ZALGO_UP = [chr(i) for i in range(0x0300, 0x0315)]  # Летят вверх
    ZALGO_DOWN = [chr(i) for i in range(0x0316, 0x032F)]  # Летят вниз
    ZALGO_MID = [chr(i) for i in range(0x0330, 0x0338)]  # Перечеркивают посередине

    ALL_ZALGO = ZALGO_UP + ZALGO_DOWN + ZALGO_MID

    def glitch_text(text, intensity=10):
        glitched_result = []

        for char in text:
            # Добавляем саму базовую букву (например, 'П')
            glitched_result.append(char)

            # Если это не пробел, накидываем на нее случайные «хвосты»
            if char != " ":
                for _ in range(intensity):
                    random_mark = random.choice(ALL_ZALGO)
                    glitched_result.append(random_mark)

        return "".join(glitched_result)

    # Проверяем работу в PyCharm
    source_text = "Питон и Юникод"
    corrupted_text = glitch_text(source_text, intensity=15)

    print("Исходный текст:", source_text)
    print("\nИскаженный Zalgo-текст:\n")
    print(corrupted_text)


def no_print_and_controls_simbols() -> None:
    no_print_simbols: list[str] = ["\0", "\t", "\n", "\r", "\x7f"]
    control_simbols: list[str] = [
        "",
        " ",
        r"\u00a0",
        r"\uooad",
    ]

    text = "A\tB\nC\u00a0D\u200bE"
    print(text)
    print('A"\u00ad"B')
    print(ya_with_point(prn=False))
    print("AЯ 😀漢")


ya_with_point()
# normalize()
# zalgo()
no_print_and_controls_simbols()
