from pathlib import Path
import pandas as pd

from prim_data_handler import start_data_convert
from function2 import Function2

import json

class FB2:
    def __init__(self, path):
        self.path = path

        self.raw_controls_df = None
        self.raw_statuses_df = None
        self.raw_settings_df = None
        self.raw_info_df = None


        self.functions = []
        self._fb_signals_latex = []
        self.mainfunc = None

        self.name = ''
        self.iec_name = ''
        self.description = ''
        self.weight = ''
        self.statuses = []

        # инициализация данных по упр. сигналам
        self._df_control = None
        self.df_buttons = None        
        self.df_switches = None
        self.buttons_list = []
        self.switches_list = [] 

        # инициализация данных по дискретным входам
        self._df_inputs = None
        self.inputs_list = [] 

        # методы при инициализации
        self.__init_raw_dfs()
        self._get_fb_data()
        self._create()
        self._collect_statuses()
        self._process_inputs()
        self._process_control()
        self.get_formatted_signals_for_latex()

    def __init_raw_dfs(self):
        if not self.path.exists():
            print(f"⚠ Файл {self.path} не найден, пропускаем")
            return
        # Загружаем все листы из файла в отдельные датафреймы
        self.raw_controls_df = pd.read_excel(self.path, sheet_name='Controls', header=1)
        self.raw_statuses_df =  pd.read_excel(self.path, sheet_name='Status information', header=1)   
        self.raw_settings_df =  pd.read_excel(self.path, sheet_name='Settings', header=1) 
        self.raw_info_df =  pd.read_excel(self.path, sheet_name='TechInfo', header=1)
        # Проверяем и создаем при необходимости столбцы reserved1 и reserved2
        if 'reserved1' not in self.raw_statuses_df.columns:
            self.raw_statuses_df['reserved1'] = '-'
        if 'reserved2' not in self.raw_statuses_df.columns:
            self.raw_statuses_df['reserved2'] = '-'    
        if 'reserved1' not in self.raw_settings_df.columns:
            self.raw_settings_df['reserved1'] = '-'
        if 'reserved2' not in self.raw_settings_df.columns:
            self.raw_settings_df['reserved2'] = '-'
        if 'reserved1' not in self.raw_controls_df.columns:
            self.raw_controls_df['reserved1'] = '-'
        if 'reserved2' not in self.raw_controls_df.columns:
            self.raw_controls_df['reserved2'] = '-'
        self.raw_settings_df = self.raw_settings_df.fillna('-')

    def _get_fb_data(self):
        """Обработка специального файла LLN0.xlsx"""
        self.iec_name = self.raw_info_df[self.raw_info_df['Parameter'] == 'IEC61850Name']['Value'].iloc[0]
        self.name = self.raw_info_df[self.raw_info_df['Parameter'] == 'RussianName']['Value'].iloc[0]
        self.description = self.raw_info_df[self.raw_info_df['Parameter'] == 'DescriptionFB']['Value'].iloc[0]
        self.weight = self.raw_info_df[self.raw_info_df['Parameter'] == 'WeightCoefficient']['Value'].iloc[0]

        #df_signals = self.raw_settings_df[self.raw_settings_df['61850_TypeLN'] == 'LLN0']
        df_summ_t = pd.concat([self.raw_settings_df, self.raw_statuses_df])
        df_signals = df_summ_t[df_summ_t['61850_TypeLN'].str.contains('LLN0', na=False)]

        self.mainfunc = Function2(
            df_signals=df_signals,
            name=self.name, # ПРОТЕСТИРОВАТЬ!!!!!
            description='Общие уставки',
            iec_name='LLN0',
            fb_name=self.name
        )
        self.functions.insert(0, self.mainfunc)


    def _create(self):
        """Основной метод создания всех функций"""
        df_summ_t = pd.concat([self.raw_settings_df, self.raw_statuses_df])
        #df = df_summ_t[df_summ_t['61850_TypeLN'] != 'LLN0']  # убираем уставки относящиеся к LLN0
        df = df_summ_t[~df_summ_t['61850_TypeLN'].str.contains('LLN0', na=False)]

        # Разбиваем датафрей по именам функций
        # Удаляем строки с пустыми значениями в 'NodeName (рус)'
        df_cleaned = df[df["NodeName (рус)"].notna() & (df["NodeName (рус)"] != "")]
        # Разделяем DataFrame на список по уникальным значениям 'NodeName (рус)'
        list_of_dfs = [
            group for _, group in df_cleaned.groupby("NodeName (рус)", dropna=True)]

        # Найдём индексы всех строк, где Parameter == 'DescriptionFuncList'
        indices = self.raw_info_df.index[self.raw_info_df['Parameter'] == 'DescriptionFuncList'].tolist()
        # Проверяем, что есть как минимум два таких элемента
        if len(indices) >= 2:
            # Берём диапазон между первым и вторым вхождением
            start_idx = indices[0] + 1
            end_idx = indices[1]
            # Вырезаем нужную часть датафрейма
            subset = self.raw_info_df.loc[start_idx:end_idx - 1]
            # Преобразуем в словарь
            result_dict = dict(zip(subset['Parameter'], subset['Value']))
        else:
            result_dict = {}
            print("Не найдено достаточного количества меток 'DescriptionFuncList'")
        #print(result_dict)

        for name_, description_ in result_dict.items():
            for node_df in list_of_dfs:
                current_name = node_df['NodeName (рус)'].iloc[0]
                if current_name == name_:
                    iec_name_ = node_df['Name GEB'].iloc[0].split('_')[0]
                    func = Function2(
                        df_signals=node_df,
                        name=name_,
                        description=description_,
                        iec_name=iec_name_,
                        fb_name=self.name
                    )
                    self.functions.append(func)



    def __process_ctrl(self, df):
        df_control_list=[]
        for _, row in df.iterrows():
            desc = row['FullDescription (Описание параметра для пояснения в ПО ЮНИТ Сервис)'].strip().replace('<<','«').replace('>>','»')
            short_desc = row['ShortDescription'].strip().replace('<<','«').replace('>>','»')
            digit_input = row['DigitalInput']
            func_btn = row['FunctionalButton']
            digit_output = row['DigitalOutput']
            led = row['LED']
            logger = row['Logger']
            disturber = row['Disturber']
            start_disturber = row['StartDisturber']
            dict = {
            'Полное наименование сигнала': desc, 
            'Наименование сигналов на ФСУ': short_desc, 
            'Дискретные входы': '+' if str(digit_input)=='1' else '-',
            'Выходные реле': '+' if str(digit_output)=='1' else '-',
            'Светодиоды': '+' if str(led)=='1' else '-',
            'ФК': '+' if str(func_btn)=='1' else '-',
            'РС': '+' if str(logger)=='1' else '-',
            'РАС': '+' if str(disturber)=='1' else '-',
            'Пуск РАС': '+' if str(start_disturber)=='1' else '-',
            }
            df_control_list.append(dict)
        return df_control_list

    def _process_control(self):
        self._df_control = self.raw_controls_df[self.raw_controls_df['Категория (group)'] ==  'control']
        self._df_control = self._df_control.reset_index(drop=True)
        if self._df_control is None:
            return 
        self.df_buttons = self._df_control[self._df_control['reserved1'] == 'button'] 
        if not self.df_buttons.empty: 
            self.buttons_list = self.__process_ctrl(self.df_buttons)
        else:
            self.buttons_list = []      
        self.df_switches = self._df_control[self._df_control['reserved1'] != 'button']
        if not self.df_switches.empty: 
            self.switches_list = self.__process_ctrl(self.df_switches)
        else:
            self.switches_list = [] 

    def _process_inputs(self):
        self._df_inputs = self.raw_controls_df[self.raw_controls_df['Категория (group)'] == 'input']
        self._df_inputs = self._df_inputs.reset_index(drop=True)
        if self._df_inputs is None:
            return 
        self.inputs_list = self.__process_ctrl(self._df_inputs)

    def _collect_statuses(self):
        self.statuses = [status for func in self.functions for status in func.get_list_status()]

    def get_fb_name(self):
        return self.name

    def get_fb_iec_name(self):
        return self.iec_name

    def get_description(self):
        return self.description

    def get_fb_statuses(self):
        return self.statuses

    def get_buttons_list(self):
        return self.buttons_list
    def get_switches_list(self):
        return self.switches_list
    def get_inputs_list(self):
        return self.inputs_list        
    
    def get_functions(self):
        return self.functions 

    def is_fb_settings_empty(self):
        for func in self.functions:
            if func.get_settings_for_bu():
                return True
        return False

    # Генерация таблицы сигналов разбитой по функциям (тип 2)
    @staticmethod
    def __remove_consecutive_duplicates(lst):
        result = []
        for item in lst:
            if not result or result[-1] != item:
                result.append(item)
        return result  

    def _is_signals_for_latex(self):
        for func in self.functions:
            if func.get_formatted_signals_for_latex():
                return True
        return False

    def _create_formatted_signals_for_latex(self):
        if not self._is_signals_for_latex():
            return
        self._fb_signals_latex.append('\\rowcolor{gray!15} \n')
        header = f'\\multicolumn{{9}}{{c|}}{{{self.description} ({self.name})}} \\\\\n\\hline\n'
        self._fb_signals_latex.append(header)
        for func in self.functions:
            self._fb_signals_latex.extend(func.get_formatted_signals_for_latex())
        self._fb_signals_latex = self.__remove_consecutive_duplicates(self._fb_signals_latex)

    def get_formatted_signals_for_latex(self):
        if not self._fb_signals_latex:
            self._create_formatted_signals_for_latex()
        #print(self._fb_signals_latex)
        return self._fb_signals_latex