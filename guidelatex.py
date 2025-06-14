# Класс описывающий руководство по эксплуатации latex
import os
import re
from pathlib import Path

from fb2 import FB2
from fsu import FSU


class ExploitationGuideLatex:
    def __init__(self, path_to_latex_desc, path_to_fsu, fbs_list):
        self.path_to_latex_desc = path_to_latex_desc # путь к корневой папке проекта РЭ
        self.path_to_fsu = path_to_fsu # путь к корневой папке описания ФБ xlsx
        self.fbs_list = fbs_list # список имен ФБ для сборки ФСУ
        self.paths = [] # пути к файлам tex

        self._fsu = None

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
                    print(f"Найден тег: ln={ln}, fb={fb}, header='{header}'")

                    # Генерируем новое содержимое
                    latex_new = self._fsu.get_table_settings_latex(ln, fb, header)

                    # Собираем старое содержимое до %===t1
                    old_block = []
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

                elif line.startswith('%===t1*'):
                    # Сохраняем старый тег, если есть
                    new_content.append(line)
                    i += 1

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



    # ГЕТТЕРЫ И СЕТТЕРЫ
    def get_paths_to_tex(self):
        return self.paths

    def get_fsu(self):
        return self._fsu



path_to_latex_desc = r'E:\www4\ИЭУ Т 35 кВ Россети\04. Разработка РЭ\01. РЭ ЮНИТ-М3-ДЗТ2'
path_to_fsu = Path('fsu/')
fbs_list = ['TDIF', 'LVARCTOC']
re_ = ExploitationGuideLatex(path_to_latex_desc, path_to_fsu, fbs_list)

re_.renew_setting_tables_re()







