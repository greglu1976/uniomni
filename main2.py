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
hw =  Hardware()

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