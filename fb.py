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

        self.get_fb_data()
        self.create()


    def process_control(self):
        pass

    def process_inputs(self):
        pass

    def get_fb_data(self):
        # Получение списка файлов и папок в директории
        if self.path.exists() and self.path.is_dir():
            files = [f for f in self.path.iterdir() if f.is_file()]
            print("Список файлов:")
            for file in files:
                excel_path = self.path / file.name
                df_signals = pd.read_excel(excel_path, sheet_name='Signals')
                df_info = pd.read_excel(excel_path, sheet_name='Info')
                df_signals_processed = start_data_convert(df_signals)
                if file.name == 'LLN0.xlsx':
                    self.mainfunc = Function(df_signals=df_signals_processed, df_info=df_info, iec_name='LLN0', fb_name='')
                    self.iec_name = df_info[df_info['Parameter'] == 'IEC61850Name']['Value'].iloc[0]
                    self.name = df_info[df_info['Parameter'] == 'RussianName']['Value'].iloc[0]
                    self.description = df_info[df_info['Parameter'] == 'DescriptionFB']['Value'].iloc[0]
                    self.weight = df_info[df_info['Parameter'] == 'WeightFB']['Value'].iloc[0]
                    self.mainfunc.set_description('Общие уставки') # подменяем описание для бланка уставок
                    self.mainfunc.set_name('') # подменяем описание для бланка уставок
                    self.functions.insert(0, self.mainfunc)  # Добавляем LLN0 в начало списка
                    break
        else:
            print(f"Директория {self.path} не существует или не является папкой.")

    def create(self):
        # Получение списка файлов и папок в директории
        if self.path.exists() and self.path.is_dir():
            files = [f for f in self.path.iterdir() if f.is_file()]
            #print("Список файлов:")
            for file in files:
                #print(file.stem)
                excel_path = self.path / file.name
                df_signals = pd.read_excel(excel_path, sheet_name='Signals')
                df_info = pd.read_excel(excel_path, sheet_name='Info')
                df_signals_processed = start_data_convert(df_signals)
                if file.name == 'control.xlsx':
                    self.process_control()
                    continue
                if file.name == 'inputs.xlsx':
                    self.process_inputs()
                    continue                                
                if file.name == 'LLN0.xlsx':
                    continue
                func = Function(df_signals=df_signals_processed, df_info=df_info, iec_name=file.stem, fb_name=self.name)
                self.functions.append(func)
        else:
            print(f"Директория {self.path} не существует или не является папкой.")



    def get_description(self):
        return self.description