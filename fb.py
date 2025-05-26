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

        self._get_fb_data()
        self._create()
        self._collect_statuses()

    def process_control(self):
        pass

    def process_inputs(self):
        pass


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
                self.process_control()
                continue
                
            if file.name == 'inputs.xlsx':
                self.process_inputs()
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


    def get_description(self):
        return self.description

    def get_fb_statuses(self):
        return self.statuses