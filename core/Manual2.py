# Manual2.py
# Класс, представляющий руководство по эксплуатации: обновление таблиц
# уставок, суммарной таблицы сигналов и перечня сокращений в latex-проекте.

import os
from pathlib import Path

from core.SettingBlanc2 import SettingBlanc
from core.UnitConverter import DEFAULT_TIME_UNIT, DEFAULT_UNIT_TYPE
from logger.logger import Logger
from utils.abbrs import start_abbr
from utils.latex import (escape_latex, escape_name, format_mark, format_numeric,
                         parse_note_to_latex)

START_SETTINGS_TAG = '%===m>'
END_SETTINGS_TAG = '%===m\n'
SUMM_TABLE_TAG = '%===t2\n'

class Manual:
    """Руководство по эксплуатации (РЭ) в формате latex."""

    def __init__(self, device_data, unit_type=DEFAULT_UNIT_TYPE,
                 time_unit=DEFAULT_TIME_UNIT, convert_step=True):
        self.device_data = device_data
        self.unit_type = unit_type
        self.time_unit = time_unit
        self.convert_step = bool(convert_step)
        self.path_to_latex_desc = device_data["path_to_latex_desc"]
        self.path_to_ru_desc = device_data["path_to_ru_desc"]

        self.setting_blanc = SettingBlanc(self.device_data, unit_type=unit_type,
                                          time_unit=time_unit,
                                          convert_step=convert_step)

    # --------------------------------------------------------------- утилиты

    def _read_lines(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.readlines()

    # ------------------------------------------------------- таблицы уставок

    def _render_latex_settings_block(self, settings_data):
        """Строки latex-таблицы уставок по данным одного ФБ."""
        def render_row(row):
            parts = [
                r'\centering ' + escape_name(row.get("col2")),
                r'\centering ' + parse_note_to_latex(row.get("col3")),
                r'\centering ' + format_numeric(row.get("col4"), escape_percent=True),
                r'\centering ' + format_numeric(row.get("col5")),
                r'\centering \arraybackslash ' + ("" if row.get("col6") is None else str(row.get("col6"))),
            ]
            return ' & '.join(parts) + ' \\\\\n'

        def is_simple(data):
            return data.get("type") == "simple"

        table = []
        if settings_data.get("type") not in ("simple", "complex"):
            Logger.warning(f"Неизвестный тип блока уставок: {settings_data.get('type')}")
            return table

        if is_simple(settings_data):
            for i, row in enumerate(settings_data.get("rows", [])):
                if i > 0:
                    table.append('\\hline\n')
                table.append(render_row(row))
            table.append('\\hline\n')
            return table

        for idx, sub in enumerate(settings_data.get("sub_functions", [])):
            subtitle = sub.get("subtitle", "")
            prefix = '' if idx == 0 else '\\hline\n'
            table.append(prefix + '\\multicolumn{5}{|c|}{ ' + escape_latex(subtitle)
                         + ' } \\\\ \\hline \n')

            for i, row in enumerate(sub.get("rows", [])):
                if i > 0:
                    table.append('\\hline\n')
                table.append(render_row(row))

        table.append('\\hline\n')
        return table

    def renew_setting_tables_re(self):
        """Обновляет таблицы уставок в приложении «Уставки» РЭ."""
        mapping = self.setting_blanc.maps

        path_to_desc = (self.device_data.get("path_to_latex_desc") or '').rstrip('/\\')
        if not path_to_desc:
            Logger.error("Error: path_to_latex_desc is empty or missing")
            return

        candidates = [
            os.path.join(path_to_desc, "Приложение. Уставки", "settings.tex"),
            os.path.join(path_to_desc, "Приложение. Уставки", "_latex", "appset.tex"),
        ]
        path = next((item for item in candidates if os.path.exists(item)), None)
        if path is None:
            Logger.error("Не найден файл уставок: " + " или ".join(candidates))
            return

        content = self._read_lines(path)
        new_content = []
        modified = False
        i = 0

        while i < len(content):
            line = content[i]

            if not line.startswith(START_SETTINGS_TAG):
                new_content.append(line)
                i += 1
                continue

            start_line = line
            i += 1

            # Собираем старое содержимое до закрывающего тега
            old_block = []
            closed = False
            while i < len(content):
                if content[i] == END_SETTINGS_TAG:
                    closed = True
                    break
                old_block.append(content[i])
                i += 1

            if not closed:
                # Незакрытый блок: файл повреждён, оставляем хвост как есть
                Logger.warning(f"Не найден закрывающий тег {END_SETTINGS_TAG.strip()!r} в {path}")
                new_content.append(start_line)
                new_content.extend(old_block)
                break

            new_content.append(start_line)

            fb, ln = self._parse_start_tag(start_line)
            mapped = mapping.get(fb, '-')
            if mapped == '-':
                Logger.warning(
                    f"Функциональный блок {fb} ({ln}) есть в описании latex, "
                    f"но отсутствует в файле поддержки устройства")
                new_content.extend(old_block)
            else:
                settings_data = self.setting_blanc.get_table_settings_latex(fb)
                latex_new = (self._render_latex_settings_block(settings_data)
                             if settings_data else [])

                if not latex_new:
                    Logger.error(f"Не найдено уставок для ФБ: {fb}, Функция: {ln}.")
                    new_content.extend(old_block)
                elif "".join(old_block) != "".join(latex_new):
                    Logger.info(f"Контент отличается - будет обновлён. "
                                f"ФБ: {fb}, функция: {ln}, блок: {settings_data.get('func_name')}")
                    new_content.extend(latex_new)
                    modified = True
                else:
                    Logger.info("Контент не изменился - пропускаем обновление.")
                    new_content.extend(old_block)

            new_content.append(END_SETTINGS_TAG)
            i += 1  # пропускаем закрывающий тег

        if modified:
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(new_content)
            Logger.info(f"Файл обновлён: {path}")
        else:
            Logger.info(f"Изменений в файле нет: {path}")

    @staticmethod
    def _parse_start_tag(raw_tag):
        """Парсит тег '%===m>FB|Функция' → (FB, Функция)."""
        parts = raw_tag[6:].split('|')
        if len(parts) not in (1, 2):
            raise ValueError(f"Неверный формат тега: {raw_tag}")

        path_part = parts[0].strip()
        function_name = parts[1].strip() if len(parts) == 2 and parts[1].strip() else "-"
        return path_part, function_name

    # --------------------------------------------- суммарная таблица сигналов

    @staticmethod
    def _blocks_are_equivalent(block1, block2):
        """Сравнивает блоки по содержанию, игнорируя форматирование."""
        def normalize(lines):
            return ' '.join(' '.join(lines).split())

        return normalize(block1) == normalize(block2)

    def renew_sum_table_latex(self):
        """Обновляет суммарную таблицу сигналов (приложение А) в РЭ."""
        path_to_tex = (Path(self.device_data["path_to_latex_desc"])
                       / "Приложение. Сигналы" / "_latex" / "appsign.tex")

        if not path_to_tex.exists():
            Logger.error(f"Файл описания приложения суммарных сигналов не найден: {path_to_tex}")
            return

        content = self._read_lines(path_to_tex)
        new_content = []
        modified = False
        i = 0

        while i < len(content):
            line = content[i]

            if line != SUMM_TABLE_TAG:
                new_content.append(line)
                i += 1
                continue

            new_content.append(line)
            i += 1

            old_block = []
            while i < len(content) and content[i] != SUMM_TABLE_TAG:
                old_block.append(content[i])
                i += 1

            latex_new = self._generate_summ_table_latex()

            if not latex_new:
                Logger.warning("Сгенерирована пустая таблица суммарных сигналов! Оставляем старую.")
                new_content.extend(old_block)
            elif not self._blocks_are_equivalent(old_block, latex_new):
                Logger.info("Контент отличается - будет обновлён.")
                new_content.extend(latex_new)
                modified = True
            else:
                Logger.info("Контент не изменился - пропускаем обновление.")
                new_content.extend(old_block)

            new_content.append(SUMM_TABLE_TAG)  # закрывающий тег
            if i < len(content):
                i += 1  # пропускаем оригинальный закрывающий тег

        if modified:
            with open(path_to_tex, 'w', encoding='utf-8') as file:
                file.writelines(new_content)
            Logger.info(f"Файл обновлён: {path_to_tex}")
        else:
            Logger.info(f"Изменений в файле нет: {path_to_tex}")

    def _generate_summ_table_latex(self):
        """Генерирует строки суммарной таблицы сигналов для latex."""
        def generate_row(row):
            cells = [
                r'\raggedright ' + escape_name(row[0]),
                r'\centering ' + escape_name(row[1]),
            ]
            cells.extend(r'\centering ' + format_mark(value) for value in row[2:8])
            cells.append(r'\centering \arraybackslash ' + format_mark(row[8]))
            return ' & '.join(cells) + ' \\\\ \\hline\n'

        table = []
        reg_data = self.setting_blanc.order_handler.get_data_for_registration()

        for section in reg_data:
            if section["main_title"] != "Сигналы функциональной логики":
                continue

            for subsection in section.get("subsections", []):
                name = subsection["title"].split("_")[0]
                if "GOOSE" in name or "Блок измерений" in name:
                    continue

                header = self.setting_blanc.abbr_dict.get(name, name)
                table.append('\\rowcolor{gray!10}\n')
                table.append(f'\\multicolumn{{9}}{{c}}{{{header}}} \\\\\n\\hline\n')

                for table_data in subsection["tables"]:
                    self._append_summ_subtable(
                        table, table_data, header_needed=header,
                        subsection_title=subsection["title"])

        return table

    def _append_summ_subtable(self, table, table_data, header_needed, subsection_title):
        """Добавляет в таблицу подраздел (таблицу) сигналов."""
        title = table_data["title"]
        header2 = title.replace('_', r'\_')

        if (title != 'БУ'
                and header_needed != header2
                and subsection_title != title):
            table.append('\\rowcolor{gray!5}\n')
            table.append(f'\\multicolumn{{9}}{{c}}{{{header2}}} \\\\\n\\hline\n')

        data_rows = []
        for param_name in table_data["parameters"]:
            row_info = self.setting_blanc.config_handler.get_param_info(param_name)
            if not row_info:
                continue

            full_description = row_info.get("fullDescription", "")
            applied_description = row_info.get("appliedDescription", "")
            if row_info.get("type") != 3:
                continue
            if str(applied_description).startswith(('MMS', 'GOOSE', 'ИЧМ', 'АСУ:')):
                continue

            order_handler = self.setting_blanc.order_handler
            in_outputs = order_handler.is_in_outputs_tree(param_name)
            in_inputs = order_handler.is_in_inputs_tree(param_name)
            in_hmi = order_handler.is_in_hmi_sign_tree(param_name)
            in_digital = order_handler.is_in_digit_sign_tree(param_name)

            is_function_key = str(applied_description).startswith('ФК:')
            data_rows.append((
                full_description,
                applied_description,
                "+" if in_inputs else "-",
                "+" if in_outputs else "-",
                "+" if in_hmi else "-",
                "+" if is_function_key else "-",
                "+" if in_digital else "-",
                "+" if in_digital else "-",
                "+" if in_digital else "-",
            ))

        for row in data_rows:
            table.append(self._generate_summ_row(row))

    def _generate_summ_row(self, row):
        cells = [
            r'\raggedright ' + escape_name(row[0]),
            r'\centering ' + escape_name(row[1]),
        ]
        cells.extend(r'\centering ' + format_mark(value) for value in row[2:8])
        cells.append(r'\centering \arraybackslash ' + format_mark(row[8]))
        return ' & '.join(cells) + ' \\\\ \\hline\n'

    # ------------------------------------------------------------ сокращения

    def renew_abbrs(self):
        path_to = Path(self.path_to_latex_desc) / '_manual_latex' / 'general.pdf'
        Logger.info(str(path_to))
        return start_abbr(path_to)

    def renew_abbrs_ru(self):
        if not self.path_to_ru_desc:
            Logger.error("Пустой путь к pdf с уставками!")
            return 1
        path_to = Path(self.path_to_ru_desc)
        Logger.info(str(path_to))
        start_abbr(path_to)
        return 0
