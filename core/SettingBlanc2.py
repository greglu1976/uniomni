# SettingBlanc2.py

import re
import json

from docxtpl import DocxTemplate, RichText
from docx import Document
from docx.enum.text import WD_BREAK

from utils.docx_handler import add_new_section, add_new_section_landscape
from utils.tables import add_table_final, add_table_settings_core4, add_table_mtrx_ins_core4, add_table_mtrx_outs_core4, add_table_leds_new_core4, add_table_fks_core4, add_table_binaries_core4, add_table_reg_core4

from logger.logger import Logger

from core.OrderHandler import OrderHandler
from core.MainConfigHandler import MainConfigHandler
from core.ExtensionHandler import ExtensionHandler

from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


class SettingBlanc:
    def __init__(self, device_data):
        Logger.info(f"Путь к пакетам поддержки: {device_data['path_to_support_packets']}")
        packet_path = device_data['path_to_support_packets']
        self.device_data = device_data
        self.code = self.device_data["setting_blanc_code"]
        self.versions = self.device_data["versions"]
        self.base_structure = None

        self.extension_handler = ExtensionHandler(packet_path)
        self.config_handler = MainConfigHandler.from_json_file(packet_path + "meta.json")
        self.order_handler = OrderHandler(self.config_handler, self.extension_handler, packet_path)

        self.di_list = []
        self.maps = self.order_handler.get_mapping()
        with open("abbr.json", 'r', encoding='utf-8') as f:
            self.abbr_dict = json.load(f)

    def _make_richtext(self, text):
        if not text:
            return RichText()
        text = text.replace('\\n', '\n')
        rt = RichText()
        parts = text.split('\n')
        for i, part in enumerate(parts):
            if i > 0:
                rt.add('\n')          # <-- замена здесь
            rt.add(part)
        return rt

    def _add_multiline_text_to_cell(self, cell, text):
        if not text:
            text = ""
        text = text.replace('\\n', '\n')
        paragraph = cell.paragraphs[0]
        paragraph.clear()
        parts = text.split('\n')
        for i, part in enumerate(parts):
            if i > 0:
                paragraph.add_run().add_break()
            paragraph.add_run(part)

    def _create_section_settings_core4(self, doc):
        if not self.base_structure:
            Logger.warning("Нет данных base_structure для генерации уставок")
            return

        add_new_section_landscape(doc)
        p = doc.add_paragraph('УСТАВКИ РЗиА')
        p.style = 'ДОК Заголовок 1'

        for func_block in self.base_structure:
            func_type = func_block.get('type')
            func_name = func_block.get('func_name', 'Без имени')

            fixed_func_name = func_name.split("_")[0]

            if "fsu-information" in fixed_func_name:
                fixed_func_name = "Общие уставки"

            if func_type == 'simple':
                p = doc.add_paragraph(self.abbr_dict.get(fixed_func_name, fixed_func_name))
                p.style = 'ДОК Заголовок 2'

                p = doc.add_paragraph(fixed_func_name)
                p.style = 'ДОК Таблица Название'

                if func_block.get('rows'):
                    table = add_table_settings_core4(doc)
                    self._fill_table_settings(table, func_block['rows'])

            elif func_type == 'complex':
                p = doc.add_paragraph(self.abbr_dict.get(fixed_func_name, fixed_func_name))
                p.style = 'ДОК Заголовок 2'

                for sub_func in func_block.get('sub_functions', []):
                    subtitle = sub_func.get('subtitle', '')

                    if subtitle:
                        p = doc.add_paragraph(subtitle)
                        p.style = 'ДОК Таблица Название'

                    if sub_func.get('rows'):
                        table = add_table_settings_core4(doc)
                        self._fill_table_settings(table, sub_func['rows'])
                        p = doc.add_paragraph().style = "TAGS"

    def _fill_table_settings(self, table, rows_data):
        for i, row_data in enumerate(rows_data, start=1):
            row = table.add_row()

            raw_col1 = row_data.get('col1', '')
            enum500 = self.extension_handler.find_enum_by_parameter_name(row_data.get('col0'))

            matches = list(re.finditer(r'\(([^()]*)\)', raw_col1))
            final_col1 = raw_col1
            final_col2 = ""

            if matches:
                last_match = matches[-1]
                extracted_text = last_match.group(1)
                final_col1 = raw_col1[:last_match.start()] + raw_col1[last_match.end():]
                final_col1 = final_col1.strip()
                final_col2 = extracted_text

            row.cells[0].text = str(i)
            row.cells[0].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            self._add_multiline_text_to_cell(row.cells[1], final_col1)

            col3_value = row_data.get('col3', '')
            if isinstance(col3_value, str) and col3_value.startswith('note_{'):
                col3_value = self._parse_note_dict(col3_value)
            if enum500:
                col3_value = " / ".join(item['VisibleValue'] for item in enum500)
            row.cells[2].text = col3_value
            row.cells[2].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            row.cells[3].text = row_data.get('col4', '')
            row.cells[3].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            row.cells[4].text = row_data.get('col5', '')
            row.cells[4].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            col6_value = row_data.get('col6', '')
            if enum500:
                lookup = {item['ParameterValue']: item['VisibleValue'] for item in enum500}
                try:
                    col6_value = lookup.get(int(col6_value), col6_value)
                except (ValueError, TypeError):
                    pass
            row.cells[5].text = str(col6_value)
            row.cells[5].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            for j in range(6, 10):
                row.cells[j].text = ''

            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(10)

        return table

    def _parse_note_dict(self, note_str):
        try:
            import ast
            if note_str.startswith('note_{'):
                dict_str = note_str[5:]
                note_dict = ast.literal_eval(dict_str)
                sorted_items = sorted(note_dict.items(), key=lambda item: int(item[0]) if item[0].isdigit() else item[0])
                values = [str(v) for k, v in sorted_items]
                return ' /\n'.join(values)
        except Exception as e:
            Logger.warning(f"Ошибка парсинга note_dict: {e}")
        return note_str

    def get_all_settings(self):
        ordered_fbs = list(self.maps.keys())
        base_structure = []
        for fb in ordered_fbs:
            fb_map = self.maps.get(fb)
            if not fb_map:
                continue
            json_data = self.order_handler.get_data_by_fb_name(fb_map)
            parsed_blocks = self.order_handler.parse_rza_structure(json_data, all_struct=0)
            base_structure.extend(parsed_blocks)
        self.base_structure = base_structure
        Logger.info(f"Загружено {len(base_structure)} блоков уставок")
        return base_structure

    def create_template(self):
        doc_tpl = DocxTemplate('origin.docx')
        last_version = ""
        colontile = ''
        if self.device_data['versions']:
            last_version = self.device_data['versions'][-1]
            colontile = f"Редакция {last_version['edition']} от {last_version['data']}"

        if "-ЮНИТ-" in self.config_handler.config_version:
            parts = self.config_handler.config_version.split("-ЮНИТ-", 1)
            first_part = parts[0]
            second_part = "ЮНИТ-" + parts[1]
        else:
            first_part = self.config_handler.config_version
            second_part = None

        context = {
            "title": self._make_richtext(self.device_data['full_description']),
            "code": self.device_data['setting_blanc_code'],
            "device_order_code": first_part,
            "hmi_order_code": second_part,
            "versions": self.device_data['versions'],
            "device_name": self.device_data['name'],
            "colontile": colontile,
            "packet": self.config_handler.model_version,
            "version": last_version['edition'],
            "date": last_version['data']
        }

        doc_tpl.render(context)
        doc_tpl.save('temp.docx')
        doc = Document('temp.docx')

        self.get_all_settings()
        Logger.info("Создаем раздел Уставки РЗиА...")
        self._create_section_settings_core4(doc)
        Logger.info("Создаем раздел Матрица входов и выходных реле...")
        self._create_section_inouts_core4(doc)

        if second_part:
            Logger.info("ИЧМ присутствует. Создаем раздел Настройка светодиодов и ФК...")
            self._create_section_leds_core4(second_part, doc)
        Logger.info("Создаем раздел Конфигурация...")
        self._create_section_config_core4(doc)
        Logger.info("Создаем раздел Настройка регистрации...")
        self._create_section_disturb_core4(doc)

        add_new_section(doc)
        add_table_final(doc)

        name_for_save = f"{self.code} Бланк уставок {self.device_data['name']} ред.{last_version['edition']}"
        doc.save(f'{name_for_save}.docx')
        Logger.info(f"Бланк уставок сохранен: '{name_for_save}.docx'")
        return doc

    def get_blanc(self):
        self.create_template()

    def _create_section_inouts_core4(self, doc):
        def extract_description(item):
            if isinstance(item, dict):
                return (item.get('fullDescription') or 
                        item.get('appliedDescription') or 
                        item.get('description') or 
                        item.get('name', ''))
            return str(item)
        
        raw_sigs, raw_gen_sigs = self.order_handler.get_fsu_signals() 
        sigs_list = [desc for desc in [extract_description(s) for s in raw_sigs] if desc]
        gen_signs = [desc for desc in [extract_description(s) for s in raw_gen_sigs] if desc]

        slots_data = self.order_handler.get_slots_data()
        items_to_process = []
        if isinstance(slots_data, list):
            for slot_dict in slots_data:
                items_to_process.extend(slot_dict.items())
        elif isinstance(slots_data, dict):
            items_to_process.extend(slots_data.items())

        pattern_inputs = re.compile(r'^M\d+_B\d{3}_B\d+_Status$')
        final_dict_inputs = {}
        for slot_name, params_list in items_to_process:
            status_signals = [p for p in params_list if pattern_inputs.match(p)]
            if not status_signals: continue
            clean_sig_list = []
            for sig in status_signals:
                try:
                    d = self.config_handler.get_param_info(sig)
                    desc = d.get("appliedDescription", sig)
                    clean_sig_list.append(desc.replace(". Статус", "").strip())
                except:
                    clean_sig_list.append(sig)
            if clean_sig_list:
                final_dict_inputs[slot_name] = clean_sig_list

        pattern_outputs = re.compile(r'^M\d+_K\d{3}_K\d+_Status$')
        final_dict_outputs = {}
        sigs_list_outputs = self.order_handler.get_fsu_out_signals()
        outs_list = self.extract_all_signals_from_structure(sigs_list_outputs)

        for slot_name, params_list in items_to_process:
            status_signals = [p for p in params_list if pattern_outputs.match(p)]
            if not status_signals: continue
            clean_sig_list = []
            for sig in status_signals:
                try:
                    d = self.config_handler.get_param_info(sig)
                    desc = d.get("appliedDescription", sig)
                    clean_sig_list.append(desc.replace(". Статус", "").strip())
                except:
                    clean_sig_list.append(sig)
            if clean_sig_list:
                final_dict_outputs[slot_name] = clean_sig_list

        if not final_dict_inputs and not final_dict_outputs:
            return

        add_new_section_landscape(doc) 
        p = doc.add_paragraph('МАТРИЦА ВХОДОВ И ВЫХОДНЫХ РЕЛЕ')
        p.style = 'ДОК Заголовок 1'

        if final_dict_inputs:
            doc.add_paragraph('Дискретные входы').style = 'ДОК Заголовок 2'
            sorted_inputs = sorted(final_dict_inputs.keys(), key=lambda x: int(re.search(r'M(\d+)', x).group(1)) if re.search(r'M(\d+)', x) else 0)
            for slot_name in sorted_inputs:
                doc.add_paragraph(f"{slot_name}").style = 'ДОК Таблица Название'
                add_table_mtrx_ins_core4(
                    doc=doc,
                    slot_name=slot_name,
                    inputs_list=final_dict_inputs[slot_name],
                    sigs=sigs_list, 
                    di_sigs=gen_signs
                )
                doc.add_paragraph()

        if final_dict_outputs:
            doc.add_paragraph('Выходные реле').style = 'ДОК Заголовок 2'
            sorted_outputs = sorted(final_dict_outputs.keys(), key=lambda x: int(re.search(r'M(\d+)', x).group(1)) if re.search(r'M(\d+)', x) else 0)
            for slot_name in sorted_outputs:
                doc.add_paragraph(f"{slot_name}").style = 'ДОК Таблица Название'
                add_table_mtrx_outs_core4(
                    doc=doc,
                    outputs_list=final_dict_outputs[slot_name],
                    sigs_list=outs_list
                )
                doc.add_paragraph()

        return

    def extract_all_signals_from_structure(self, data_structure):
        all_signals = []
        for function_item in data_structure:
            subfunctions = function_item.get('subfunctions', [])
            for subfunc in subfunctions:
                data_list = subfunc.get('data', [])
                for signal in data_list:
                    if signal:
                        all_signals.append(signal)
        return all_signals

    def _create_section_leds_core4(self, order_code, doc):
        parts = order_code.split('-')
        result = [
            "Модуль расширения 1 на 16 светодиодов" if parts[3]=="С" else "Модуль расширения 1 на 16 функциональных кнопок" if parts[3]=="К" else "Модуль отсутствует",
            "Модуль расширения 2 на 16 светодиодов" if parts[4]=="С" else "Модуль расширения 2 на 16 функциональных кнопок" if parts[4]=="К" else "Модуль отсутствует",
            "Модуль расширения 3 на 16 светодиодов" if parts[5]=="С" else "Модуль расширения 3 на 16 функциональных кнопок" if parts[5]=="К" else "Модуль отсутствует",
            "Модуль расширения 4 на 16 светодиодов" if parts[6]=="С" else "Модуль расширения 4 на 16 функциональных кнопок" if parts[6]=="К" else "Модуль отсутствует"
        ]

        add_new_section_landscape(doc)
        p = doc.add_paragraph('НАСТРОЙКА СВЕТОДИОДОВ И ФУНКЦИОНАЛЬНЫХ КЛАВИШ')
        p.style = 'ДОК Заголовок 1'
        p = doc.add_paragraph('Светодиоды')
        p.style = 'ДОК Заголовок 2'

        drop_list = self.order_handler.get_digital_signals_for_led()
        doc.add_paragraph("ИЧМ").style = 'ДОК Таблица Название'
        add_table_leds_new_core4(doc, drop_list)

        for res in result:
            if "светодиодов" in res:
                doc.add_paragraph()
                doc.add_paragraph(res).style = 'ДОК Таблица Название'
                add_table_leds_new_core4(doc, drop_list)                

        p = doc.add_paragraph('Функциональные клавиши')
        p.style = 'ДОК Заголовок 2'

        buttons_list = self.order_handler.get_fsu_hmi_buttons()
        doc.add_paragraph("ИЧМ").style = 'ДОК Таблица Название'        
        add_table_fks_core4(doc, buttons_list)

        for res in result:
            if "функциональных кнопок" in res:
                doc.add_paragraph()
                doc.add_paragraph(res).style = 'ДОК Таблица Название'
                add_table_fks_core4(doc, drop_list)  

    def enum_calc(self, enum, default):
        result_str = " / ".join([item['VisibleValue'] for item in enum])
        default_visible = None
        for item in enum:
            if str(item.get('ParameterValue')) == default:
                default_visible = item.get('VisibleValue')
                break
        return result_str, default_visible

    def parse_note(self, note, default):
        parts = [part.strip() for part in note.split(',')]
        values = []
        default_value = None
        for part in parts:
            if ' - ' in part:
                key_str, value = part.split(' - ', 1)
                key_str = key_str.strip()
                value = value.strip()
                values.append(value)
                if key_str == str(default):
                    default_value = value
        result_str = " / ".join(values)
        return result_str, default_value

    def _create_section_config_core4(self, doc):
        add_new_section(doc)
        p = doc.add_paragraph('КОНФИГУРАЦИЯ')
        p.style = 'ДОК Заголовок 1'

        raw_data = self.order_handler.get_data_for_configuration()

        for datum in raw_data:
            excluded_titles = {"ИЧМ", "Установка полномочий переключения на станционном уровне (LocSta)",
                               "Установка режима симуляции для получения GOOSE и SV от испытательных систем (Sim)",
                               "Синхронизация времени", "Модуль ЦП", "Параметры отладки",
                               "Слот M1. Модуль питания (P02c)", "Слот M12. Измерительный модуль (M090)",
                               "Слот M14. Центральный процессор (C01)"}
            if datum["main_title"] in excluded_titles:
                continue
            p = doc.add_paragraph(datum["main_title"])
            p.style = 'ДОК Заголовок 2'

            for table in datum["tables"]:
                doc.add_paragraph(table["title"]).style = 'ДОК Таблица Название'

                fixed_rows = []
                for row in table["rows"]:
                    row_name = row["name"]
                    row_data = self.config_handler.get_param_info(row_name)
                    enum_data = self.extension_handler.find_enum_by_parameter_name(row_name)

                    col1 = row_data["fullDescription"]
                    col2 = row_data["appliedDescription"]
                    col3 = row_data["note"] if row_data["note"].count('-') >= 2 else ""
                    col4 = row_data["units"] if row_data["units"] else '-'
                    col5 = row_data["step"] if row_data["step"] else '-'
                    col6 = row_data["defaultValue"]

                    if col3:
                        col3, col6 = self.parse_note(col3, col6)

                    if str(col6) == "false":
                        col3 = 'Вывод / Ввод'
                        col6 = "Вывод"
                    if str(col6) == "true":
                        col3 = 'Вывод / Ввод'
                        col6 = "Ввод"

                    if enum_data:
                        col3, col6 = self.enum_calc(enum_data, col6)
                        col4 = col5 = '-'
                    elif col3:
                        col4 = col5 = '-'
                    elif row_data["minValue"] is None:
                        col3 = '-'
                    else:
                        if row_data["minValue"] == "0" and row_data["maxValue"] == "1":
                            col3 = 'Вывод / Ввод'
                            col6 = "Вывод" if row_data["defaultValue"] == "0" else "Ввод"
                            col5 = '-'
                        else:
                            col3 = row_data["minValue"] + ' ... ' + row_data["maxValue"]

                    fixed_rows.append((col1, col2, col3, col4, col5, col6))

                add_table_binaries_core4(doc, fixed_rows)
                p = doc.add_paragraph()

    def _create_section_disturb_core4(self, doc):
        add_new_section_landscape(doc)
        p = doc.add_paragraph('НАСТРОЙКА РЕГИСТРАЦИИ')
        p.style = 'ДОК Заголовок 1'

        reg_data = self.order_handler.get_data_for_registration()

        for section in reg_data:
            p = doc.add_paragraph(section["main_title"])
            p.style = 'ДОК Заголовок 2'
            
            for subsection in section.get("subsections", []):
                _name = subsection["title"].split("_")[0]
                p_sub = doc.add_paragraph(self.abbr_dict.get(_name, _name))
                p_sub.style = 'ДОК Заголовок 3'
                
                for table_data in subsection["tables"]:
                    doc.add_paragraph(table_data["title"]).style = 'ДОК Таблица Название'
                    
                    data_rows = []
                    for param_name in table_data["parameters"]:
                        row_info = self.config_handler.get_param_info(param_name)
                        if row_info:
                            col1 = row_info.get("fullDescription", "")
                            col2 = row_info.get("appliedDescription", "")
                            param_type = row_info.get("type")
                            data_rows.append((col1, col2, param_type))
                    
                    if data_rows:
                        add_table_reg_core4(doc, data_rows)
                        doc.add_paragraph().style = 'TAGS'

    def get_table_settings_latex(self, fb_key):
        if not self.base_structure:
            self.get_all_settings()

        block = None
        for func_block in self.base_structure:
            if fb_key == func_block.get('func_name'):
                block = func_block
                break

        if not block:
            Logger.warning(f"Блок {fb_key} не найден")
            return None

        func_type = block.get('type', 'simple')
        
        def prepare_rows(rows_data):
            result_rows = []
            for row_data in rows_data:
                raw_col1 = row_data.get('col1', '')
                param_name = row_data.get('col0')
                enum500 = self.extension_handler.find_enum_by_parameter_name(param_name)

                matches = list(re.finditer(r'\(([^()]*)\)', raw_col1))
                final_col1 = raw_col1.strip()
                final_col2 = ""

                if matches:
                    last_match = matches[-1]
                    final_col2 = last_match.group(1)
                    final_col1 = (raw_col1[:last_match.start()] + raw_col1[last_match.end():]).strip()

                col3_value = row_data.get('col3', '')
                if enum500:
                    col3_value = " / ".join(item['VisibleValue'] for item in enum500)
                elif isinstance(col3_value, str) and col3_value.startswith('note_{'):
                    pass
                    
                col6_value = row_data.get('col6', '')
                if enum500:
                    lookup = {item['ParameterValue']: item['VisibleValue'] for item in enum500}
                    try:
                        col6_value = lookup.get(int(col6_value), col6_value)
                    except (ValueError, TypeError):
                        pass

                result_rows.append({
                    "col1": final_col1,
                    "col2": final_col2,
                    "col3": str(col3_value),
                    "col4": row_data.get('col4', ''),
                    "col5": row_data.get('col5', ''),
                    "col6": col6_value,
                    "col7": row_data.get('col7', ''),
                })
            return result_rows

        output = {
            "type": func_type,
            "func_name": block.get('func_name', fb_key)
        }

        if func_type == 'simple':
            if block.get('rows'):
                output["rows"] = prepare_rows(block['rows'])
            else:
                return None

        elif func_type == 'complex':
            subs = []
            for sub_func in block.get('sub_functions', []):
                if sub_func.get('rows'):
                    subs.append({
                        "subtitle": sub_func.get('subtitle', ''),
                        "rows": prepare_rows(sub_func['rows'])
                    })
            if subs:
                output["sub_functions"] = subs
            else:
                return None
        else:
            Logger.warning(f"Неизвестный тип блока {func_type} для {fb_key}")
            return None

        return output