from pathlib import Path

from pydantic import BaseModel, TypeAdapter
from PyQt6.QtGui import QFontDatabase


class FontsList(BaseModel):
    font_family: str
    font_name: str
    is_emoji: bool = False
    is_main: bool = False


class Fonts:
    def __init__(self, project_root: Path):
        self.fonts_directory = project_root / "fonts"
        self.fonts_list_path = self.fonts_directory / "fonts_list.txt"
        self.fonts_list: list[FontsList] = []
        self.text_fonts_name_list: list[str] = []
        self.emoji_fonts_name_list: list[str] = []
        self.read_and_validation_fonts_list()
        self.load_font_and_verify_family()

    def read_and_validation_fonts_list(self) -> list[FontsList]:

        self.fonts_list = TypeAdapter(list[FontsList]).validate_json(
            self.fonts_list_path.read_text()
        )
        return self.fonts_list

    def load_font_and_verify_family(self) -> None:
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
        return self.filter_list_font_names(is_emoji=False)

    def get_emoji_fonts_name_list(self):
        return self.filter_list_font_names(is_emoji=True)

    def filter_list_font_names(self, is_emoji: bool) -> list[str]:

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


if __name__ == "__main__":
    fonts = Fonts(Path(__file__).resolve().parents[1])
    print(fonts.get_text_fonts_name_list())
    print(fonts.get_emoji_fonts_name_list())
