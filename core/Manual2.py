#Manual2.py
# Класс, представляющий руководство по эксплуатации 

import os
import re
from pathlib import Path
import ast
from utils.abbrs import start_abbr
from logger.logger import Logger

from core.SettingBlanc2 import SettingBlanc

class Manual:
    def __init__(self, device_data):
        self.device_data = device_data
        self.path_to_latex_desc = device_data["path_to_latex_desc"]
        self.path_to_ru_desc = device_data["path_to_ru_desc"]
        self.paths = []

        self.setting_blanc = SettingBlanc(self.device_data)

    def __find_fbpath(self, tex_file_path):
        with open(tex_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line.startswith(r'\newcommand{\fbpath}'):
                    start = line.find('{', line.find('}') + 1) + 1
                    end = line.rfind('}')
                    fbpath = line[start:end]
                    return fbpath.replace('\\', '/')  # нормализуем слеши
        return None

    # Ищем пути к функциям из general.tex
    def _get_all_paths_from_general_tex(self):
        self.path_to_general_tex = Path(self.path_to_latex_desc) / "_manual_latex" / "general.tex"

        # === Шаг 1: Найти значение \fbpath ===
        fbpath = self.__find_fbpath(self.path_to_general_tex)
        if not fbpath:
            Logger.error("Ошибка: переменная \\fbpath не найдена в файле.")
        else:
            Logger.info("Найден путь \\fbpath:")
            Logger.info(fbpath)

            # === Шаг 2: Извлечь пути из блока %===f ===
            in_block = False

            with open(self.path_to_general_tex, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()

                    # Переключаем флаг при встрече %===f
                    if line.startswith('%===f'):
                        in_block = not in_block
                        continue

                    # Обрабатываем только внутри блока и не комментарии
                    if in_block and line.startswith(r'\input{\fbpath') and not line.startswith('%'):
                        # Извлекаем относительный путь
                        start = line.find('{') + 1
                        end = line.find('}')
                        relative_path = line[start:end]

                        # Формируем полный путь
                        full_path = os.path.normpath(relative_path.replace(r'\fbpath', fbpath))
                        self.paths.append(full_path)

            # === Вывод результата ===
            Logger.info("Список путей:")
            for p in self.paths:
                Logger.info(p)


    #########################################################
    ###### Метод для обновления таблиц уставок в РЭ #########
    #########################################################

    def _render_latex_settings_block(self, settings_data):
        #print(settings_data)
        #print("==================")
        table = []
        if settings_data["type"] == "simple":
        #if header is not None and header != "":
            #head_latex = '\\multicolumn{5}{|c|}{ ' + header + ' } \\\\ \\hline \n'
            #table.append(head_latex)
            for i, row in enumerate(settings_data["rows"]):
                # Добавляем \hline перед всеми строками, кроме первой
                if i > 0:
                    table.append('\\hline\n')

                col3 = self.parse_note_to_latex(row["col3"])

                str_ = '\\centering '
                str_ += row["col2"].replace('_', r'\_').replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|')
                str_ += ' & \\centering '
                #str_ += row["col2"].replace('-', r'--').replace('_', r'\_').replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|') if row["col2"] else "--" #.replace('-', r'--').replace('_', r'\_')
                #str_ += ' & \\centering '
                str_ += col3 #.replace('\n', r'\\')
                str_ += ' & \\centering '
                str_ += row["col4"].replace('-', r'--').replace('%', r'\%')
                str_ += ' & \\centering '
                str_ += row["col5"].replace('-', r'--')
                str_ += ' & \\centering \\arraybackslash '
                str_ += row["col6"]               
                str_ += ' \\\\\n'  # Закрываем строку таблицы и переносим строку
                table.append(str_)
                
            table.append('\\hline\n')  # Добавляем \hline отдельным элементом            
            return table
        else:
            subs = settings_data["sub_functions"]
            for idx, sub in enumerate(subs):
                # Добавляем верхнюю линию только перед первым заголовком
                if idx == 0:
                    head_latex = '\\multicolumn{5}{|c|}{ ' + sub["subtitle"] + ' } \\\\ \\hline \n'
                else:
                    # Между подфункциями тоже нужен разделитель
                    head_latex = '\\hline\n\\multicolumn{5}{|c|}{ ' + sub["subtitle"] + ' } \\\\ \\hline \n'
                
                table.append(head_latex)
                for i, row in enumerate(sub["rows"]):
                    # Добавляем \hline перед всеми строками, кроме первой
                    if i > 0:
                        table.append('\\hline\n')

                    col3 = self.parse_note_to_latex(row["col3"])

                    str_ = '\\centering '
                    str_ += row["col2"].replace('_', r'\_').replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|')
                    str_ += ' & \\centering '
                    #str_ += row["col2"].replace('-', r'--').replace('_', r'\_').replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|') if row["col2"] else "--" #.replace('-', r'--').replace('_', r'\_')
                    #str_ += ' & \\centering '
                    str_ += col3 #.replace('\n', r'\\')
                    str_ += ' & \\centering '
                    str_ += row["col4"].replace('-', r'--').replace('%', r'\%')
                    str_ += ' & \\centering '
                    str_ += row["col5"].replace('-', r'--')
                    str_ += ' & \\centering \\arraybackslash '
                    str_ += row["col6"]               
                    str_ += ' \\\\\n'  # Закрываем строку таблицы и переносим строку
                    table.append(str_)
            table.append('\\hline\n')  # Добавляем \hline отдельным элементом
            return table

    def parse_note_to_latex(self, note_str):
        # Если это не строка или не начинается с "note_", возвращаем как есть
        if not isinstance(note_str, str) or not note_str.startswith("note_{"):
            return str(note_str) if note_str is not None else ""
        
        # Убираем "note_" и преобразуем в словарь
        dict_str = note_str[5:]  # убираем 'note_' (5 символов)
        # dict_str теперь: "{'0': 'Не предусмотрено', '1': 'Предусмотрено'}"

        # Парсим строку в словарь
        note_dict = ast.literal_eval(dict_str)
        
        # Получаем значения, сортируя по ключам (как числа)
        # Ключи могут быть '0', '1', '2' и т.д.
        sorted_values = [note_dict[key] for key in sorted(note_dict.keys(), key=lambda x: int(x))]
        
        # Объединяем через " \\ " (обратите внимание на пробелы)
        return " \\\\ ".join(sorted_values)



    def _parse_start_tag(self, raw_tag):
        """
        Полный парсинг тега
        """
    
        parts = raw_tag[6:].split('|')
        
        if len(parts) not in (1, 2):
            raise ValueError(f"Неверный формат: {raw_tag}")
        
        # Если есть разделитель и после него что-то есть
        if len(parts) == 2:
            path_part = parts[0].strip()
            function_name = parts[1].strip() if parts[1].strip() else "-"
        else:
            # Если разделителя нет
            path_part = parts[0].strip()
            function_name = "-"

        return path_part, function_name



    def renew_setting_tables_re(self):

        mapping = self.setting_blanc.maps
        #print(all_settings)

        start_tag_prefix = '%===m>'
        end_tag = '%===m\n'

        self._get_all_paths_from_general_tex()

        path_to_desc = self.device_data.get("path_to_latex_desc")
        if not path_to_desc:
            Logger.error("Error: path_to_latex_desc is empty or missing")
            return
        path_to_desc = path_to_desc.rstrip('/\\')   

        default_path = path_to_desc + "/Приложение. Уставки/settings.tex"
        self.paths = [default_path if os.path.exists(default_path) else path_to_desc + "/Приложение. Уставки/_latex/appset.tex"]


        #self.paths = [path_to_desc + "/Приложение. Уставки/settings.tex",] # Перезаписываем self.paths одной строкой пути к файлу settings в приложении Уставки


        for path in self.paths:
            if not os.path.exists(path):
                Logger.warning(f"Файл не найден: {path}")
                continue

            with open(path, 'r', encoding='utf-8') as f:
                content = f.readlines()

            new_content = []
            i = 0
            modified = False  # <-- Объявляем флаг здесь

            while i < len(content):
                line = content[i]

                if line.startswith(start_tag_prefix):
                    # Сохраняем начальный тег
                    start_line = line
                    new_content.append(start_line)

                    # Собираем старое содержимое до %===t1
                    old_block = []
                    i += 1
                    line = content[i]
                    if line.startswith('%===m>'):
                        # Сохраняем старый тег, если есть
                        new_content.append(line)
                        i += 1

                    while i < len(content):
                        current_line = content[i]
                        if current_line.startswith('%===m>'):
                            # Сохраняем старый тег %===t1*...
                            old_block.append(current_line)
                            i += 1                        
                        elif current_line == end_tag:
                            break
                        else:
                            old_block.append(current_line)
                            i += 1

                    # Парсим LN, FB и заголовок
                    fb, ln = self._parse_start_tag(start_line)
                    m = (mapping.get(fb, '-'))
                    if m=='-':
                        Logger.warning(f"Функциональный блок {fb} ({ln}) есть в описании latex, но отсутствует в файле поддержки устройства ")
                        # Оставляем старый блок как есть
                        new_content.extend(old_block)
                        new_content.append(end_tag)
                        i += 1
                        continue  # Пропускаем генерацию нового содержимого

                    #print(ln, fb, header)
                    # Генерируем новое содержимое
                    latex_new = []
                    settings_data = self.setting_blanc.get_table_settings_latex(fb)

                    if settings_data:
                        latex_new = self._render_latex_settings_block(settings_data)
                        #print(ln, fb)
                    else:
                        Logger.error(f"Не найдено уставок для ФБ: {fb}, Функция: {ln}.")
                        latex_new = old_block

                    # Склеиваем списки в одну строку для сравнения реального содержания
                    old_str = "".join(old_block)
                    new_str = "".join(latex_new)

                    # Проверяем результат get_table_settings_latex
                    if not latex_new:  # None или пустой список
                        Logger.info("Новое содержимое не сгенерировано - оставляем старое.")
                        new_content.extend(old_block)
                        new_content.append(end_tag)
                    elif old_str != new_str:
                        Logger.info(f"Контент отличается - будет обновлён. {settings_data['func_name'], ln, fb}")
                        new_content.extend(latex_new)
                        new_content.append(end_tag)
                        modified = True  # <-- Теперь корректно
                    else:
                        Logger.info("Контент не изменился - пропускаем обновление.")
                        new_content.extend(old_block)
                        new_content.append(end_tag)

                    i += 1  # Пропускаем закрывающий тег после добавления

                else:
                    # Копируем остальные строки
                    new_content.append(line)
                    i += 1

            # Записываем только если были изменения
            if modified:
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(new_content)
                Logger.info(f"Файл обновлён: {path}")
            else:
                Logger.info(f"Изменений в файле нет: {path}")

    #########################################################
    # Метод для обновления суммарной таблицы сигналов в РЭ ##
    #########################################################

    # Упрощенная проверка - сравниваем только существенное содержимое
    def _blocks_are_equivalent(self, block1, block2):
        """Проверяет, эквивалентны ли блоки по содержанию (игнорируя форматирование)"""
        # Объединяем все строки и удаляем лишние пробелы/переносы
        content1 = ' '.join(block1).replace('\n', ' ').replace('  ', ' ')
        content2 = ' '.join(block2).replace('\n', ' ').replace('  ', ' ')
        return content1 == content2


    def renew_sum_table_latex(self):
   
        path_to_appA_tex = Path(self.device_data["path_to_latex_desc"]) / "Приложение. Сигналы" / "_latex" / "appsign.tex"
        start_tag = '%===t2\n'

        if not os.path.exists(path_to_appA_tex):
            Logger.error(f"Файл описания приложения суммарных сигналов не найден: {path_to_appA_tex}")
            return

        with open(path_to_appA_tex, 'r', encoding='utf-8') as f:
            content = f.readlines()

        new_content = []
        i = 0
        modified = False

        while i < len(content):
            line = content[i]

            if line == start_tag:
                # Найден начальный тег
                new_content.append(line)  # Сохраняем начальный тег
                i += 1

                # Собираем старое содержимое до закрывающего %===t2
                old_block = []
                while i < len(content) and content[i] != start_tag:
                    old_block.append(content[i])
                    i += 1

                # Генерируем новое содержимое
                latex_new = self._generate_summ_table_latex() # old_block #self._fsu.get_summ_table_latex()


                # Проверяем результат
                if not latex_new:
                    Logger.warning("Сгенерирована пустая таблица суммарных сигналов! Оставляем старую.")
                    new_content.extend(old_block)
                    new_content.append(start_tag)  # Добавляем закрывающий тег
                elif not self._blocks_are_equivalent(old_block, latex_new):
                    Logger.info("Контент отличается - будет обновлён.")
                    new_content.extend(latex_new)
                    new_content.append(start_tag)  # Добавляем закрывающий тег
                    modified = True
                else:
                    Logger.info("Контент не изменился - пропускаем обновление.")
                    new_content.extend(old_block)
                    new_content.append(start_tag)

                i += 1  # Пропускаем закрывающий тег после добавления

            else:
                # Копируем остальные строки
                new_content.append(line)
                i += 1

        # Записываем только если были изменения
        if modified:
            with open(path_to_appA_tex, 'w', encoding='utf-8') as f:
                f.writelines(new_content)
            Logger.info(f"Файл обновлён: {path_to_appA_tex}")
        else:
            Logger.info(f"Изменений в файле нет: {path_to_appA_tex}")


    ###################################################
    ### Генерация суммарной таблицы в формате LATEX ###
    ###################################################
    def _generate_summ_table_latex(self):
        def _generate_row(row):
            row_str = '\\raggedright '
            row_str += row[0].replace('_', r'\_') #.replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|')
            row_str += ' & \\centering '
            row_str += row[1].replace('_', r'\_') #.replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|')
            row_str += ' & \\centering '
            row_str += row[2].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row[3].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row[4].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row[5].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row[6].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering '
            row_str += row[7].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' & \\centering \\arraybackslash '
            row_str += row[8].replace('-', r'--').replace('*', r'$\ast$')
            row_str += ' \\\\ \\hline\n'
            return row_str

        def _generate_section(data, title=''):
            section = []
            #print(data)
            if data:
                #section.append(f'\\multicolumn{{9}}{{c|}}{{{title}}} \\\\\n\\hline\n')
                if title:
                    section.append(f'\\multicolumn{{9}}{{c}}{{\\textbf{{{title}}}}} \\\\\n\\hline\n')
                for row in data:
                    section.append(_generate_row(row))
            return section

        table = [] 

        reg_data = self.setting_blanc.order_handler.get_data_for_registration()
        for section in reg_data:
            if section["main_title"] != "Сигналы функциональной логики":
                continue
            
            # Обрабатываем подразделы
            for subsection in section.get("subsections", []):
                # Заголовок подраздела (например, "ТО РПН")
                _name = subsection["title"].split("_")[0]
                if "GOOSE" in _name:
                    continue
                if "Блок измерений" in _name:
                    continue


                table.append('\\rowcolor{gray!10}\n')
                header_needed = self.setting_blanc.abbr_dict.get(_name, _name)
                table.append(f'\\multicolumn{{9}}{{c}}{{{header_needed}}} \\\\\n\\hline\n')

                # Таблицы внутри подраздела
                for table_data in subsection["tables"]:
                    data_rows = []
                    header2 = table_data["title"].replace('_',r'\_')
                    if table_data["title"]!='БУ' and header_needed!=header2 and subsection["title"]!=table_data["title"]: # subsection["title"]!=table_data["title"] появилось в АРНТ где АРНТ_1 и АРНТ_1
                        #print(table_data["title"])
                        table.append('\\rowcolor{gray!5}\n')
                        table.append(f'\\multicolumn{{9}}{{c}}{{{header2}}} \\\\\n\\hline\n')  

                    for param_name in table_data["parameters"]:
                        row_info = self.setting_blanc.config_handler.get_param_info(param_name)
                        
                        if row_info:
                            col1 = row_info.get("fullDescription", "")
                            col2 = row_info.get("appliedDescription", "")
                            param_type = row_info.get("type")
                            if param_type!=3:
                                continue
                            if col2.startswith('MMS') or col2.startswith('GOOSE') or col2.startswith('ИЧМ') or col2.startswith('АСУ:'):
                                continue

                            is_in_outputs = self.setting_blanc.order_handler.is_in_outputs_tree(param_name)
                            is_in_inputs = self.setting_blanc.order_handler.is_in_inputs_tree(param_name)
                            is_in_hmi_sign = self.setting_blanc.order_handler.is_in_hmi_sign_tree(param_name)
                            is_in_digit_sign = self.setting_blanc.order_handler.is_in_digit_sign_tree(param_name)

                            if  col2.startswith('ФК:'):  
                                l = (col1, col2, "+" if is_in_inputs else "-", "+" if is_in_outputs else "-", "+" if is_in_hmi_sign else "-", "+", "+" if is_in_digit_sign else "-", "+" if is_in_digit_sign else "-", "+" if is_in_digit_sign else "-")
                            else:
                                l = (
                                    col1, 
                                    col2, 
                                    "+" if is_in_inputs else "-", 
                                    "+" if is_in_outputs else "-", 
                                    "+" if is_in_hmi_sign else "-", 
                                    "-", 
                                    "+" if is_in_digit_sign else "-", 
                                    "+" if is_in_digit_sign else "-", 
                                    "+" if is_in_digit_sign else "-"
                                    )
                            data_rows.append(l)
                    
                    if data_rows:
                        s = _generate_section(data_rows)
                        table.extend(s)

        return table


    ###################################################
           ### Обновить перечень сокращений  ###
    ###################################################        

    def renew_abbrs(self):
        path_to = Path(self.path_to_latex_desc)  / '_manual_latex' / 'general.pdf'
        Logger.info(path_to)
        start_abbr(path_to) 

    def renew_abbrs_ru(self):
        if not self.path_to_ru_desc:
            Logger.error("Пустой путь к pdf с уставками!")
            return 1
        path_to = Path(self.path_to_ru_desc) 
        Logger.info(path_to)
        start_abbr(path_to) 
        return 0