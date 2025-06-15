# Класс описывающий руководство по эксплуатации latex
import os
import re
from pathlib import Path

import pandas as pd

from fb2 import FB2
from fsu import FSU
from hardware import Hardware

from docx import Document
from docxtpl import DocxTemplate

from tables import add_summ_table2
from docx_handler import add_new_section_landscape

from templater import fill_template, create_template

class ExploitationGuideLatex:
    def __init__(self, path_to_latex_desc, path_to_fsu, fbs_list):
        self.path_to_latex_desc = path_to_latex_desc # путь к корневой папке проекта РЭ
        self.path_to_fsu = path_to_fsu # путь к корневой папке описания ФБ xlsx
        self.fbs_list = fbs_list # список имен ФБ для сборки ФСУ
        self.paths = [] # пути к файлам tex

        self._fsu = None
        self._hardware = None

        self._proceed_init() # ищем все пути к файлам tex
        self._create_fsu()

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

    def _proceed_init(self):
        self.path_to_general_tex = Path(self.path_to_latex_desc) / "_manual_latex" / "general.tex"

        # === Шаг 1: Найти значение \fbpath ===
        fbpath = self.__find_fbpath(self.path_to_general_tex)
        if not fbpath:
            print("Ошибка: переменная \\fbpath не найдена в файле.")
        else:
            print("Найден путь \\fbpath:")
            print(fbpath)

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
            print("\nСписок путей:")
            for p in self.paths:
                print(p)

    def _create_fsu(self):
        self._fsu = FSU()

        for file_name in self.fbs_list:
            file_path = self.path_to_fsu / f"{file_name}.xlsx"  # Добавляем расширение .xlsx
            
            fb = FB2(file_path)

            self._fsu.add_fb(fb)   # Добавляем в FSU
            print(f"Добавляем функциональный блок: {fb.get_fb_name()}")

        self._fsu.collect_control()
        self._fsu.collect_statuses()
        self._fsu.collect_inputs()

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
    # метод для обновления таблиц с уставками в РЭ
    def renew_setting_tables_re(self):
        start_tag_prefix = '%==+t1*'
        end_tag = '%===t1\n'

        for path in self.paths:
            if not os.path.exists(path):
                print(f"Файл не найден: {path}")
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

                    # Парсим LN, FB и заголовок
                    ln, fb, header = self._parse_start_tag(start_line)
                    #print(f"Найден тег: ln={ln}, fb={fb}, header='{header}'")

                    # Генерируем новое содержимое
                    latex_new = self._fsu.get_table_settings_latex(ln, fb, header)

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

                    # Проверяем результат get_table_settings_latex
                    if not latex_new:  # None или пустой список
                        print("Новое содержимое не сгенерировано — оставляем старое.")
                        new_content.extend(old_block)
                        new_content.append(end_tag)
                    elif old_block != latex_new:
                        print("Контент отличается — будет обновлён.")
                        new_content.extend(latex_new)
                        new_content.append(end_tag)
                        modified = True  # <-- Теперь корректно
                    else:
                        print("Контент не изменился — пропускаем обновление.")
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
                print(f"Файл обновлён: {path}")
            else:
                print(f"Изменений в файле нет: {path}")
    # метод для обновления суммарной таблицы сигналов в РЭ
    def renew_sum_table_latex(self):
        path_to_appA_tex = Path(self.path_to_latex_desc) / "Приложение А. Сигналы" / "_latex" / "app1.tex"
        start_tag = '%===t2\n'

        if not os.path.exists(path_to_appA_tex):
            print(f"Файл описания приложения А не найден: {path_to_appA_tex}")
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
                latex_new = self._fsu.get_summ_table_latex()

                # Проверяем результат
                if not latex_new:
                    print("Новое содержимое не сгенерировано — оставляем старое.")
                    new_content.extend(old_block)
                    new_content.append(start_tag)  # Добавляем закрывающий тег
                elif old_block != latex_new:
                    print("Контент отличается — будет обновлён.")
                    #print(old_block)
                    #print(latex_new)
                    new_content.extend(latex_new)
                    new_content.append(start_tag)  # Добавляем закрывающий тег
                    modified = True
                else:
                    print("Контент не изменился — пропускаем обновление.")
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
            print(f"Файл обновлён: {path_to_appA_tex}")
        else:
            print(f"Изменений в файле нет: {path_to_appA_tex}")
    # метод для создания экземпляра класса Hardware из xlsx файла
    def _init_hardware_with_xlsx(self):
        path2 = Path("hardware/")
        excel_path2 = path2 / 'description.xlsx'
        df_versions = pd.read_excel(excel_path2, sheet_name='Версии')
        df_versions['Дата'] = df_versions['Дата'].dt.strftime(r'%d.%m.%Y')
        df_info = pd.read_excel(excel_path2, sheet_name='Инфо')
        # 1. Словарь из df_versions (Номер -> Дата)
        #versions = dict(zip(df_versions['Номер'], df_versions['Дата']))
        versions = df_versions[['Номер', 'Дата']].to_dict('records')
        # 2. Словарь из df_info (Ключ -> Значение)
        info = dict(zip(df_info['Ключ'], df_info['Значение']))
        self._hardware = Hardware(versions, info)
    # метод для создания суммарной таблицы сигналов в docx
    def generate_sum_table_docx(self):
        doc = Document('origin_summ.docx')
        add_new_section_landscape(doc)
        p = doc.add_paragraph('Перечень сигналов ФСУ, предназначенных для конфигурирования устройства')
        p.style = 'ДОК Таблица Название'
        add_summ_table2(doc, isVirtKey=self._fsu.get_fsu_buttons(), isVirtSwitch=self._fsu.get_fsu_switches(), isStatuses=bool(self._fsu.get_fsu_statuses_sorted()),isSysStatuses=bool(self._fsu.get_fsu_sys_statuses_sorted()))
        doc.save("summ_table_templ.docx")
        doc2 = DocxTemplate("summ_table_templ.docx")
        # Формируем контекст для Jinja2
        context = {
            "fsu": self._fsu,
        }
        # Заполняем документ
        doc2.render(context)
        doc2.save("Таблица сигналов.docx")
    # метод для создания бланка уставок в docx файл
    def generate_setting_blanc_docx(self):
        if self._hardware is None:
            self._init_hardware_with_xlsx()
        create_template(self._fsu, self._hardware)
        fill_template(self._fsu, self._hardware)


    # ГЕТТЕРЫ И СЕТТЕРЫ
    def get_paths_to_tex(self):
        return self.paths

    def get_fsu(self):
        return self._fsu



path_to_latex_desc = r'E:\www4\ИЭУ Т 35 кВ Россети\04. Разработка РЭ\01. РЭ ЮНИТ-М3-ДЗТ2'
path_to_fsu = Path('fsu/')
fbs_list = ['TDIF', 'LVARCTOC']
re_ = ExploitationGuideLatex(path_to_latex_desc, path_to_fsu, fbs_list)

# 1. Обновляем таблицы с уставками в разделах РЭ
#re_.renew_setting_tables_re()

# 2. Обновляем суммарную таблицу сигналов приложения А в РЭ
#re_.renew_sum_table_latex()

# 3. Генерируем суммарную таблицу сигналов в docx
#re_.generate_sum_table_docx()

# 4. Генерируем бланк уставок в docx
re_.generate_setting_blanc_docx()   
