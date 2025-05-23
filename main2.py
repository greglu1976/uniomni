from pathlib import Path
import pandas as pd

import json

from prim_data_handler import start_data_convert
from fb import FB



# Создание пути (автоматически учитывает ОС)
path = Path("funcs/")

a = FB(path)

#print(a.name, a.description)

for func in a.functions:
    print(func.list_statuses)
    print('=================================')