# Меняем вхождения в файлах приложения уставок

import re
import os

# === Настройки путей к файлам ===
# Укажите имя вашего исходного файла
input_file = 'settings.tex'
# Имя файла, куда будет сохранен результат
output_file = 'settings_corrected.tex'

def process_text():
    # Проверяем, существует ли файл
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл '{input_file}' не найден!")
        return

    # Читаем содержимое файла с кодировкой UTF-8
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Регулярное выражение для поиска
    # (.*?) - захватывает имя метки таблицы (например, mtz:tbl1, dz:tbl0)
    # (.*?) - захватывает название функции (например, МТЗ, ДЗ, АУ)
    pattern = r"В таблице \\ref\{(.*?)\} приведены параметры, необходимые для настройки (.*?)\."

    # Строка замены (подставляем захваченные группы через \1 и \2)
    replacement = r"Параметры для настройки \2 представлены в таблице \\ref{\1}."

    # Считаем количество совпадений до замены
    count = len(re.findall(pattern, text))

    # Выполняем замену
    new_text = re.sub(pattern, replacement, text)

    # Записываем результат в новый файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_text)

    # Выводим отчет о проделанной работе
    print(f"Обработка завершена!")
    print(f"Количество исправлений: {count}")
    print(f"Результат сохранен в файл: '{output_file}'")

if __name__ == "__main__":
    process_text()