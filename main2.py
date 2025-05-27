from pathlib import Path
import pandas as pd

import json

import pickle

from prim_data_handler import start_data_convert
from fb import FB
from fsu import FSU
from hardware import Hardware

from templater import fill_template, create_template

# Создание пути (автоматически учитывает ОС)
path = Path("funcs/")

a = FB(path)
b = FB(path)

for func in a.functions:
    #print(func.get_list_status())
    pass
aa = FSU()
aa.add_fb(a)
aa.add_fb(b)
aa.collect_control()
aa.collect_statuses()
aa.collect_inputs()



# Создаем описание железа
# Создание пути (автоматически учитывает ОС)
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

#for fb in aa.fbs:
    #print(fb.get_buttons_list)
    #for btn in fb.get_buttons_list():
        #print(btn)



#with open('object.pkl', 'wb') as file:
    #pickle.dump(a, file)

# Загружаем объект обратно
#with open('object.pkl', 'rb') as file:
    #a = pickle.load(file)



create_template(aa, hw)
fill_template(aa, hw)



#print(a.name, a.description)

#for func in a.functions:
    #print(func.get_iec_name(), func.get_name(), func.get_description())
    #print('=================================')