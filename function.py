import pandas as pd

class Function:
    def __init__(self, df_signals=None, df_info=None, iec_name='', fb_name = ''):
        self.df_signals = df_signals
        self.df_info = df_info
        self.iec_name = iec_name
        self.fb_name = fb_name
        self.df_setting = None  # для хранения уставок
        self.df_status = None   # для хранения статусов

        self.list_bu = []
        self.list_re = []

        self.list_status = []

        self.description = ''
        self.weight = ''
        self.name = ''

        self._process()
        self._get_info()
        self._get_settings()
        self._get_statuses()

    @staticmethod
    def __get_description_by_number(text, number):
        lines = text.split('\n')  # Разделяем строку по переводам строк
        for line in lines:
            if line.strip():  # Пропускаем пустые строки
                parts = line.split(' - ', 1)  # Разделяем по первому вхождению ' - '
                if len(parts) == 2:
                    current_num = parts[0].strip()
                    if current_num.isdigit() and int(current_num) == number:
                        return parts[1].strip()
        return None

    def _get_info(self):
        self.description = self.df_info[self.df_info['Parameter'] == 'DescriptionFunc']['Value'].iloc[0]
        self.weight = self.df_info[self.df_info['Parameter'] == 'WeightFunc']['Value'].iloc[0]
        self.name = self.df_signals['NodeName (рус)'].iloc[0]

    def _process(self):
        # Разделяем по уставкам и статусам
        # Фильтруем по значению в столбце 'Категория (group)'
        self.df_setting = self.df_signals[self.df_signals['Категория (group)'] == 'setting']
        self.df_status = self.df_signals[self.df_signals['Категория (group)'] == 'status']
        # Опционально: сброс индексов (если нужен "чистый" вид)
        self.df_setting = self.df_setting.reset_index(drop=True)
        self.df_status = self.df_status.reset_index(drop=True)

    def _get_settings(self):
        if self.df_setting is None:
            return
        for _, row in self.df_setting.iterrows():
            desc = row['FullDescription (Описание параметра для пояснения в ПО ЮНИТ Сервис)'].strip().replace('<<','«').replace('>>','»')
            short_desc = row['ShortDescription']
            applied_desc = row['AppliedDescription']
            note = row['Note (Справочная информация)']
            units = row['units']
            min_value = row['minValue']
            max_value = row['maxValue']
            step = row['step']
            default_value =  row['DefaultValue']
            type = row['type']
            znach_diap = ''
            isKey = False
            if 'SGF' in row['reserved2'] or 'SGF' in applied_desc: # Дополнительная строка с разъяснениями (если есть SGF - то это ключ)
                isKey = True

            # алгоритм взят из www5 - добавлена проверка подстроки с запятой 'ЭМВ, ЭМО1 и ЭМО2' 
            if isKey:
                #tt = '-' if any(substring in applied_desc for substring in ['Side', 'ksch', 'comp3i0']) else applied_desc # ПРОВЕРИТЬ !!! явно не рабочее!
                znach_diap = note.replace('\n', '')
                if 'ЭМВ, ЭМО1 и ЭМО2' in znach_diap:
                    znach_diap = znach_diap.replace('ЭМВ, ЭМО1 и ЭМО2', '@@')              
                znach_diap = znach_diap.replace(', ', '\n').replace(',', '\n')
                if '@@' in znach_diap:
                    znach_diap = znach_diap.replace('@@', 'ЭМВ, ЭМО1 и ЭМО2')                     
                units = '-'
                step = '-'
                raw_default_value = default_value
                default_value = self.__get_description_by_number(znach_diap, default_value) # вытащим описание текстовое значения по умолчанию

            else:
                if float(step)==1:
                    step = '1'  

                if units == 'мс':
                    units = 'с'
                    min_value = str(int(min_value)/1000)
                    max_value = str(int(max_value)/1000)
                    step = str(int(step)/1000)
                    default_value = str(int(default_value)/1000)                

                if 'INT' not in type or units == 'с':
                    step_str = str(step).replace(',', '.')  # Нормализуем разделитель
                    if '.' in step_str:
                        decimal_places = len(step_str.split('.')[1])
                    else:
                        decimal_places = 0

                    # Обрабатываем minValue
                    min_val_str = str(min_value).replace(',', '.')
                    try:
                        min_value = float(min_val_str)
                        min_value = f"{min_value:.{decimal_places}f}".replace('.', ',')
                    except ValueError:
                        min_value = min_val_str.replace('.', ',')  # Если не число
                    
                    # Обрабатываем maxValue
                    max_val_str = str(max_value).replace(',', '.')
                    try:
                        max_value = float(max_val_str)
                        max_value = f"{max_value:.{decimal_places}f}".replace('.', ',')
                    except ValueError:
                        max_value = max_val_str.replace('.', ',')  # Если не число

                    # Обрабатываем step (просто заменяем точку на запятую)
                    step = str(step).replace('.', ',')
                    znach_diap = f"{min_value} ... {max_value}"

                    # Обрабатываем setValue
                    default_value = str(default_value).replace(',', '.')
                    try:
                        default_value = float(default_value)
                        default_value = f"{default_value:.{decimal_places}f}".replace('.', ',')
                    except ValueError:
                        default_value = default_value.replace('.', ',')  # Если не число
                else:
                    # Для INT значений убираем все после точки/запятой
                    min_val = str(min_value).split('.')[0].split(',')[0]
                    max_val = str(max_value).split('.')[0].split(',')[0]
                    step = str(step).split('.')[0].split(',')[0]
                    znach_diap = f"{min_val} ... {max_val}"
                    #default_value = str(default_value).replace('.', ',')
                    default_value = f"{default_value:.{decimal_places}f}".replace('.', ',')
                    
            # словарь для бланка уставок
            dict_bu = {'Описание': desc, 'Наименование ПО': short_desc, 'Наименование ФСУ': applied_desc, 'Значение / Диапазон': znach_diap, 'Ед.изм.': units, 'Шаг': step, 'Значение по умолчанию': default_value}
            # словарь для руководства по эксплуатации
            dict_re = {'Параметр на ИЧМ': desc +' (' + short_desc + ')', 'Условное обозначение на схеме': applied_desc, 'Значение / Диапазон': znach_diap.replace('-', '='), 'Ед.изм.': units, 'Шаг': step }

            self.list_bu.append(dict_bu)
            self.list_re.append(dict_re)            

    def _get_statuses(self):
        if self.df_status is None:
            return
        for _, row in self.df_status.iterrows():
            if row['type']!='BOOL':
                continue
            desc = row['FullDescription (Описание параметра для пояснения в ПО ЮНИТ Сервис)'].strip().replace('<<','«').replace('>>','»')
            short_desc = row['ShortDescription']
            digit_input = row['DigitalInput']
            func_btn = row['FunctionalButton']
            digit_output = row['DigitalOutput']
            led = row['LED']
            logger = row['Logger']
            disturber = row['Disturber']
            start_disturber = row['StartDisturber']

            dict = {
            'Полное наименование сигнала': self.fb_name + ' / ' + self.name + ': ' + desc, 
            'Наименование сигналов на ФСУ': short_desc, 
            'Дискретные входы': '+' if str(digit_input)=='1' else '-',
            'Выходные реле': '+' if str(digit_output)=='1' else '-',
            'Светодиоды': '+' if str(led)=='1' else '-',
            'ФК': '+' if str(func_btn)=='1' else '-',
            'РС': '+' if str(logger)=='1' else '-',
            'РАС': '+' if str(disturber)=='1' else '-',
            'Пуск РАС': '+' if str(start_disturber)=='1' else '-',
            }
            self.list_status.append(dict)

    def _get_controls(self):
        pass

    def save_to_xlsx(self, filename='split_data.xlsx'):
        # Проверяем, есть ли данные для записи
        if self.df_setting is None or self.df_setting.empty:
            print("Нет данных для листа 'Setting'. Пропускаем запись.")
        if self.df_status is None or self.df_status.empty:
            print("Нет данных для листа 'Status'. Пропускаем запись.")

        if (self.df_setting is None or self.df_setting.empty) and \
        (self.df_status is None or self.df_status.empty):
            print("Нет данных для сохранения.")
            return

        # Записываем только те листы, которые содержат данные
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if self.df_setting is not None and not self.df_setting.empty:
                self.df_setting.to_excel(writer, sheet_name='Setting', index=False)
            if self.df_status is not None and not self.df_status.empty:
                self.df_status.to_excel(writer, sheet_name='Status', index=False)

        print(f"Файл успешно сохранён как {filename}")



    def get_settings_for_bu(self):
        return self.list_bu
    def get_settings_for_re(self):
        return self.list_re
    def get_iec_name(self):
        return self.iec_name
    def get_name(self):
        return self.name
    def get_description(self):
        return self.description

    def get_list_status(self):
        return self.list_status

    def set_description(self, desc):
        self.description = desc
    def set_name(self, name):
        self.name = name
    def set_fb_name(self, fb_name):
        self.fb_name = fb_name
