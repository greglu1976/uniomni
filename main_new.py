from pathlib import Path
import pandas as pd

from fb2 import FB2
from fsu import FSU

from hardware import Hardware

from templater import fill_template, create_template

# В РАЗРАБОТКЕ ####################################
from sign_templater import create_summ_table
################################################



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
    #print(f"Added FB from: {fb.get_fb_name()}")

fsu.collect_control()
fsu.collect_statuses()
fsu.collect_inputs()

print(fsu.get_fsu_statuses_sorted())



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

create_summ_table(fsu)
