# класс обвертка вокруг файла порядка следования для ИЧМ, файл находится в данных ЮнитСервис
# и называется как func_order.json, GROUPING.json - в ЮНИТ СЕРВИС РЗА пакет поддержки

# В РАЗРАБОТКЕ

import json
from typing import List, Dict, Any
from collections import defaultdict

from core.MainConfigHandler import MainConfigHandler

class OrderHandler:

    def __init__(self, config_handler = None, root_path = ''):
        with open(root_path+"grouping.json", 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.settings_group1 = None
        self._extrude_settings_group1()

        if config_handler:
            self.config_handler = config_handler
        else:
            self.config_handler = MainConfigHandler.from_json_file("meta.json")

        self.mapping = {}
        self._create_mapping_from_structure()

        self.fsu_signals = []
        self.fsu_di_signals = []
        self.fsu_out_signals = []


        self.general_sigs_of_func_logic = [] # Общие сигналы функциональной логики вытащенные из GROUPING

    def _extrude_settings_group1(self):
        """Извлекает структуру 'Группа уставок 1' из JSON"""
        for root_node in self.data:
            if root_node.get("Name") == "SettingsTree":
                setting_tree = root_node
                break
        
        for nodes in setting_tree.get("Nodes", []):
            if nodes.get("Name") == "Группа уставок 1":
                settings = nodes
                break
        
        self.settings_group1 = settings.get("Nodes", []) if settings else []

    
    def get_settings_by_fb_name(self, fb_name):
        result = []
        for setting in self.settings_group1:
            if setting["Name"] == fb_name:
                settings = setting["Nodes"]
                for setting in settings:
                    result.append(setting["Name"])
        return result

    def get_data_by_fb_name(self, fb_name):
        for settings in self.settings_group1:
            if settings["Name"]!=fb_name:
                continue
            else:
                return settings
            
    def parse_options(self, options_str):
        """Парсит строку вида '0 - Вывод, 1 - По ЭМО1, ЭМО2' в словарь"""
        import re
        result = {}
        
        # Ищем все вхождения "цифра - значение" (значение может содержать запятые)
        # ?: - несохраняющая группа
        # \s*\d+\s*-\s* - цифра, тире с пробелами
        # (.*?) - значение (любые символы) лениво до...
        # (?=\s*\d+\s*-|$) - ...следующей цифры с тире или конца строки
        pattern = r'(\d+)\s*-\s*(.*?)(?=\s*\d+\s*-|$)'
        
        for match in re.finditer(pattern, options_str):
            key = match.group(1)
            value = match.group(2).strip().rstrip(',')
            result[key] = value
        
        return result


    def prepare_data_for_table(self, fb_name):
        raw = self.config_handler.get_param_info(fb_name)

        s = raw["description"]
        desc = "_".join(s.split("_", 1)[1:])
        col1 = raw["fullDescription"] + " (" + desc + ") "
        col2 = raw["appliedDescription"]
        col0 = fb_name
        
        op_dict = {}
        is_sgf = False
        # Форматирование col3
        if raw["note"] == '':
            # Форматируем min и max с учётом шага
            if raw["step"] and raw["step"] != '':
                step = float(raw["step"])
                # Определяем количество знаков после запятой
                step_str = str(step).rstrip('0').rstrip('.')
                decimals = len(step_str.split('.')[1]) if '.' in step_str else 0
                
                min_val = float(raw["minValue"])
                max_val = float(raw["maxValue"])
                min_formatted = f"{min_val:.{decimals}f}".replace('.', ',')
                max_formatted = f"{max_val:.{decimals}f}".replace('.', ',')
                col3 = f"{min_formatted}...{max_formatted}"
            else:
                # Шага нет - выводим как есть
                col3 = f"{raw['minValue']}...{raw['maxValue']}"
        else:
            col3 = raw["note"]
            op_dict = self.parse_options(col3)

            col3 ="note_"+str(op_dict)
            is_sgf = True

        
        col4 = "-" if raw["units"] == '' else raw["units"]
        
        # col5 - сохраняем старую логику: "-" если note не пустой, иначе step
        if raw["note"] != '':
            col5 = "-"
        else:
            if raw["step"] and raw["step"] != '':
                step = float(raw["step"])
                step_str = str(step).rstrip('0').rstrip('.')
                decimals = len(step_str.split('.')[1]) if '.' in step_str else 0
                col5 = f"{step:.{decimals}f}".replace('.', ',')
            else:
                col5 = "-"
        
        # col6 - форматируем defaultValue
        col6 = "-"
        if raw["defaultValue"] and raw["defaultValue"] != '':
            if is_sgf:
                # SGF параметр - заменяем код на текстовое описание
                col6 = op_dict.get(raw["defaultValue"], raw["defaultValue"])
            elif raw["step"] and raw["step"] != '':
                # Обычный параметр с шагом
                step = float(raw["step"])
                step_str = str(step).rstrip('0').rstrip('.')
                decimals = len(step_str.split('.')[1]) if '.' in step_str else 0
                default_val = float(raw["defaultValue"])
                col6 = f"{default_val:.{decimals}f}".replace('.', ',')
            else:
                # Обычный параметр без шага
                col6 = raw["defaultValue"]
        
        col7=''
        return col0, col1, col2, col3, col4, col5, col6, col7

    def parse_rza_structure(self, data: List[Dict[str, Any]], all_struct: bool = True) -> List[Dict[str, Any]]:
        """
        Преобразует структуру JSON РЗА в список блоков для шаблона Jinja2.
        Каждая уставка (параметр) становится отдельной строкой таблицы.
        all_struct = True если нужно прогнать весь файл с уставками, если отдельный ФБ - то all_struct=False, потом переделать автоматически определение структуры
        """
        
        def is_simple_group(node: Dict) -> bool:
            """
            Группа простая, если не содержит дочерних групп (только параметры).
            """
            if 'Nodes' not in node or not node['Nodes']:
                return True
            
            for child in node['Nodes']:
                if child.get('Type') == 'Group':
                    return False
            return True

        def create_row(param_name: str) -> Dict[str, str]:
            """
            Создает словарь для одной строки таблицы.
            col1 - Имя параметра (для поиска в БД)
            col2-col4 - заглушки для будущих данных (Значение, Ед.изм, Описание)
            """

            col0, col1, col2, col3, col4, col5, col6, col7 = self.prepare_data_for_table(param_name)

            return {
                "col0": col0, # обозначение ключа
                "col1": col1, 
                "col2": col2,  # Место для значения из БД
                "col3": col3,  # Место для ед. измерения
                "col4": col4,   # Место для описания
                "col5": col5,   # Место для описания
                "col6": col6,   # Место для значения по умолчанию
                "col7": col7  # Место для выставленного значения - для режимов
            }

        def process_group(node: Dict) -> List[Dict]:
            """
            Рекурсивная обработка. Возвращает список блоков.
            """
            result_blocks = []
            
            # --- ДОБАВЛЕННАЯ ПРОВЕРКА ---
            # Если имя самой группы (функции) начинается с "GOOSE", 
            # мы просто возвращаем пустой список, игнорируя всё внутри.
            if node.get('Name', '').startswith("GOOSE") or node.get('Name', '').startswith("ВКл:"):
                return [] 

            if is_simple_group(node):
                # --- ПРОСТАЯ ФУНКЦИЯ ---
                # Собираем все параметры в список строк
                rows = []
                if 'Nodes' in node:
                    for child in node['Nodes']:
                        if child.get('Type') == 'Parameter':
                            rows.append(create_row(child.get('Name', '')))
                
                result_blocks.append({
                    "type": "simple",
                    "func_name": node.get('Name', ''),
                    "rows": rows
                })
                
            else:
                # --- СЛОЖНАЯ ФУНКЦИЯ ---
                # Сама группа является контейнером для подфункций
                complex_block = {
                    "type": "complex",
                    "func_name": node.get('Name', ''),
                    "sub_functions": []
                }
                
                for child in node.get('Nodes', []):
                    if child.get('Type') == 'Group':
                        # Обрабатываем подгруппу
                        sub_rows = []
                        if 'Nodes' in child:
                            for param_node in child['Nodes']:
                                if param_node.get('Type') == 'Parameter':
                                    sub_rows.append(create_row(param_node.get('Name', '')))
                        
                        complex_block["sub_functions"].append({
                            "subtitle": child.get('Name', ''),
                            "rows": sub_rows
                        })
                    
                result_blocks.append(complex_block)
                
            return result_blocks

        # --- Основная точка входа ---
        final_output = []
        
        if not data:
            return final_output

        if all_struct:

            # 1. Находим корень SettingsTree
            settings_tree = data[0] 
            
            # 2. Находим первую группу уставок (например, "Группа уставок 1")
            top_nodes = settings_tree.get('Nodes', [])
            if not top_nodes:
                return final_output
                
            first_settings_group = top_nodes[0]
            # Перебираем функциональные группы
            functional_groups = first_settings_group.get('Nodes', [])
            for func_group in functional_groups:
                if func_group.get('Type') == 'Group':
                    blocks = process_group(func_group)
                    final_output.extend(blocks)
        
        else:
            # Режим: data - это уже группа уставок или отдельный блок
            if isinstance(data, list):
                for item in data:
                    if item.get('Type') == 'Group':
                        blocks = process_group(item)
                        final_output.extend(blocks)
            elif isinstance(data, dict) and data.get('Type') == 'Group':
                # Если передан один блок
                blocks = process_group(data)
                final_output.extend(blocks)
                    
        return final_output
    
    def _create_mapping_from_structure(self) -> Dict[str, str]:
        """Создаёт mapping префикс -> имя верхней группы (рекурсивно)"""
        
        mapping = {}
        
        def process_nodes(nodes, root_group_name):
            """Рекурсивно обходит узлы, сохраняя имя корневой группы"""
            if not nodes:
                return
                
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                    
                node_type = node.get('Type')
                
                # Если это Группа - спускаемся внутрь неё рекурсивно
                if node_type == 'Group':
                    # Важно: мы передаем то же самое root_group_name, 
                    # чтобы параметры внутри получили имя верхней группы (например, "ЛО Т_1")
                    process_nodes(node.get('Nodes', []), root_group_name)
                    
                # Если это Параметр
                elif node_type == 'Parameter':
                    param_name = node.get('Name', '')
                    if '_1_' not in param_name:
                        continue
                        
                    prefix = param_name.split('_1_')[0]
                    
                    # Пропускаем служебные
                    if prefix == "Номинальный ток входа":
                        continue
                    
                    # Добавляем в маппинг, если такого префикса еще нет
                    if prefix not in mapping:
                        mapping[prefix] = root_group_name

        # Основной цикл по верхнему уровню
        for group in self.settings_group1:
            if not isinstance(group, dict) or group.get('Type') != 'Group':
                continue
                
            group_name = group.get('Name', '')
            
            # Пропускаем служебные верхние группы
            if group_name.startswith("GOOSE") or group_name.startswith("ВКл:"):
                continue
            
            # Запускаем рекурсию для узлов этой группы
            process_nodes(group.get('Nodes', []), group_name)

        self.mapping = mapping
        return mapping


    def get_setting_group1(self):
        return self.settings_group1
    def get_mapping(self):
        return self.mapping


    # возвращает список дискретных сигналов 
    def _drag_gen_sigs_of_func_logic(self, tree_name = "MeasurementsTree"):
        for data in self.data:
            if data["Name"] == tree_name:
                m = data["Nodes"]
                for node in m:
                    if node["Name"] == "Сигналы функциональной логики":
                        self.general_sigs_of_func_logic = node["Nodes"]
                        break

    def get_fsu_signals(self):
        """
        Возвращает кортеж (fsu_signals, fsu_di_signals).
        fsu_signals: общие сигналы функциональной логики (для ФК, светодиодов и т.д.)
        fsu_di_signals: дискретные входы (DI_)
        """
        
        # 1. Если данные уже есть в кэше, возвращаем ОБА списка сразу
        # Важно: возвращаем кортеж, чтобы распаковка _, raw = ... работала всегда
        if self.fsu_signals is not None and self.fsu_di_signals is not None:
             # Проверка на пустоту списков может быть опасна, если сигналов действительно нет.
             # Лучше проверять флаг "инициализировано" или просто наличие списков.
             # Если списки были созданы в __init__ как [], то проверка if self.fsu_signals: 
             # вернет False для пустого списка, и код пойдет пересчитывать.
             # Поэтому лучше использовать отдельный флаг или проверять тип.
             
             # Вариант А: Если в __init__ они []:
             if self.fsu_signals or self.fsu_di_signals: 
                 return self.fsu_signals, self.fsu_di_signals
             # Если оба пустые, но мы уже ходили за данными, можно добавить флаг _signals_loaded
             # Но для простоты, если списки могут быть легитимно пустыми, лучше убрать этот блок
             # и полагаться на то, что пересчет быстрый, или использовать флаг.
             
             # Давайте используем более надежный подход с флагом, если он есть, 
             # или просто позволим коду выполниться один раз.
             # Ниже приведен стандартный паттерн с проверкой наличия данных.

        # Если мы здесь, значит нужно собрать данные
        # (или данные пустые, и мы хотим их обновить/собрать заново)
        
        # Очищаем списки перед сбором, чтобы не дублировать при повторном вызове
        self.fsu_signals = []
        self.fsu_di_signals = []

        if not self.general_sigs_of_func_logic:
            self._drag_gen_sigs_of_func_logic()

        gen_signals = []
        
        # Ищем нужный узел
        for o in self.general_sigs_of_func_logic:
            if o.get("Name") == "Общие сигналы ФС":
                gen_signals = o.get("Nodes", [])
                break # Нашли, выходим из цикла

        pass_data = ["GOOSE", "HMI_", "FB_", "BitTest_"] 
        
        for signal in gen_signals:
            try:
                sig_data = self.config_handler.get_param_info(signal["Name"])
            except Exception:
                continue

            # 1. Разделяем DI сигналы
            if "DI_" in sig_data.get("name", ""):
                self.fsu_di_signals.append(sig_data)
                continue

            # 2. Фильтры для остальных сигналов
            # Пропускаем команды и многобитные сигналы
            if sig_data.get("command") is True or sig_data.get("size", 1) != 1:
                continue
            
            # Пропускаем по префиксам
            if any(signal["Name"].startswith(prefix) for prefix in pass_data):
                continue
            
            # Пропускаем по содержимому имени
            if "HMI" in signal["Name"] or "ACS" in signal["Name"] or "APCSRst" in signal["Name"]:
                continue
            
            # Пропускаем конкретные имена
            if signal["Name"] in ["IRF", "Test", "Test_blocked", "Loc", "cError", "ncError"]:
                continue

            # Добавляем в основной список
            self.fsu_signals.append(sig_data)

        # ВСЕГДА возвращаем кортеж из двух элементов
        return self.fsu_signals, self.fsu_di_signals
    

    def get_fsu_out_signals(self):
        if self.fsu_out_signals:
            return self.fsu_out_signals

        # Находим "Сигналы функциональной логики"
        sigs_of_func_logic = []
        for data in self.data:
            if data["Name"] == "DigitalSignalsTree":
                m = data["Nodes"]
                for node in m:
                    if node["Name"] == "Сигналы функциональной логики":
                        sigs_of_func_logic = node["Nodes"]
                        break
                break

        def collect_subfunctions(nodes):
            """Рекурсивно собирает подфункции с их параметрами"""
            subfunctions = []
            
            for node in nodes:
                if node.get("Type") == "Group":
                    # Собираем параметры только для этой конкретной группы
                    params_data = []
                    for child in node.get("Nodes", []):
                        if child.get("Type") == "Parameter":
                            t = self.config_handler.get_param_info(child["Name"])
                            if t.get("size") == 1:
                                params_data.append(t.get("appliedDescription", ""))
                        elif child.get("Type") == "Group":
                            # Если внутри есть вложенные группы, рекурсивно собираем их
                            params_data.extend(collect_flat_params(child))
                    
                    subfunctions.append({
                        "name": node["Name"],
                        "data": params_data
                    })
            
            return subfunctions

        def collect_flat_params(node):
            """Собирает параметры из узла и всех его вложенных групп (плоский список)"""
            params = []
            for child in node.get("Nodes", []):
                if child.get("Type") == "Parameter":
                    t = self.config_handler.get_param_info(child["Name"])
                    if t.get("size") == 1:
                        params.append(t.get("appliedDescription", ""))
                elif child.get("Type") == "Group":
                    params.extend(collect_flat_params(child))
            return params

        # Словарь для группировки по функциям
        functions_dict = {}

        for signal in sigs_of_func_logic:
            signal_name = signal.get("Name", "")
            
            # Пропускаем ненужные сигналы
            if (signal_name == "Общие сигналы ФС" or 
                "GOOSE" in signal_name or 
                "ВКл:" in signal_name or 
                "ВКн:" in signal_name):
                continue

            function_name = signal_name.split("_")[0]

            # Собираем подфункции
            subfunctions = []
            if "Nodes" in signal:
                for node in signal["Nodes"]:
                    if node.get("Type") == "Group":
                        # Собираем параметры для этой подгруппы
                        params_data = collect_flat_params(node)
                        subfunctions.append({
                            "name": node["Name"],
                            "data": params_data
                        })

            # Группируем
            if function_name not in functions_dict:
                functions_dict[function_name] = {
                    "function": function_name,
                    "subfunctions": []
                }
            
            # Добавляем найденные подфункции
            functions_dict[function_name]["subfunctions"].extend(subfunctions)

        self.fsu_out_signals = list(functions_dict.values())
        return self.fsu_out_signals



    # Собираем данные по платам в слотах
    def get_slots_data(self):
        sigs_of_func_logic = []
        for data in self.data:
            if data["Name"] == "DigitalSignalsTree":
                m = data["Nodes"]
                for node in m:
                    if "Слот" in node["Name"]:
                        #print(node["Name"])
                        sigs = node["Nodes"]
                        #print(sigs)
                        
                        # Extract only parameter names
                        param_names = []
                        for item in sigs:
                            if item["Type"] == "Parameter":
                                param_names.append(item["Name"])
                            elif item["Type"] == "Group" and "Nodes" in item:
                                # If there are nested parameters in groups
                                for nested in item["Nodes"]:
                                    if nested["Type"] == "Parameter":
                                        param_names.append(nested["Name"])
                        
                        a = {
                            node["Name"]: param_names
                        }
                        sigs_of_func_logic.append(a)
                        
                break
        
        return sigs_of_func_logic


################################################################################
    #########################################################################
    # ДАННЫЕ ДЛЯ ВЫПАДАЮЩЕГО СПИСКА СВЕТОДИОДОВ
    def get_digital_signals_for_led(self):

        sigs_of_func_logic = []
        for data in self.data:
            if data["Name"] == "DigitalSignalsTree":
                m = data["Nodes"]
                for node in m:
                    if node["Name"] == "Обобщенные сигналы" or node["Name"] == "Периферийные блоки" :
                        continue
                    sigs_of_func_logic.append(node)
        q = self.extract_parameters(sigs_of_func_logic)

        raw_list = []
        for par in q:
            if "VirtualKey_" in par or "VirtualButton_" in par:
                raw = self.find_virt_key_desc(par)
                desc = self.config_handler.get_param_info(par)
                raw_list.append(f"{raw} ({desc['appliedDescription']})")
            else:
                raw = self.config_handler.get_param_info(par)
                if raw["size"]==1 and raw["group"]!="Setting" and "Convert_SPS" not in raw["name"] and "BitTest_" not in raw["name"] and "_ACS_" not in raw["name"] and "GOOSE_" not in raw["name"] and "FB_" not in raw["name"] and "HMI" not in raw["name"] and "DI_" not in raw["name"] and "APCSRst_CLS_Reset" not in raw["name"] and "Convert_" not in raw["name"]: 
                    raw_list.append(raw["appliedDescription"])
        return raw_list

    def extract_parameters(self, nodes):
        """
        Рекурсивная функция для извлечения только имен параметров (сигналов).
        
        Args:
            nodes (list): Список узлов (групп или параметров).
            
        Returns:
            list: Плоский список строк с именами сигналов.
        """
        signal_names = []
        
        if not isinstance(nodes, list):
            return signal_names

        for node in nodes:
            name = node.get('Name', '')
            node_type = node.get('Type', '')
            
            if node_type == 'Parameter':
                # Добавляем только имя сигнала
                if name: # Исключаем пустые имена, если такие возможны
                    signal_names.append(name)
            elif node_type == 'Group':
                # Рекурсивно обрабатываем вложенные узлы
                sub_nodes = node.get('Nodes', [])
                signal_names.extend(self.extract_parameters(sub_nodes))
                
        return signal_names

    def find_virt_key_desc(self, target_name):
        """
        Ищет параметр с именем target_name в структуре self.data
        и возвращает имя родительской группы.
        
        Args:
            target_name (str): Имя искомого параметра (например, "VirtualKey_1_FuncOperOut")
            
        Returns:
            str or None: Имя родительской группы или None, если не найдено.
        """
        # Внутренняя рекурсивная функция
        def _search_recursive(nodes, parent_group_name=None):
            if not isinstance(nodes, list):
                return None

            for node in nodes:
                name = node.get('Name')
                node_type = node.get('Type')
                sub_nodes = node.get('Nodes', [])

                # Если это группа, запоминаем её имя как потенциального родителя
                # и спускаемся глубже
                if node_type == 'Group':
                    result = _search_recursive(sub_nodes, parent_group_name=name)
                    if result:
                        return result
                
                # Если это параметр, проверяем имя
                elif node_type == 'Parameter':
                    if name == target_name:
                        # Возвращаем имя последней запомненной группы
                        return parent_group_name
            
            return None

        # Запуск поиска с корневого уровня
        # Для корневого элемента parent_group_name пока None, 
        # но так как структура начинается с Groups, первая найденная Group станет родителем
        return _search_recursive(self.data)


        

    # Сбор сигналов для раздела конфигурация !!!!!!!!!!!!!!! ДОРАБОТАТЬ !!!!!!!!!!!!!!!!!!!!
    def get_data_for_configuration(self):
        """
        Сбор сигналов для раздела конфигурация.
        Возвращает структуру для Word:
        [
            {
                'main_title': 'Название группы',
                'tables': [
                    {'title': 'Название подгруппы', 'rows': [{'name': 'параметр1', 'value': ''}, ...]},
                    ...
                ]
            },
            ...
        ]
        """
        # 1. Получаем дерево конфигурации
        config_tree = None
        for data in self.data:
            if data["Name"] == "ConfigurationTree":
                config_tree = data["Nodes"]
                break
        
        if not config_tree:
            return []
        
        # 2. Рекурсивный обход для построения структуры
        result = []
        
        def process_node(node, parent_group=None):
            """
            Рекурсивно обрабатывает узлы дерева.
            Возвращает список таблиц для текущей группы.
            """
            node_name = node.get('Name')
            node_type = node.get('Type')
            children = node.get('Nodes', [])
            
            if node_type == 'Group':
                # Группа может быть как контейнером для таблиц, так и самой таблицей
                
                # Сначала находим все параметры в этой группе (прямые дети)
                direct_params = [child for child in children if child.get('Type') == 'Parameter']
                # И все вложенные группы
                sub_groups = [child for child in children if child.get('Type') == 'Group']
                
                if direct_params:
                    # Если есть прямые параметры - создаем таблицу для этой группы
                    current_table = {
                        'title': node_name,
                        'rows': [{'name': param.get('Name'), 'value': ''} for param in direct_params]
                    }
                    
                    # Обрабатываем вложенные группы - они станут отдельными таблицами
                    nested_tables = []
                    for sub_group in sub_groups:
                        nested_result = process_node(sub_group, node_name)
                        if isinstance(nested_result, list):
                            nested_tables.extend(nested_result)
                        elif nested_result:
                            nested_tables.append(nested_result)
                    
                    # Возвращаем текущую таблицу + вложенные
                    return [current_table] + nested_tables if nested_tables else [current_table]
                
                elif sub_groups:
                    # Если параметров нет, но есть вложенные группы - просто обрабатываем их
                    all_tables = []
                    for sub_group in sub_groups:
                        sub_result = process_node(sub_group, node_name)
                        if isinstance(sub_result, list):
                            all_tables.extend(sub_result)
                        elif sub_result:
                            all_tables.append(sub_result)
                    return all_tables
                
                else:
                    # Пустая группа - игнорируем
                    return []
            
            return []
        
        # 3. Обрабатываем корневые узлы
        for root_node in config_tree:
            if root_node.get('Type') == 'Group':
                tables = process_node(root_node)
                if tables:
                    result.append({
                        'main_title': root_node.get('Name'),
                        'tables': tables
                    })
        
        return result
    
    # Сбор сигналов для раздела Настройка регистрации
    def get_data_for_registration(self):

        sigs_of_func_logic = []
        for data in self.data:
            if data["Name"] == "DigitalSignalsTree":
                m = data["Nodes"]
                for node in m:
                    if node["Name"] == "Периферийные блоки" :
                        continue
                    sigs_of_func_logic.append(node)
        #print(sigs_of_func_logic)
        return self.build_configuration_structure(sigs_of_func_logic)
        
    def build_configuration_structure(self, data):
        """
        Формирует структуру для вывода конфигурации в Word
        
        Returns:
            [
                {
                    'main_title': 'Название раздела',
                    'subsections': [  # <-- изменено: вместо tables теперь subsections
                        {
                            'title': 'Название подраздела (группы)',
                            'tables': [
                                {
                                    'title': 'Название таблицы',
                                    'parameters': ['параметр1', ...]
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                },
                ...
            ]
        """
        result = []
        
        root_groups = [item for item in data if item.get('Type') == 'Group']
        
        for root in root_groups:
            section = {
                'main_title': root.get('Name'),
                'subsections': []
            }
            
            def process_group(group_node, parent_path=""):
                """Рекурсивная обработка группы, возвращает структуру подразделов"""
                group_name = group_node.get('Name')
                children = group_node.get('Nodes', [])
                
                # Собираем прямые параметры группы
                direct_params = [child for child in children if child.get('Type') == 'Parameter']
                
                # Собираем вложенные группы
                sub_groups = [child for child in children if child.get('Type') == 'Group']
                
                # Текущий подраздел для этой группы
                subsection = {
                    'title': group_name,
                    'tables': []
                }
                
                # Если есть прямые параметры - создаем таблицу для них
                if direct_params:
                    subsection['tables'].append({
                        'title': group_name,  # таблица с тем же именем, что и группа
                        'parameters': [param.get('Name') for param in direct_params]
                    })
                
                # Рекурсивно обрабатываем вложенные группы
                for sub_group in sub_groups:
                    sub_subsection = process_group(sub_group)
                    # Добавляем таблицы из вложенной группы в текущий подраздел
                    subsection['tables'].extend(sub_subsection['tables'])
                
                return subsection
            
            # Обрабатываем все вложенные группы корневого раздела
            for child in root.get('Nodes', []):
                if child.get('Type') == 'Group':
                    subsection = process_group(child)
                    section['subsections'].append(subsection)
            
            # Также обрабатываем прямые параметры корневого раздела
            direct_params = [child for child in root.get('Nodes', []) if child.get('Type') == 'Parameter']
            if direct_params:
                section['subsections'].append({
                    'title': root.get('Name'),
                    'tables': [{
                        'title': root.get('Name'),
                        'parameters': [param.get('Name') for param in direct_params]
                    }]
                })
            
            result.append(section)
        
        return result