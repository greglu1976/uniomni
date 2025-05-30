import sys
import argparse

from pathlib import Path
import pandas as pd

from fb2 import FB2
from fsu import FSU

from hardware import Hardware

from templater import fill_template, create_template

# В РАЗРАБОТКЕ ####################################
from sign_templater2 import create_summ_table
################################################


def get_help():
    print("""
Справка по использованию скрипта:
--------------------------------
--help, -h      : Показать это сообщение
--------------------------------

Версии
0.2.1 - альфа версия , без особого тестирования
(с) ООО Юнител Инжиниринг, 2025, Лубов Г.А.

В папке с exe должны быть папка fsu/
В ней должен быть файл init.xlsx в нем прописан порядок следования функц блоков и какие блоки используются
сами блоки - их названия должны быть как в файле init.xlsx

Блоки должны быть ДОРАБОТАНЫ (как в примере красной заливкой). 
1. Общие уставки прописываются тегом LLN0 в столбце 61850_TypeLN.
2. Отделить функциональные кнопки отдельно тегом button в столбце reserved1. Если столбца нет его нужно добавить
3. На листе Controls в Категория (group) прописать правильные теги (control, input, и system)
4. Столбцы MappingMask, Extension_enum, Extension_enum_HMI заменить на Logger, Disturber, StartDisturber в них прописать что требуется (сигналы на РС, РАС, пуск РАС) на листах Controls, Status Information, Settings
5. На лист TechInfo добавить описание ФБ (DescriptionFB) и описание функций между тегами DescriptionFuncList


1. В папке hardware/ описание железа терминала
2. В папке fsu/ описание функций терминала
3. Файл origin.docx - необходимый файл для шаблона бланка уставок - НЕ УДАЛЯТЬ!
4. Файл origin_summ.docx - необходимый файл для шаблона таблицы сигналов - НЕ УДАЛЯТЬ!
""")
    sys.exit(0)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--help', '-h', action='store_true')
args = parser.parse_args()

if args.help:
    get_help()



print('Генератор бланка уставок и суммарной таблицы сигналов v0.2.1 от 30.05.25')

# Задаем папку где описание софт
path = Path('fsu/')

# Читаем лист 'order' и первый столбец
df = pd.read_excel(path / 'init.xlsx', sheet_name='Order')
fbs_list = df.iloc[:, 0].tolist()  # первый столбец (индекс 0)

#print(fbs_list)

fsu = FSU()

for file_name in fbs_list:
    file_path = path / f"{file_name}.xlsx"  # Добавляем расширение .xlsx
    
    fb = FB2(file_path)

    fsu.add_fb(fb)   # Добавляем в FSU
    print(f"Добавляем функциональный блок: {fb.get_fb_name()}")

fsu.collect_control()
fsu.collect_statuses()
fsu.collect_inputs()

#print(fsu.get_fsu_all_statuses_sorted())


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


########################################################################
# Запуск генерации бланка уставок устройства
create_template(fsu, hw)
fill_template(fsu, hw)

########################################################################
# Запуск генерации суммарной таблицы

create_summ_table(fsu, isVirtKey=fsu.get_fsu_buttons(), isVirtSwitch=fsu.get_fsu_switches(), isStatuses=bool(fsu.get_fsu_statuses_sorted()),isSysStatuses=bool(fsu.get_fsu_sys_statuses_sorted()))

path = Path('.')
# Убеждаемся, что папка существует
if path.exists() and path.is_dir():
    # Список файлов для удаления
    files_to_remove = ['summ_table_templ.docx', 'temp.docx']

    for filename in files_to_remove:
        file_path = path / filename  # Полный путь к файлу
        if file_path.exists():      # Проверяем, существует ли файл
            file_path.unlink()      # Удаляем файл
            print(f"Файл {filename} удален.")
        else:
            print(f"Файл {filename} не найден.")
else:
    print("Папка fsu/ не найдена или это не папка.")


input("Нажмите Enter для выхода...")