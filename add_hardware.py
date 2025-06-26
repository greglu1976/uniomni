# Дополнительный класс описания железа, только для того чтобы выдать latex таблицу сигналов для второго устройства в РЭ!!!
# Не совсем правильно, должно быть одно РЭ на одно! устройство
# Здесь создаем дополнительную таблицу
# Надеюсь класс временный и потом будет УДАЛЕН!!!

import pandas as pd

class AdditionalHardware():
    def __init__(self, path_to_hardware_desc):
        self.path_to_hardware_desc = path_to_hardware_desc
        self._order_code_parsed = []
        if self.path_to_hardware_desc is None:
            return
        df_info = pd.read_excel(self.path_to_hardware_desc, sheet_name='Инфо')
        # 2. Словарь из df_info (Ключ -> Значение)
        info = dict(zip(df_info['Ключ'], df_info['Значение']))
        print(info)
