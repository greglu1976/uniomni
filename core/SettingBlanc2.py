# Класс, представляющий бланк уставок
# Требует инициализации
# для генерации бланка уставок в него нужно передать объект класса Device

import re

from docxtpl import DocxTemplate
from docx import Document

from utils.docx_handler import add_new_section, add_new_section_landscape
from utils.tables import add_table_settings, add_table_mtrx_ins, add_table_mtrx_outs, add_table_leds_new, add_table_fks, add_table_binaries, add_table_reg, add_table_final, add_table_settings_core4, add_table_mtrx_ins_core4, add_table_mtrx_outs_core4

from xml.sax.saxutils import escape # для экранирования в дропдаун списке всяких << >>

from docxtpl import DocxTemplate

from logger.logger import Logger

from core.OrderHandler import OrderHandler
from core.MainConfigHandler import MainConfigHandler

class SettingBlanc:
    def __init__(self, code='', versions=[{"edition":"X.X", "data": "XX.XX.XXXX"}]):
        self.code = code
        self.versions = versions
        self.base_structure = None  # Будет хранить структуру из get_all_settings()

        self.order_handler = OrderHandler()
        self.config_handler = MainConfigHandler.from_json_file("meta.json")


    # НОВАЯ ФУНКЦИЯ ДЛЯ CORE4
    def _create_section_settings_core4(self, doc):
        """Генерирует раздел уставок для Core4 с таблицами как в Core3"""
        if not self.base_structure:
            Logger.warning("Нет данных base_structure для генерации уставок")
            return
        
        add_new_section_landscape(doc)
        
        # Основной заголовок
        p = doc.add_paragraph('УСТАВКИ РЗиА')
        p.style = 'ДОК Заголовок 1'
        
        # Проходим по всем блокам
        for func_block in self.base_structure:
            func_type = func_block.get('type')
            func_name = func_block.get('func_name', 'Без имени')
            
            if func_type == 'simple':
                # Заголовок функции
                p = doc.add_paragraph(func_name)
                p.style = 'ДОК Заголовок 2'
                
                # Создаем и заполняем таблицу
                if func_block.get('rows'):
                    table = add_table_settings_core4(doc)
                    self._fill_table_settings(table, func_block['rows'])
            
            elif func_type == 'complex':
                # Заголовок составной функции
                p = doc.add_paragraph(func_name)
                p.style = 'ДОК Заголовок 2'
                
                # Проходим по подфункциям
                for sub_func in func_block.get('sub_functions', []):
                    subtitle = sub_func.get('subtitle', '')
                    
                    if subtitle:
                        p = doc.add_paragraph(subtitle)
                        p.style = 'ДОК Таблица Название'
                    
                    if sub_func.get('rows'):
                        table = add_table_settings_core4(doc)
                        self._fill_table_settings(table, sub_func['rows'])

    def _fill_table_settings(self, table, rows_data):
        """
        Заполняет таблицу уставок данными для Core4
        
        Логика обработки col1 (ПО ЮС):
        1. Если есть текст в скобках, например "Ввод функции в работу (Ввод_функции)",
        то "(Ввод_функции)" переносится в col2 (ИЧМ).
        2. Из col1 скобки и их содержимое удаляются.
        3. Старое значение col2 игнорируется/перезаписывается.
        """
        import re
        from docx.shared import Pt
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        
        # Добавляем строки с данными (начиная с row_index=2, т.к. 0 и 1 - заголовки)
        for i, row_data in enumerate(rows_data, start=1):
            row = table.add_row()
            
            # --- Обработка Ячейки 1 (ПО ЮС) и Ячейки 2 (ИЧМ) ---
            raw_col1 = row_data.get('col1', '')
            raw_col2 = row_data.get('col2', '') # Старое значение ИЧМ нам не нужно, но переменная нужна для логики
            
            # Ищем текст в круглых скобках в конце или в любом месте строки
            # Паттерн: открывающая скобка, любое содержимое (не жадное), закрывающая скобка
            match = re.search(r'\((.*?)\)', raw_col1)
            
            final_col1 = raw_col1
            final_col2 = "" # По умолчанию ИЧМ пуст, если скобок нет
            
            if match:
                # Извлекаем содержимое скобок (группа 1)
                extracted_text = match.group(1)
                # Удаляем найденную часть (скобки и содержимое) из исходной строки
                # Также убираем лишние пробелы, которые могли остаться перед скобками
                final_col1 = re.sub(r'\s*\(.*?\)', '', raw_col1).strip()
                # Переносим содержимое в ИЧМ
                final_col2 = extracted_text
            
            # --- Заполнение таблицы ---
            
            # Ячейка 0 (№) - номер по порядку
            row.cells[0].text = str(i)
            row.cells[0].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Ячейка 1 (ПО ЮС) - очищенное значение
            row.cells[1].text = final_col1
            
            # Ячейка 2 (ИЧМ) - значение из скобок (или пусто)
            row.cells[2].text = final_col2
            row.cells[2].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Ячейка 3 (Значение / Диапазон) - из col3 с обработкой note_
            col3_value = row_data.get('col3', '')
            if isinstance(col3_value, str) and col3_value.startswith('note_{'):
                col3_value = self._parse_note_dict(col3_value)
            row.cells[3].text = col3_value
            row.cells[3].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER 
            
            # Ячейка 4 (Ед. изм.) - из col4
            row.cells[4].text = row_data.get('col4', '')
            row.cells[4].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Ячейка 5 (Шаг) - из col5
            row.cells[5].text = row_data.get('col5', '')
            row.cells[5].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Ячейка 6 (Значение по умолчанию) - из col6
            row.cells[6].text = row_data.get('col6', '')
            row.cells[6].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Ячейки 7-10 (Группы уставок) - не заполняем
            row.cells[7].text = ''
            row.cells[8].text = ''
            row.cells[9].text = ''
            row.cells[10].text = ''
            
            # Устанавливаем размер шрифта
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
        
        return table
        
    
    def _parse_note_dict(self, note_str):
        """
        Парсит строку вида "note_{'0': 'Не предусмотрено', '1': 'Предусмотрено'}"
        в формат "Не предусмотрено / Предусмотрено"
        """
        try:
            import ast
            # Убираем "note_" в начале
            if note_str.startswith('note_{'):
                dict_str = note_str[5:]  # оставляем "{'0': '...', '1': '...'}"
                note_dict = ast.literal_eval(dict_str)
                
                # Извлекаем только значения и сортируем их по ключам, 
                # чтобы порядок был предсказуемым (0, 1, 2...), так как словари в старых Python не упорядочены,
                # а в новых хотя и сохраняют порядок вставки, но явная сортировка надежнее для конфигов.
                # Если ключи всегда строковые цифры, можно отсортировать как числа или как строки.
                sorted_items = sorted(note_dict.items(), key=lambda item: int(item[0]) if item[0].isdigit() else item[0])
                values = [str(v) for k, v in sorted_items]
                
                return ' /\n'.join(values)
        except Exception as e:
            Logger.warning(f"Ошибка парсинга note_dict: {e}")
        
        return note_str

    def get_all_settings(self):
        """Собирает структуру уставок из заказа"""

        self.maps = self.order_handler.get_mapping()
        
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

    def create_template(self, device_data):
        """
        Создает шаблон для Core4 (без использования docxtpl)
        """
       
        # Создаем документ
        #doc = Document('origin.docx')
        doc_tpl = DocxTemplate('origin.docx')

        colontile = ''
        if device_data['versions']:
            last_version = device_data['versions'][-1]
            colontile = f"Редакция {last_version['edition']} от {last_version['data']}"

        context = {
            "title": device_data['full_description'],
            "code": device_data['setting_blanc_code'],
            "device_order_code": device_data['order_code'],
            "hmi_order_code": device_data['order_code_hmi'],
            "versions":  device_data['versions'],
            "device_name":  device_data['name'],
            "colontile": colontile,
            "packet": self.config_handler.model_version
        }

        doc_tpl.render(context)
        doc_tpl.save('temp.docx')
        doc = Document('temp.docx')

        # Получаем структуру уставок
        self.get_all_settings()

        # Генерируем раздел уставок (новый метод)
        self._create_section_settings_core4(doc)
        self._create_section_inouts_core4(doc)


        self._create_section_leds_core4(device.modules, device.hmi, doc)
        # Остальные разделы пока закомментированы, при необходимости аналогично адаптировать
        # self._create_section_leds_core4(device.modules, device.hmi, doc)
        # self._create_section_config_core4(device.aux_funcs, doc)
        # self._create_section_disturb_core4(device.fsu, doc)
        
        # Добавляем финальную таблицу
        add_new_section(doc)
        add_table_final(doc)
        
        # Сохраняем
        name_for_save = f"{self.code} Бланк уставок Core4"
        doc.save(f'{name_for_save}.docx')
        Logger.info(f"Бланк уставок Core4 сохранен: '{name_for_save}.docx'")
        
        return doc

    def get_blanc(self, device_data):
        """
        Основной метод для генерации бланка уставок Core4
        """
        #print(device_data)
        self.create_template(device_data)


##################################################################################
#####################################################################################
####################################################################################


    # РАЗДЕЛ ПАРАМЕТРИРОВАНИЯ ВХОДОВ И ВЫХОДОВ
    def _create_section_inouts_core4(self, doc):
        """
        Генерирует раздел документации "Матрица входов и выходов".
        """
        import re
        
        # ======================================================================
        # ЧАСТЬ 0: Подготовка общих списков сигналов для Dropdown
        # ======================================================================
        try:
            raw_sigs, raw_di_sigs = self.order_handler.get_fsu_signals()
        except Exception:
            raw_sigs, raw_di_sigs = [], []

        def extract_description(item):
            if isinstance(item, dict):
                return (item.get('fullDescription') or 
                        item.get('appliedDescription') or 
                        item.get('description') or 
                        item.get('name', ''))
            return str(item)

        # Очищенные списки строк для dropdown
        sigs_list = [desc for desc in [extract_description(s) for s in raw_sigs] if desc]
        di_sigs_list = [desc for desc in [extract_description(s) for s in raw_di_sigs] if desc]

        # Получаем данные слотов один раз
        slots_data = self.order_handler.get_slots_data()
        items_to_process = []
        if isinstance(slots_data, list):
            for slot_dict in slots_data:
                items_to_process.extend(slot_dict.items())
        elif isinstance(slots_data, dict):
            items_to_process.extend(slots_data.items())

        # ======================================================================
        # ЧАСТЬ 1: ОБРАБОТКА ВХОДОВ (M*_B*_B*_Status)
        # ======================================================================
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

        # ======================================================================
        # ЧАСТЬ 2: ОБРАБОТКА ВЫХОДОВ (M*_K*_K*_Status)
        # ======================================================================
        pattern_outputs = re.compile(r'^M\d+_K\d{3}_K\d+_Status$')
        final_dict_outputs = {}
        
        sigs_list_outputs = self.order_handler.get_fsu_out_signals()
        
        outs_list = self.extract_all_signals_from_structure(sigs_list_outputs)

        for slot_name, params_list in items_to_process:
            print(slot_name, params_list)
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

        # ======================================================================
        # ЧАСТЬ 3: ГЕНЕРАЦИЯ ДОКУМЕНТА
        # ======================================================================
        if not final_dict_inputs and not final_dict_outputs:
            return

        add_new_section_landscape(doc) 
        
        p = doc.add_paragraph('МАТРИЦА ВХОДОВ И ВЫХОДНЫХ РЕЛЕ')
        p.style = 'ДОК Заголовок 1'

        # --- ГЕНЕРАЦИЯ ВХОДОВ ---
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
                    di_sigs=di_sigs_list
                )
                doc.add_paragraph()

        # --- ГЕНЕРАЦИЯ ВЫХОДОВ ---
        if final_dict_outputs:
            #print(final_dict_outputs)
            doc.add_paragraph('Выходные реле').style = 'ДОК Заголовок 2'
            
            sorted_outputs = sorted(final_dict_outputs.keys(), key=lambda x: int(re.search(r'M(\d+)', x).group(1)) if re.search(r'M(\d+)', x) else 0)
            
            for slot_name in sorted_outputs:
                doc.add_paragraph(f"{slot_name}").style = 'ДОК Таблица Название'
                # Вызываем новую функцию для выходов

                #print(sigs_list)
                add_table_mtrx_outs_core4(
                    doc=doc,
                    outputs_list=final_dict_outputs[slot_name],
                    sigs_list=outs_list
                )
                doc.add_paragraph()

        return


    def extract_all_signals_from_structure(self, data_structure):
        """
        Извлекает все сигналы из структуры данных функций и подфункций.
        
        :param data_structure: Список словарей с ключами 'function' и 'subfunctions'
        :return: Плоский список всех сигналов (desc)
        """
        all_signals = []
        
        for function_item in data_structure:
            # Получаем название функции (для контекста, если нужно)
            function_name = function_item.get('function', '')
            
            # Проходим по всем подфункциям
            subfunctions = function_item.get('subfunctions', [])
            for subfunc in subfunctions:
                subfunc_name = subfunc.get('name', '')
                
                # Извлекаем данные (сигналы) из подфункции
                data_list = subfunc.get('data', [])
                for signal in data_list:
                    if signal:  # Пропускаем пустые строки
                        all_signals.append(signal)
        
        return all_signals




    # РАЗДЕЛ СВЕТОДИОДОВ И ФК
    def _create_section_leds_core4(self, modules, hmi, fsu, doc):
        #if hmi.order_code=='': # Если ИЧМ не заказан, но раздел не формируем
            #return

        #############################################################################
        # СОЗДАЕМ РАЗДЕЛ НАСТРОЙКА СВЕТОДИОДОВ И ФУНКЦИОНАЛЬНЫХ КЛАВИШ
        add_new_section_landscape(doc) # Создаем раздел для матрицы вх/вых
        # Добавляем заголовок
        p = doc.add_paragraph('НАСТРОЙКА СВЕТОДИОДОВ И ФУНКЦИОНАЛЬНЫХ КЛАВИШ')
        p.style = 'ДОК Заголовок 1'

        ###############################################################
        p = doc.add_paragraph('Светодиоды')
        p.style = 'ДОК Заголовок 2'

        text = doc.add_paragraph('Для светодиода возможно подключение до пяти сигналов.')
        text.style = 'ДОК Текст'

        p = doc.add_paragraph(r'{% for leds in hmi.get_leds() if hmi.get_leds() %}')
        p.style = 'ДОК Текст'

        p = doc.add_paragraph(r'{{ leds }}')
        p.style = 'ДОК Таблица Название'

        statuses = fsu.get_statuses()
        statuses = sorted([item[0] for item in statuses])

        add_table_leds_new(doc, statuses, plates_data=modules.get_statuses())

        p = doc.add_paragraph(r'{% endfor %}')
        p.style = 'TAGS'    

        ###############################################################
        p = doc.add_paragraph('Функциональные клавиши')
        p.style = 'ДОК Заголовок 2'

        text = doc.add_paragraph('Для функциональной клавиши возможно подключение только одного управляющего сигнала.')
        text.style = 'ДОК Текст'

        p = doc.add_paragraph(r'{% for fks in hmi.get_fks() if hmi.get_fks() %}')
        p.style = 'ДОК Текст'

        p = doc.add_paragraph(r'{{ fks }}')
        p.style = 'ДОК Таблица Название'

        choices = fsu.get_controls()
        #choices = sorted(list(choices))
        choices = sorted([item[0] for item in choices])

        add_table_fks(doc, choices)

        p = doc.add_paragraph(r'{% endfor %}')
        p.style = 'TAGS'