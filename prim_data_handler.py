# приводит ячейки датафрейма (четыре столбца), значения с цифрами к единому виду

import pandas as pd
import numpy as np

# Предположим, что тебе нужно обработать несколько столбцов, например:
columns_to_convert = ['minValue', 'maxValue', 'step', 'DefaultValue']  # замени на реальные названия

def convert_mixed_column(col):
    """
    Преобразует колонку с разными форматами чисел, '-' и Null в float,
    заменяя '-', '', None на NaN.
    """
    def convert_value(val):
        if isinstance(val, str) and val.strip() == '-':
            return np.nan
        elif pd.isna(val):  # проверяем на Null (NaN, None)
            return np.nan
        else:
            try:
                # Пытаемся преобразовать строку с ',' или '.' в float
                if isinstance(val, str):
                    val = val.replace(',', '.')  # замена запятой на точку
                return float(val)
            except ValueError:
                return np.nan  # если не число — тоже NaN
    return col.apply(convert_value)

def start_data_convert(df):
    # Создаем копию, чтобы не менять оригинал
    df = df.copy()
    
    for col in columns_to_convert:
        if col in df.columns:
            df[col] = convert_mixed_column(df[col])
    return df