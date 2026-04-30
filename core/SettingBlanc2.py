# Класс, представляющий бланк уставок
# Требует инициализации
# для генерации бланка уставок в него нужно передать объект класса Device

from docxtpl import DocxTemplate
from docx import Document

from utils.docx_handler import add_new_section, add_new_section_landscape
from utils.tables import add_table_settings, add_table_mtrx_ins, add_table_mtrx_outs, add_table_leds_new, add_table_fks, add_table_binaries, add_table_reg, add_table_final, add_table_settings_core4

from xml.sax.saxutils import escape # для экранирования в дропдаун списке всяких << >>

from docxtpl import DocxTemplate

from logger.logger import Logger

from core.OrderHandler import OrderHandler

class SettingBlanc:
    def __init__(self, code='', versions=[{"edition":"X.X", "data": "XX.XX.XXXX"}]):
        self.code = code
        self.versions = versions
        self.base_structure = None  # Будет хранить структуру из get_all_settings()

    # НОВАЯ ФУНКЦИЯ ДЛЯ CORE4
    def _create_section_settings(self, doc):
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
        self.order_handler = OrderHandler()
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

    def create_template(self, device):
        """
        Создает шаблон для Core4 (без использования docxtpl)
        """
        # Получаем структуру уставок
        self.get_all_settings()
        
        # Создаем документ
        doc = Document('origin.docx')
        
        # Генерируем раздел уставок (новый метод)
        self._create_section_settings(doc)
        
        # Остальные разделы пока закомментированы, при необходимости аналогично адаптировать
        # self._create_section_inouts_core4(device.modules, doc)
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

    def get_blanc(self, device):
        """
        Основной метод для генерации бланка уставок Core4
        """
        self.create_template(device)


# Пример использования:
# blanc = SettingBlanc(code="ПМ-001", versions=[{"edition":"1.0", "data": "01.01.2025"}])
# blanc.get_blanc_core4(device)