"""Каталог сборки latex."""

import shutil
from pathlib import Path

from logger.logger import Logger
from utils.paths import BUILD_DIR


def create_directories(base_path=None):
    """Пересоздаёт каталог сборки latex_build (и подкаталоги images, obj).

    Args:
        base_path: базовый каталог; по умолчанию — корень проекта.

    Returns:
        bool: True, если каталоги готовы к работе.
    """
    build_dir = Path(base_path) / "latex_build" if base_path else Path(BUILD_DIR)
    images_dir = build_dir / "images"
    obj_dir = build_dir / "obj"

    # Страховка: удаляем только каталог сборки, а не произвольный путь
    if build_dir.exists() and build_dir.is_dir():
        if build_dir.name != "latex_build":
            Logger.error(f"Отказ удалять каталог с неожиданным именем: {build_dir}")
            return False
        try:
            shutil.rmtree(build_dir)
            Logger.info(f"Удалена существующая директория: {build_dir}")
        except OSError as error:
            Logger.error(f"Не удалось удалить {build_dir}: {error}")
            return False

    try:
        images_dir.mkdir(parents=True, exist_ok=False)
        obj_dir.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        Logger.error(f"Ошибка при создании директорий: {error}")
        return False

    Logger.info("Созданы новые директории:")
    Logger.info(f"  - {build_dir}")
    Logger.info(f"  - {images_dir}")
    Logger.info(f"  - {obj_dir}")
    return True
