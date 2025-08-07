import pandas as pd
import re
import html

class Function2:
    def __init__(self, df_signals=None,  name = '', description = '', iec_name='', fb_name = ''):
        self.df_signals = df_signals

        self.name = name
        self.description = description
        self.iec_name = iec_name
        self.fb_name = fb_name
        self.weight = '' # deprecated

        self.df_setting = None  # для хранения уставок
        self.df_status = None   # для хранения статусов

        self._func_signals_latex = [] # хранение отформатированых под latex сигналов вместе с заголовком
        self.list_bu = []
        self.list_re = []

        self.list_status = []

        self._process()
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

    def _process(self):
        # Разделяем по уставкам и статусам
        # Фильтруем по значению в столбце 'Категория (group)'
        self.df_setting = self.df_signals[self.df_signals['Категория (group)'] == 'setting']
        self.df_status = self.df_signals[self.df_signals['Категория (group)'] == 'status']

        # Заполняем NaN значения
        self.df_setting.loc[:, 'reserved1'] = self.df_setting['reserved1'].fillna('-')
        self.df_setting.loc[:, 'reserved2'] = self.df_setting['reserved2'].fillna('-') 
        # Опционально: сброс индексов (если нужен "чистый" вид)
        self.df_setting = self.df_setting.reset_index(drop=True)
        self.df_status = self.df_status.reset_index(drop=True)

    def _escape_latex_symbols(self, text):
        """Экранирует специальные символы для LaTeX"""
        if not isinstance(text, str):
            return str(text)
        # Используем математический режим для символов
        text = text.replace('>', '$>$')
        text = text.replace('<', '$<$')
        return text

    def _get_settings(self):
        if self.df_setting is None:
            return
        for _, row in self.df_setting.iterrows():
            desc = row['FullDescription (Описание параметра для пояснения в ПО ЮНИТ Сервис)'].strip().replace('<<','«').replace('>>','»')
            short_desc = row['ShortDescription'].replace('<<','«').replace('>>','»')
            applied_desc = row['AppliedDescription'] #.replace('<<','«').replace('>>','»')
            note = row['Note (Справочная информация)']
            units = row['units']
            min_value = row['minValue']
            max_value = row['maxValue']
            step = row['step']
            default_value =  row['DefaultValue']
            type = row['type']
            znach_diap = ''
            isKey = False
            if 'Del' in row['reserved2']:
                continue
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
                    default_value = f"{default_value:.{0}f}".replace('.', ',')

            znach_diap_bu = znach_diap   # Изм по зам. Халезова для бланка уставок 
            default_value_for_word =  default_value 
            if isKey:                   
                znach_diap_bu = re.sub(r'\d+ - ', '', znach_diap_bu)
                znach_diap_bu = html.escape(znach_diap_bu)  # Экранируем <, >, &, ", '
                default_value_for_word = html.escape(str(default_value)) # Убедимся, что это строка
                #print(znach_diap_bu)
            # словарь для бланка уставок
            dict_bu = {'Описание': desc, 'Наименование ПО': short_desc, 'Наименование ФСУ': applied_desc, 'Значение / Диапазон': znach_diap_bu, 'Ед.изм.': units, 'Шаг': step, 'Значение по умолчанию': default_value_for_word}
            # словарь для руководства по эксплуатации
            if isKey: # добавлено , чтобы -45 град не менял на =45. (После отработки исполнения ОЛ)
                znach_diap = znach_diap.replace('-', '=')
            #applied_desc = '\\mbox{'+applied_desc+'}'    
            dict_re = {'Параметр на ИЧМ': desc +' (' + short_desc + ')', 'Условное обозначение на схеме': self._escape_latex_symbols(applied_desc), 'Значение / Диапазон': znach_diap, 'Ед.изм.': units, 'Шаг': step }

            #if '-' in applied_desc:
                #dict_bu = {'Описание': "desc", 'Наименование ПО': "short_desc", 'Наименование ФСУ': "applied_desc", 'Значение / Диапазон': "znach_diap", 'Ед.изм.': "units", 'Шаг': "step", #'Значение по умолчанию': "default_value"}
            self.list_bu.append(dict_bu)
            self.list_re.append(dict_re)            





    def _format_status(self, value):
        """Форматирование числового статуса в символьное представление
        
        Параметры:
            value (int/str): Входное значение статуса
            
        Возвращает:
            str: Символьное представление статуса:
                - '+' для значения 1
                - '-' для значения 0
                - '*' для значения 2
                - '⊕' для значения 3
                - '?' для всех остальных случаев
        """
        status_mapping = {
            '0': '-',
            '1': '+',
            '2': '*',
            '3': '-'  # Символ плюса в кружочке (U+2295)
        }
        str_value = str(int(float(str(value).strip())))
        return status_mapping.get(str_value, '?')

    def _get_statuses(self):
        if self.df_status is None:
            return
        for _, row in self.df_status.iterrows():
            if row['type']!='BOOL':
                continue
            desc = row['FullDescription (Описание параметра для пояснения в ПО ЮНИТ Сервис)'].strip().replace('<<','«').replace('>>','»')
            short_desc = row['ShortDescription'].strip().replace('<<','«').replace('>>','»')

            dict = {
            'Полное наименование сигнала': self.fb_name + ' / ' + self.name + ': ' + desc, 
            'Наименование сигналов на ФСУ': short_desc, 
            'Дискретные входы': self._format_status(row['DigitalInput']),
            'Выходные реле': self._format_status(row['DigitalOutput']),
            'Светодиоды': self._format_status(row['LED']),
            'ФК': self._format_status(row['FunctionalButton']),
            'РС': self._format_status(row['Logger']),
            'РАС': self._format_status(row['Disturber']),
            'Пуск РАС': self._format_status(row['StartDisturber']),
            }
            self.list_status.append(dict)

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

    def get_settings_for_latex(self, header):
        table = []
        if header is not None and header != "":
            head_latex = '\multicolumn{5}{|c|}{ ' + header + ' } \\\\ \hline \n'
            table.append(head_latex)
        for row in self.list_re:
            str_ = '\centering '
            str_ += row['Параметр на ИЧМ'].replace('_', r'\_')
            str_ += ' & \centering '
            str_ += row['Условное обозначение на схеме'].replace('-', r'--').replace('_', r'\_')
            str_ += ' & \centering '
            str_ += row['Значение / Диапазон'].replace('\n', r'\\')
            str_ += ' & \centering '
            str_ += row['Ед.изм.'].replace('-', r'--').replace('%', r'\%')
            str_ += ' & \centering \\arraybackslash '
            str_ += row['Шаг'].replace('-', r'--')
            str_ += ' \\\\\n'  # Закрываем строку таблицы и переносим строку
            table.append(str_)  # Добавляем строку таблицы
            table.append('\\hline\n')  # Добавляем \hline отдельным элементом
 
        return table

    # Генерация таблицы сигналов разбитой по функциям (тип 2)
    # для форматирования latex сигналов функции
    def _create_formatted_signals_for_latex(self):
        if not self.list_status:
            return
        # Добавляем заголовок функции
        if self.description == 'Общие уставки':
            self.header_for_latex = f'\\multicolumn{{9}}{{c}}{{Общие сигналы}} \\\\\n\\hline\n'
        else:
            name_ = self.name.replace('_', r'\_')
            self.header_for_latex = f'\\multicolumn{{9}}{{c}}{{{self.description} ({name_})}} \\\\\n\\hline\n'

        self._func_signals_latex.append(self.header_for_latex)    
        for row in self.list_status:
            row_str = '\\raggedright '
            row_str += row['Полное наименование сигнала'].split(':')[1].replace('_', r'\_')
            row_str += ' & \\centering '
            row_str += row['Наименование сигналов на ФСУ'].replace('_', r'\_')
            row_str += ' & \\centering '
            row_str += row['Дискретные входы'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['Выходные реле'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['Светодиоды'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['ФК'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['РС'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row['РАС'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering \\arraybackslash '
            row_str += row['Пуск РАС'].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' \\\\ \\hline\n'
            self._func_signals_latex.append(row_str)

    def get_formatted_signals_for_latex(self):
        if not self._func_signals_latex:
            self._create_formatted_signals_for_latex()
        return self._func_signals_latex

