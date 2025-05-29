from pathlib import Path
import pandas as pd

from prim_data_handler import start_data_convert
from function import Function

import json

class FB:
    def __init__(self, path):
        self.path = path
        self.functions = []

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
        self._get_fb_data()
        self._create()
        self._collect_statuses()


    def __process_ctrl(self, df):
        df_control_list=[]
        for _, row in df.iterrows():
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

    def process_control(self, file):
        df_signals_processed, df_info = self._process_excel_file(file)
        self._df_control = df_signals_processed[df_signals_processed['Категория (group)'] == 'control']
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

    def process_inputs(self, file):
        df_signals_processed, df_info = self._process_excel_file(file)
        self._df_inputs = df_signals_processed[df_signals_processed['Категория (group)'] == 'input']
        self._df_inputs = self._df_inputs.reset_index(drop=True)
        if self._df_inputs is None:
            return 
        self.inputs_list = self.__process_ctrl(self._df_inputs)

    def _process_excel_file(self, file):
        """Общая функция обработки Excel файла."""
        excel_path = self.path / file.name
        df_signals = pd.read_excel(excel_path, sheet_name='Signals')
        df_info = pd.read_excel(excel_path, sheet_name='Info')
        return start_data_convert(df_signals), df_info

    def _process_LLN0(self, df_signals_processed, df_info):
        """Обработка специального файла LLN0.xlsx"""
        self.iec_name = df_info[df_info['Parameter'] == 'IEC61850Name']['Value'].iloc[0]
        self.name = df_info[df_info['Parameter'] == 'RussianName']['Value'].iloc[0]
        self.description = df_info[df_info['Parameter'] == 'DescriptionFB']['Value'].iloc[0]
        self.weight = df_info[df_info['Parameter'] == 'WeightFB']['Value'].iloc[0]
        self.mainfunc = Function(
            df_signals=df_signals_processed,
            df_info=df_info,
            iec_name='LLN0',
            fb_name=self.name
        )
        self.mainfunc.set_description('Общие уставки')
        self.mainfunc.set_name('')
        self.functions.insert(0, self.mainfunc)

    def _get_fb_data(self):
        """Обработка только LLN0.xlsx для получения имени функционального блока"""
        if not (self.path.exists() and self.path.is_dir()):
            print(f"Директория {self.path} не существует или не является папкой.")
            return

        for file in self.path.iterdir():
            if file.is_file() and file.name == 'LLN0.xlsx':
                df_signals_processed, df_info = self._process_excel_file(file)
                self._process_LLN0(df_signals_processed, df_info)
                break

    def _create(self):
        """Основной метод создания всех функций"""
        if not (self.path.exists() and self.path.is_dir()):
            print(f"Директория {self.path} не существует или не является папкой.")
            return

        for file in self.path.iterdir():
            if not (file.is_file() and file.suffix == '.xlsx'):
                continue
                
            if file.name == 'control.xlsx':
                self.process_control(file)
                continue
                
            if file.name == 'inputs.xlsx':
                self.process_inputs(file)
                continue
                
            if file.name == 'LLN0.xlsx':
                continue
                
            df_signals_processed, df_info = self._process_excel_file(file)
            func = Function(
                df_signals=df_signals_processed,
                df_info=df_info,
                iec_name=file.stem,
                fb_name=self.name
            )
            self.functions.append(func)

    def _collect_statuses(self):
        self.statuses = [status for func in self.functions for status in func.get_list_status()]


    def get_fb_name(self):
        return self.name

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