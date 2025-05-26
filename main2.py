from pathlib import Path
import pandas as pd

import json

import pickle

from prim_data_handler import start_data_convert
from fb import FB
from fsu import FSU


from templater import fill_template

# Создание пути (автоматически учитывает ОС)
path = Path("funcs/")

a = FB(path)
b = FB(path)

aa = FSU()
aa.add_fb(a)
aa.add_fb(b)

with open('object.pkl', 'wb') as file:
    pickle.dump(a, file)

# Загружаем объект обратно
with open('object.pkl', 'rb') as file:
    a = pickle.load(file)



fill_template(aa)



#print(a.name, a.description)

#for func in a.functions:
    #print(func.get_iec_name(), func.get_name(), func.get_description())
    #print('=================================')