# Класс, представляющий руководство по эксплуатации

import os
import re
from pathlib import Path

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

    def _render_latex_settings_block(self, settings_data, header):
        table = []
        if header is not None and header != "":
            head_latex = '\\multicolumn{5}{|c|}{ ' + header + ' } \\\\ \\hline \n'
            table.append(head_latex)
        
        for i, row in enumerate(settings_data):
            # Добавляем \hline перед всеми строками, кроме первой
            if i > 0:
                table.append('\\hline\n')
                
            str_ = '\\centering '
            str_ += row[0].replace('_', r'\_')
            str_ += ' & \\centering '
            str_ += row[1].replace('-', r'--').replace('_', r'\_')
            str_ += ' & \\centering '
            str_ += row[2].replace('\n', r'\\')
            str_ += ' & \\centering '
            str_ += row[3].replace('-', r'--').replace('%', r'\%')
            str_ += ' & \\centering \\arraybackslash '
            str_ += row[4].replace('-', r'--')
            str_ += ' \\\\\n'  # Закрываем строку таблицы и переносим строку
            table.append(str_)
        
        return table
    # Старая функция - добавляет hline после последней строки 30.12.25 Вынесена в архив
    def _render_latex_settings_blockOLD(self, settings_data, header):
        table = []
        if header is not None and header != "":
            head_latex = '\multicolumn{5}{|c|}{ ' + header + ' } \\\\ \hline \n'
            table.append(head_latex)
        for row in settings_data:
            str_ = '\centering '
            str_ += row[0].replace('_', r'\_')
            str_ += ' & \centering '
            str_ += row[1].replace('-', r'--').replace('_', r'\_')
            str_ += ' & \centering '
            str_ += row[2].replace('\n', r'\\')
            str_ += ' & \centering '
            str_ += row[3].replace('-', r'--').replace('%', r'\%')
            str_ += ' & \centering \\arraybackslash '
            str_ += row[4].replace('-', r'--')
            str_ += ' \\\\\n'  # Закрываем строку таблицы и переносим строку
            table.append(str_)  # Добавляем строку таблицы
            #print(str_)
            table.append('\\hline\n')  # Добавляем \hline отдельным элементом
        #print(table)
        return table
    ########################################################################################


    def _parse_start_tag(self, tag_line):
        """
        Парсит строку вида:
            %==+t1*PDIF1|TDIF> Дифференциальная защита
        или
            %==+t1*PDIF1|TDIF
        Возвращает кортеж: (ln, fb, header)
        """
        match = re.search(r'\*(.*?)\|(.*?)(?:>(.*))?$', tag_line)
        if match:
            ln = match.group(1).strip()
            fb = match.group(2).strip()
            header = match.group(3).strip() if match.group(3) else ""
            return ln, fb, header
        return None, None, None

    def renew_setting_tables_re(self, device):
        start_tag_prefix = '%==+t1*'
        end_tag = '%===t1\n'

        self._get_all_paths_from_general_tex()

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
                    if line.startswith('%===t1*'):
                        # Сохраняем старый тег, если есть
                        new_content.append(line)
                        i += 1

                    while i < len(content):
                        current_line = content[i]
                        if current_line.startswith('%===t1*'):
                            # Сохраняем старый тег %===t1*...
                            old_block.append(current_line)
                            i += 1                        
                        elif current_line == end_tag:
                            break
                        else:
                            old_block.append(current_line)
                            i += 1

                    # Парсим LN, FB и заголовок
                    ln, fb, header = self._parse_start_tag(start_line)
                    # Генерируем новое содержимое
                    latex_new = []
                    settings_data = device.fsu.get_table_settings_latex(ln, fb)
                    if settings_data:
                        latex_new = self._render_latex_settings_block(settings_data, header)
                        #print(ln, fb)
                    else:
                        Logger.error(f"Не найдено уставок для ФБ: {fb}, Функция: {ln}.")
                        latex_new = old_block

                    # Проверяем результат get_table_settings_latex
                    if not latex_new:  # None или пустой список
                        Logger.info("Новое содержимое не сгенерировано - оставляем старое.")
                        new_content.extend(old_block)
                        new_content.append(end_tag)
                    elif old_block != latex_new:
                        Logger.info("Контент отличается - будет обновлён.")
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
        



        path_to_appA_tex = Path(self.device_data["path_to_latex_desc"]) / "Приложение А. Сигналы" / "_latex" / "app1.tex"
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
            row_str += row[0].replace('_', r'\_')
            row_str += ' & \\centering '
            row_str += row[1].replace('_', r'\_')
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
            print(data)
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

                table.append('\\rowcolor{gray!15}\n')
                header = f'\\multicolumn{{9}}{{c}}{{{self.setting_blanc.abbr_dict.get(_name, _name)}}} \\\\\n\\hline\n'
                table.append(header)

                Logger.info(f"{_name}")
                Logger.info(f"Еще 1: {self.setting_blanc.abbr_dict.get(_name, _name)}")

                # Таблицы внутри подраздела
                for table_data in subsection["tables"]:
                    Logger.info(f"Еще 2:  {table_data["title"]}")
                    #doc.add_paragraph(table_data["title"]).style = 'ДОК Таблица Название'
                    
                    data_rows = []
                    for param_name in table_data["parameters"]:
                        row_info = self.setting_blanc.config_handler.get_param_info(param_name)
                        
                        if row_info:
                            col1 = row_info.get("fullDescription", "")
                            col2 = row_info.get("appliedDescription", "")
                            param_type = row_info.get("type")
                            l = (col1, col2, str(param_type), "", "", "", "", "", "")
                            Logger.info(l)
                            data_rows.append(l)
                    
                    if data_rows:
                        #add_table_reg_core4(doc, data_rows)
                        #doc.add_paragraph().style = 'TAGS'
                        s = _generate_section(data_rows)
                        table.extend(s)
                        Logger.info(f"Рисуем таблицу")

        return table


        # Список сигналов ФСУ
        temp_common = device.fsu.get_statuses_for_latex()
        if temp_common:
            table.append(f'\\multicolumn{{9}}{{c}}{{\\textbf{{{"Общие сигналы функциональной логики"}}}}} \\\\\n\\hline\n')
            for fb_dict in temp_common:
                funcs_count = fb_dict["funcs_count"]
                table.append('\\rowcolor{gray!15}\n')
                header = f'\\multicolumn{{9}}{{c}}{{{fb_dict["description_fb"]} ({fb_dict["russian_name"]})}} \\\\\n\\hline\n'
                table.append(header)
                
                # Проходим по всем функциям с их статусами
                for func_group in fb_dict["statuses_by_function"]:
                    func_name = func_group["function_name"]
                    func_description = func_group["function_description"]
                    statuses = func_group["statuses"]
                    
                    
                    # Добавляем подзаголовок функции если нужно
                    if func_name:
                        # Не выводим заголовок только если: имя совпадает И функций ровно 1
                        if not (func_name == fb_dict["russian_name"] and funcs_count == 1):
                            # Определяем текст заголовка
                            if func_name == fb_dict["russian_name"]:
                                header_text = f'Общие сигналы ({func_name})'
                            else:
                                header_text = f'{func_description} ({func_name})'
                            
                            func_header = f'\\multicolumn{{9}}{{c}}{{{header_text}}} \\\\\n\\hline\n'
                            table.append(func_header)

                    # Генерируем таблицу для статусов этой функции
                    table.extend(_generate_section(statuses, ""))

        # Список сигналов ЖЕЛЕЗА
        #statuses_list = device.modules.get_statuses_for_latex_sum_table()
        #if statuses_list:
            #table.append(f'\\multicolumn{{9}}{{c}}{{\\textbf{{{"Дискретные сигналы блоков в составе устройства"}}}}} \\\\\n\\hline\n')
            #for module in device.modules.get_statuses_for_latex_sum_table():
                #table.append('\\rowcolor{gray!15}\n')
                #header = f'\\multicolumn{{9}}{{c}}{{{module["module"]}}} \\\\\n\\hline\n'
                #table.append(header)
                #table.extend(_generate_section(module["statuses"]))
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