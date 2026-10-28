# Класс LatexDoc - собирает единый файл описания (raw.tex) из проекта latex.
# Принимает путь к каталогу с general.tex, создаёт latex_build/raw.tex,
# копируя картинки в latex_build/images.

import re
import shutil
from pathlib import Path

from logger.logger import Logger
from utils.paths import BUILD_DIR

INPUT_RE = re.compile(r'\\input\{([^}]*)\}')
INCLUDEGRAPHICS_RE = re.compile(
    r'(\\includegraphics(?:\[[^]]*\])?(?:\{[^}]*\})*)\{([^}]*)\}')


class LatexDoc:
    def __init__(self, path_to_latex_doc, build_dir=None):
        self.path_to_latex_doc = Path(path_to_latex_doc).resolve()

        self.fbpath = None
        self.genpath = None
        self.apppath = None

        self.image_counter = 1
        self.build_dir = Path(build_dir) if build_dir else BUILD_DIR
        self.images_dir = self.build_dir / "images"

        self._handle_tex()

    # ------------------------------------------------------------- макросы

    def _known_macros(self):
        return {
            r'\fbpath': self.fbpath,
            r'\genpath': self.genpath,
            r'\apppath': self.apppath,
        }

    def _expand_macros(self, text):
        """Подставляет значения макросов путей (все, а не только первый)."""
        result = text
        for macro, value in self._known_macros().items():
            if macro in result and value:
                result = result.replace(macro, value)
        return result

    def _find_image(self, img_ref):
        """Ищет файл изображения относительно каталога документа."""
        candidates = [
            self.path_to_latex_doc / img_ref,
            self.path_to_latex_doc / "images" / img_ref,
            self.path_to_latex_doc / "figures" / img_ref,
            self.path_to_latex_doc / "graphics" / img_ref,
            Path(img_ref),
        ]
        for path in candidates:
            if path.is_file():
                return path

        # Резервный поиск по имени файла в подкаталогах документа
        name = Path(img_ref).name
        for base in (self.path_to_latex_doc, self.path_to_latex_doc / "images",
                     self.path_to_latex_doc / "figures",
                     self.path_to_latex_doc / "graphics"):
            if not base.exists():
                continue
            for found in base.rglob(name):
                if found.is_file():
                    return found
        return None

    def _process_images(self, lines):
        """Копирует картинки в latex_build/images и переименовывает в img1, img2..."""
        for i, line in enumerate(lines):
            if '\\includegraphics' not in line:
                continue

            matches = list(INCLUDEGRAPHICS_RE.finditer(line))
            if not matches:
                continue

            new_line = line
            for match in reversed(matches):
                before = match.group(1)
                img_ref = self._expand_macros(match.group(2).strip())

                # Уже обработанный файл пропускаем
                if re.match(r'img\d+\.(pdf|png|jpg|jpeg|gif)$', img_ref, re.IGNORECASE):
                    Logger.info(f"Пропускаем уже обработанный файл: {img_ref}")
                    continue

                image_path = self._find_image(img_ref)
                if image_path is None:
                    Logger.error(f"Файл изображения не найден: {img_ref}")
                    continue

                extension = image_path.suffix.lower()
                new_name = f"img{self.image_counter}{extension}"
                destination = self.images_dir / new_name

                try:
                    shutil.copy(image_path, destination)
                    Logger.info(f"Скопировано: {image_path} в {destination}")
                except OSError as error:
                    Logger.error(f"Ошибка копирования {image_path}: {error}")
                    continue

                start, end = match.span()
                new_line = f"{new_line[:start]}{before}{{{new_name}}}{new_line[end:]}"
                self.image_counter += 1

            lines[i] = new_line

    # ---------------------------------------------------------- input-файлы

    def _add_lines_from_tex(self, target_list, file_path):
        """Добавляет строки .tex-файла, пропуская комментарии."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # Пустые строки НЕ пропускаем: на них ломается вёрстка
                    # (например, в КС контроле синхронизма).
                    if line.strip().startswith('%'):
                        continue
                    target_list.append(line)
        except OSError as error:
            Logger.error(f"Ошибка чтения файла {file_path}: {error}")

    def _get_normalized_path(self, line):
        """Путь из строки \\input{...} с подставленными макросами."""
        clean_line = line.split('%', 1)[0].strip()

        match = INPUT_RE.search(clean_line)
        if not match:
            return None

        relative_path = self._expand_macros(match.group(1).strip())
        return Path(relative_path).resolve()

    # --------------------------------------------------------------- сборка

    def _read_paths(self, lines):
        """Первый проход: значения \\newcommand{\\fbpath} и т.п."""
        for line in lines:
            if line.strip().startswith('%'):
                continue
            for macro, attribute in ((r'\newcommand{\fbpath}', 'fbpath'),
                                     (r'\newcommand{\genpath}', 'genpath'),
                                     (r'\newcommand{\apppath}', 'apppath')):
                if macro not in line:
                    continue
                value = line.split('{', 2)[2].split('}', 1)[0] if line.count('{') >= 3 else None
                setattr(self, attribute, value)

    def _handle_tex(self):
        general_tex = self.path_to_latex_doc / 'general.tex'
        if not general_tex.is_file():
            raise FileNotFoundError(f"Не найден файл описания: {general_tex}")

        with open(general_tex, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 1 проход — пути из макросов
        self._read_paths(lines)

        # 2 проход — раскрываем \input
        raw_tex = []
        for line in lines:
            if line.strip().startswith('%') or not line.strip():
                continue

            if r'\input' in line:
                normalized_path = self._get_normalized_path(line)
                if normalized_path is None:
                    Logger.warning(f"Не удалось разобрать строку \\input: {line.strip()}")
                    continue
                self._add_lines_from_tex(raw_tex, normalized_path)
                continue

            raw_tex.append(line)

        # 3 проход — картинки
        self._process_images(raw_tex)

        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        raw_path = self.build_dir / 'raw.tex'
        with open(raw_path, 'w', encoding='utf-8') as file:
            file.writelines(raw_tex)

        Logger.info(f"Собран файл: {raw_path}")
