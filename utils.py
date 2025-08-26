import os
from pathlib import Path
import shutil

def create_directories(base_path="."):
    """
    Удаляет существующую директорию latex_build (если есть), затем создаёт
    заново latex_build и latex_build/images в указанной базовой папке.
    """
    base_dir = Path(base_path)
    build_dir = base_dir / "latex_build"
    images_dir = build_dir / "images"
    
    try:
        # Если директория latex_build существует — удаляем её и всё содержимое
        if build_dir.exists() and build_dir.is_dir():
            shutil.rmtree(build_dir)
            print(f"Удалена существующая директория: {build_dir.absolute()}")

        # Создаём заново (с поддиректорией images)
        images_dir.mkdir(parents=True, exist_ok=False)  # parents=True создаст и build_dir тоже
        
        print(f"Созданы новые директории:")
        print(f"  - {build_dir.absolute()}")
        print(f"  - {images_dir.absolute()}")
        
        return True
    except Exception as e:
        print(f"Ошибка при обработке директорий: {e}")
        return False