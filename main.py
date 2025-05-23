from pathlib import Path
import pandas as pd

import json

from prim_data_handler import start_data_convert
from function import Function

# Создание пути (автоматически учитывает ОС)
path = Path("funcs/")

# Переменные для хранения DataFrame
df_signals = None
df_info = None

# Получение списка файлов и папок в директории
if path.exists() and path.is_dir():
    files = [f for f in path.iterdir() if f.is_file()]
    print("Список файлов:")
    for file in files:
        print(file.name)
        if file.name == 'PDIF2.xlsx':
            # Полный путь к файлу Excel
            excel_path = path / file.name

            # Считываем нужные листы в DataFrame
            df_signals = pd.read_excel(excel_path, sheet_name='Signals')
            df_info = pd.read_excel(excel_path, sheet_name='Info')

            df_signals_processed = start_data_convert(df_signals)
            func = Function(df_signals=df_signals_processed, df_info=None)
            #func.save_to_xlsx()
            #func.get_settings()
            print(func.list_re)

            # Сохраняем в файл с отступами (для читаемости)
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(func.list_bu, f, ensure_ascii=False, indent=4)


            # Сохраняем обработанный DataFrame в новый Excel-файл
            #output_path = "PDIF2_processed.xlsx"
            #df_signals_processed.to_excel(output_path, index=False, sheet_name='Signals_Processed')
            #print(f"Обработанный датафрейм сохранён в: {output_path}")

            print(f"Файл {file.name} успешно прочитан.")
            break  # Прерываем цикл, если нашли нужный файл
    else:
        print("Файл PDIF2.xlsx не найден.")
else:
    print(f"Директория {path} не существует или не является папкой.")

# Теперь у тебя в переменных df_signals и df_info данные из Excel