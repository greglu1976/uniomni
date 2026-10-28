"""Пути проекта и поиск файлов в пакетах поддержки.

Все остальные модули должны брать пути к ресурсам проекта (devices.ini,
origin.docx, abbr.json, dictionary.json, latex_build) отсюда, а не
относительно текущего рабочего каталога: иначе приложение работает только
при запуске из корня проекта.
"""

import json
from pathlib import Path

# Корень проекта: каталог, где лежат main.py, devices.ini, origin.docx и т.д.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Каталог сборки LaTeX (создаётся приложением)
BUILD_DIR = PROJECT_ROOT / "latex_build"

# Каталог запуска приложения вручную (на будущее, сейчас = корень проекта)
def project_path(*parts) -> Path:
    """Возвращает путь внутри корня проекта."""
    return PROJECT_ROOT.joinpath(*parts)


def find_file(directory, filename):
    """Возвращает Path к файлу в каталоге без учёта регистра имени.

    Пакеты поддержки приходят с разным регистром имён файлов
    (grouping.json / GROUPING.json), а файловая система Linux
    регистрозависимая — поэтому ищем файл по имени в нижнем регистре.

    Args:
        directory: каталог поиска (строка или Path).
        filename: имя файла, регистр которого может не совпадать.

    Returns:
        Path или None, если файл не найден.
    """
    if not directory:
        return None

    directory = Path(directory)
    if not directory.is_dir():
        return None

    direct = directory / filename
    if direct.is_file():
        return direct

    lowered = filename.lower()
    for item in directory.iterdir():
        if item.is_file() and item.name.lower() == lowered:
            return item

    return None


def load_packet_json(directory, filename):
    """Читает JSON-файл пакета поддержки с поиском имени без учёта регистра.

    Raises:
        FileNotFoundError: если файл отсутствует в каталоге пакета.
        json.JSONDecodeError: если файл содержит некорректный JSON.
    """
    path = find_file(directory, filename)
    if path is None:
        raise FileNotFoundError(
            f"В пакете поддержки не найден файл {filename}: {directory}"
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file), path
