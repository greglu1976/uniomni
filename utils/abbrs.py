"""Обновление перечня сокращений в latex-документе.

Алгоритм: берём текст pdf, вытаскиваем слова-кандидаты в сокращения,
сверяемся со словарём dictionary.json и записываем latex-таблицу между
невидимыми тегами <begABBRS> и <endABBRS>.
"""

import json
import os
import re
import subprocess
import sys

try:  # PyMuPDF >= 1.24 предпочитает новое имя пакета
    import pymupdf
except ImportError:  # pragma: no cover - совместимость со старыми сборками
    import fitz as pymupdf

from logger.logger import Logger
from utils.paths import find_file, project_path

# Начало и конец latex-таблицы перечня сокращений
INTRO_STRS = [
    r"\phantomsection" + "\n",
    r"\color{uniblue}\section*{\centering{\large{ПЕРЕЧЕНЬ СОКРАЩЕНИЙ}}}" + "\n",
    r"\addcontentsline{toc}{section}{Перечень сокращений}" + "\n",
    r"{\color{white}\fontsize{0.1pt}{0.1pt}\selectfont<begABBRS>}" + "\n",
    r"\color{black}" + "\n",
    r'\begin{longtable}{>{\raggedright\arraybackslash}m{2cm}'
    r'>{\raggedright\arraybackslash}m{0.5cm}'
    r'>{\raggedright\arraybackslash}m{20cm}}' + "\n",
    r'\endfirsthead\endhead\endfoot\endlastfoot' + "\n",
]

OUTRO_STRS = [
    r'\end{longtable}' + "\n",
]

# Внутренний словарь на случай отсутствия dictionary.json
DEFAULT_ABBR_DICT = {
    'ОСФ': 'Орган сравнения фаз',
    'КИТЦ': 'Контроль исправности токовых цепей',
    'КИЦТ': 'Контроль исправности токовых цепей - неправильная абр',
    'ЗП': 'Защита от перегрузки',
    'ЗПО': 'Защита от потери охлаждения',
    'УРОВ': 'Устройство резервирования при отказе выключателя',
    'ТЗНП': 'Токовая защита нулевой последовательности',
    'ТЗОП': 'Токовая защита обратной последовательности',
    'ФСУ': 'Функционально-структурная схема',
    'ЗПНОП': 'Защита от повышения напряжения обратной последовательности',
}

# Слова, которые не являются сокращениями
EXCLUDE_LIST = {
    "AB", "BC", "CA", "DZ", "II", "RS", "SF", "SFP", "SGF", "TOF", "TON", "TP",
    "UA", "UB", "UC", "UI", "UА", "UБНН", "UС", "VD", "АВ", "ВС", "СА",
    "ЗАКАЗА", "ЗАЩИТ", "РЕМОНТ", "СХЕМ", "СХЕМЫ", "ФУНКЦИИ", "ЦЕПЕЙ", "KR",
    "KХ", "RJ", "RU", "АААА", "ВC", "ВЭД", "ИК", "ИЛИ", "ИС", "ИФ", "КОД",
    "НЕ", "НИ", "НК", "НФ", "ОКПД", "ООО", "ПАО", "РАБОТА", "СЕРВИС", "ТП",
    "ФЗ", "ФФ", "ЮНИТ", "ЮТКБ",
}

# Первые две заглавные буквы, дальше допустимы буквы, тильда и пробелы
ABBR_RE = re.compile(r'^[A-ZА-Я]{2}[A-Za-zА-Яа-я~\s]*$')


def load_dict(default_dict=None):
    """Читает dictionary.json из корня проекта (или отдаёт встроенный словарь)."""
    data = default_dict if default_dict is not None else DEFAULT_ABBR_DICT
    path = find_file(project_path(), 'dictionary.json')
    if path is None:
        Logger.warning("Не найден external словарь сокращений dictionary.json — "
                       "используется встроенный")
        return data

    try:
        with open(path, 'r', encoding='utf-8') as file:
            Logger.info("Найден внешний словарь сокращений dictionary.json")
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        Logger.error(f"Не удалось прочитать dictionary.json: {error}")
        return data


def get_abbrs(word_list):
    """Отбирает из списка слов кандидатов в сокращения."""
    new_word_list = []
    for word in word_list:
        cleaned = re.sub(r'^[^A-Za-zА-Яа-я]+', '', word)
        cleaned = re.sub(r'[^A-Za-zА-Яа-я]+$', '', cleaned)
        if ABBR_RE.match(cleaned):
            new_word_list.append(cleaned)

    abbrs = {word for word in new_word_list
             if len(word) <= 7 and word not in EXCLUDE_LIST}
    return sorted(abbrs)


def extract_words_from_pdf(pdf_path):
    """Возвращает слова pdf, кроме содержимого существующей таблицы сокращений."""
    words = []
    skip = False

    with pymupdf.open(str(pdf_path)) as document:
        for page in document:
            text = page.get_text("text")
            # «АСУ ТП» не должно разбиваться на два слова
            text = re.sub(r'АСУ\s+ТП', 'АСУ~ТП', text)

            for token in text.split():
                if token == '<begABBRS>':
                    skip = True
                    continue
                if token == '<endABBRS>':
                    skip = False
                    continue
                if not skip:
                    words.append(token)

    return words


def build_paths(pdf_path):
    """Пути основных файлов обновления (pdf, .tex, .txt, .docx)."""
    path = os.path.normpath(str(pdf_path))
    base_path, file_name = os.path.split(path)
    stem = os.path.splitext(file_name)[0]

    return (
        path,
        os.path.abspath(os.path.join(base_path, f'toa_{stem}.tex')),
        os.path.abspath(os.path.join(base_path, f'attrs_{stem}.txt')),
    )


def open_in_editor(path):
    """Открывает файл во внешней программе (если это возможно).

    Раньше здесь был os.startfile — он есть только в Windows.
    """
    try:
        if os.name == 'nt':
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', str(path)])
        else:
            subprocess.Popen(['xdg-open', str(path)])
    except (OSError, AttributeError) as error:
        Logger.warning(f"Не удалось открыть {path} во внешней программе: {error}")


def parse_tex(new_word_list, dictionary):
    """Строки latex-таблицы перечня сокращений."""
    tex_list = []
    for word in new_word_list:
        if word not in dictionary:
            continue

        value = str(dictionary[word])
        if value.startswith('!'):
            # Восклицательный знак в словаре — выделение красным
            tex_list.append(f'{word} & -- & \\textcolor{{red}}{{{value[1:]}}}; \\\\' + "\n")
        else:
            tex_list.append(f'{word} & -- & {value}; \\\\' + "\n")

    if tex_list:
        # В последней строке точка вместо точки с запятой
        last_index = len(tex_list) - 1
        tex_list[last_index] = tex_list[last_index].replace('; \\\\\n', '. \\\\\n')
        tex_list.append(
            r"{\color{white}\fontsize{0.1pt}{0.1pt}\selectfont<endABBRS>}" + "\n")

    return tex_list


def start_abbr(filepath):
    """Точка входа: обновить перечень сокращений по pdf-файлу.

    Returns:
        str: 'ok', 'noabbrs' или 'error'.
    """
    Logger.info("Запуск скрипта обновления сокращений...")

    pdf_path, tex_path, attrs_path = build_paths(filepath)

    if not os.path.isfile(pdf_path):
        Logger.error(f"Файл pdf не найден: {pdf_path}")
        return 'error'

    Logger.info(f"Обработка {pdf_path}")
    try:
        words = extract_words_from_pdf(pdf_path)
    except (RuntimeError, ValueError, OSError) as error:
        Logger.error(f"Не удалось прочитать pdf {pdf_path}: {error}")
        return 'error'

    word_list = sorted(set(words))
    new_word_list = get_abbrs(word_list)
    Logger.info(new_word_list)

    if not new_word_list:
        Logger.info("Нет распознанных сокращений в текущем файле pdf...")
        return 'noabbrs'

    dictionary = load_dict(DEFAULT_ABBR_DICT)
    known_keys = set(dictionary)
    new_abbrs = [word for word in new_word_list if word not in known_keys]

    with open(attrs_path, 'w', encoding='utf-8') as file:
        file.write("Список всех найденных сокращений в general.pdf: "
                   + ", ".join(new_word_list) + "\n")
        file.write("Список новых сокращений для добавления в dictionary.json: "
                   + ", ".join(new_abbrs))

    # Показываем файл, чтобы можно было дописать новые сокращения в словарь
    if new_abbrs:
        Logger.warning(f"Найдены сокращения, отсутствующие в dictionary.json: "
                       f"{', '.join(new_abbrs)}")
        open_in_editor(attrs_path)

    tex_list = parse_tex(new_word_list, dictionary)
    final_tex = INTRO_STRS + tex_list + OUTRO_STRS

    with open(tex_path, 'w', encoding='utf-8') as file:
        file.writelines(final_tex)

    Logger.info(f"Перечень сокращений записан: {tex_path}")
    return 'ok'
