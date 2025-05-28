from pathlib import Path
import pandas as pd

import json

import pickle

from prim_data_handler import start_data_convert
from fb import FB
from fsu import FSU
from hardware import Hardware

from templater import fill_template, create_template

# В РАЗРАБОТКЕ ####################################
from sign_templater import create_summ_table
################################################


# Функция сборки объекта FSU
def create_fsu_from_subdirs(base_dir):
    """Создает объект FSU, добавляя FB для каждой подпапки в base_dir."""
    path = Path(base_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {base_dir}")
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {base_dir}")

    fsu = FSU()  # Создаем FSU

    # Проходим по всем подпапкам (без учета имен)
    for subdir in path.iterdir():
        if subdir.is_dir():
            try:
                fb = FB(subdir)  # Создаем FB из подпапки
                fsu.add_fb(fb)   # Добавляем в FSU
                print(f"Added FB from: {subdir.name}")
            except Exception as e:
                print(f"Error creating FB from {subdir}: {e}")

    # Если добавили хотя бы один FB, собираем данные
    if hasattr(fsu, 'fbs') and fsu.fbs:  
        fsu.collect_control()
        fsu.collect_statuses()
        fsu.collect_inputs()
    else:
        print("Warning: No FB objects were added!")

    return fsu


###########################################################################
# Создаем описание ФСУ устройства (описание функций находится в папке fsu, далее в ней есть папки по ФБ с номерами 1...)

print('Генератор бланка уставок v0.1.1')
fsu = create_fsu_from_subdirs("fsu/")

###########################################################################
# Создаем описание железа устройства
path2 = Path("hardware/")

excel_path2 = path2 / 'description.xlsx'
df_versions = pd.read_excel(excel_path2, sheet_name='Версии')
df_versions['Дата'] = df_versions['Дата'].dt.strftime(r'%d.%m.%Y')
df_info = pd.read_excel(excel_path2, sheet_name='Инфо')

# 1. Словарь из df_versions (Номер -> Дата)
#versions = dict(zip(df_versions['Номер'], df_versions['Дата']))
versions = df_versions[['Номер', 'Дата']].to_dict('records')
# 2. Словарь из df_info (Ключ -> Значение)
info = dict(zip(df_info['Ключ'], df_info['Значение']))

hw = Hardware(versions, info)

########################################################################
# Запуск генерации бланка уставок устройства
create_template(fsu, hw)
fill_template(fsu, hw)

########################################################################
# Запуск генерации суммарной таблицы

create_summ_table(fsu)
