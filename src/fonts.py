from pathlib import Path

import regex
from PyQt6.QtWidgets import QPlainTextEdit, QPlainTextDocumentLayout
from pydantic import BaseModel, TypeAdapter
from PyQt6.QtGui import QFontDatabase


class FontsList(BaseModel):
    """Модель Pydantic для валидации отдельной записи шрифта из конфигурации.

    Attributes:
        font_family (str): Имя семейства шрифта (как оно регистрируется в ОС/Qt)
        font_name (str): Имя файла шрифта с расширением (например, 'custom.ttf')
        is_emoji (bool): Флаг, указывающий, является ли шрифт специализированным для эмодзи
        is_main (bool): Флаг основного шрифта в своей категории. Должен быть ровно один
    """

    font_family: str
    font_name: str
    is_emoji: bool = False
    is_main: bool = False


class Fonts:
    """Управление загрузкой, валидацией и фильтрацией шрифтов приложения.

    Класс отвечает за чтение конфигурационного файла, регистрацию шрифтов
    в QFontDatabase Qt и разделение их на текстовые и эмодзи-семейства.
    """

    def __init__(self, project_root: Path):
        """Инициализировать менеджер шрифтов и загрузить конфигурацию.

        Args:
            project_root (Path): Путь к корневой директории проекта,
                где находятся папка 'fonts' и файл 'fonts_list.txt'.
        """
        self.fonts_directory = project_root / "fonts"
        self.fonts_list_path = self.fonts_directory / "fonts_list.txt"
        self.fonts_list: list[FontsList] = []
        self.text_fonts_name_list: list[str] = []
        self.emoji_fonts_name_list: list[str] = []
        self._read_and_validation_fonts_list()
        self._load_font_and_verify_family()

    def _read_and_validation_fonts_list(self) -> list[FontsList]:
        """Прочитать файл конфигурации и провалидировать его через Pydantic

        Returns:
            list[FontsList]: Список валидированных объектов конфигурации шрифтов

        Raises:
            FileNotFoundError: Файл конфигурации не найден
            ValidationError: Ошибка валидации структуры JSON
        """

        self.fonts_list = TypeAdapter(list[FontsList]).validate_json(
            self.fonts_list_path.read_text()
        )
        return self.fonts_list

    def _load_font_and_verify_family(self) -> None:
        """Зарегистрировать файлы шрифтов в Qt и проверить корректность семейств.

        Raises:
            RuntimeError: Если Qt не смог загрузить файл шрифта
                или в загруженном файле отсутствует указанное семейство.
        """
        for font in self.fonts_list:
            font_id = QFontDatabase.addApplicationFont(
                str(self.fonts_directory / font.font_name)
            )

            if font_id == -1:
                raise RuntimeError(
                    f"Не удалось загрузить шрифт {str(self.fonts_directory/ font.font_name)}"
                )
            families = QFontDatabase.applicationFontFamilies(font_id)
            if font.font_family not in families:
                raise RuntimeError(
                    f"В загруженном файле нет семейства {font.font_family}"
                )

    def get_text_fonts_name_list(self):
        """Получить упорядоченный список имен семейств для обычного текста.

        Основной шрифт (is_main=True) всегда идет первым.

        Returns:
            list[str]: Список названий шрифтовых семейств.
        """
        return self._filter_list_font_names(is_emoji=False)

    def get_emoji_fonts_name_list(self):
        """Получить упорядоченный список имен семейств для отображения эмодзи.

        Основной шрифт (is_main=True) всегда идет первым.

        Returns:
            list[str]: Список названий шрифтовых семейств для эмодзи.
        """
        return self._filter_list_font_names(is_emoji=True)

    def _filter_list_font_names(self, is_emoji: bool) -> list[str]:
        """Отфильтровать шрифты по категории и проверить бизнес-правила.

        Правила: в категории должен быть ровно 1 шрифт с отметкой 'is_main',
        и итоговый список не должен быть пустым.

        Args:
            is_emoji (bool): Фильтр категории (True для эмодзи, False для текста).

        Returns:
            list[str]: Упорядоченный список семейств (main-шрифт на индексе 0).

        Raises:
            ValueError: Если шрифтов в категории 0 или количество главных
                шрифтов (is_main) отлично от 1.
        """

        filtered_fonts_name_list: list[str] = []
        count_main = 0

        for font in self.fonts_list:
            if font.is_emoji == is_emoji:
                if font.is_main:
                    filtered_fonts_name_list.insert(0, font.font_family)
                    count_main += 1
                else:
                    filtered_fonts_name_list.append(font.font_family)

        if len(filtered_fonts_name_list) == 0:
            raise ValueError(
                f"Нет ни одного шрифта для отображения {'эмодзи' if is_emoji else 'текста'}"
            )
        if count_main != 1:
            raise ValueError(
                f"Количество шрифтов ({count_main})с отметкой main для отображения "
                f"{'эмодзи' if is_emoji else 'текста'} отлично от 1"
            )

        return filtered_fonts_name_list

    @staticmethod
    def get_symbol_font_families(widget: QPlainTextEdit) -> list[str] | None:
        """Определить реальные шрифты, использованные Qt для отрисовки первого символа.

        Использует анализ Layout и GlyphRuns для извлечения семейства шрифта,
        которым фактически отрисовался символ (включая fallback-механизмы Qt).

        Args:
            widget (QPlainTextEdit): Виджет, текстовый слой которого анализируется.

        Returns:
            list[str] | None: Отсортированный список уникальных семейств шрифтов
                или None, если слой документа не найден или некорректен.
        """

        document = widget.document()
        if not document:
            return None

        block = document.firstBlock()

        match = regex.match(r"\X", block.text())
        if match is None:
            return []

        symbol = match.group()
        length = len(symbol.encode("utf-16-le")) // 2

        document_layout = document.documentLayout()

        if not isinstance(document_layout, QPlainTextDocumentLayout):
            return None

        document_layout.ensureBlockLayout(block)

        block_layout = block.layout()
        if not block_layout:
            return None
        runs = block_layout.glyphRuns(0, length)

        return sorted({run.rawFont().familyName() for run in runs})


if __name__ == "__main__":
    fonts = Fonts(Path(__file__).resolve().parents[1])
    print(fonts.get_text_fonts_name_list())
    print(fonts.get_emoji_fonts_name_list())
