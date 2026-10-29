# OrderHandler.py
# Обёртка вокруг файла порядка следования (GROUPING.json пакета поддержки
# ЮНИТ Сервис РЗА): уставки, сигналы, конфигурация, регистрация.

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from core.MainConfigHandler import MainConfigHandler
from core.UnitConverter import (
    DEFAULT_TIME_UNIT,
    DEFAULT_UNIT_TYPE,
    UnitConverter,
    format_value,
    normalize_unit_label,
    to_float,
)
from logger.logger import Logger
from utils.paths import load_packet_json

# Деревья GROUPING.json
TREE_SETTINGS = "SettingsTree"
TREE_CONFIGURATION = "ConfigurationTree"
TREE_DIGITAL_SIGNALS = "DigitalSignalsTree"
TREE_HARDWARE_INPUTS = "ParametersToHardwareDigitalInputsTree"
TREE_HARDWARE_OUTPUTS = "ParametersToHardwareDigitalOutputsTree"
TREE_HMI_BUTTONS = "ParametersToHmiButtonsTree"
TREE_HMI_SIGNALS = "ParametersToHmiSignalizationTree"
TREE_FB_LOGIC_INPUTS = "FunctionalBlockLogicInputsTree"

# Признаки служебных сигналов, которые не выводим в списках назначения
EXCLUDED_SIGNAL_MARKERS = (
    "Convert_SPS", "BitTest_", "_ACS_", "GOOSE_", "FB_", "HMI", "DI_",
    "APCSRst_CLS_Reset", "Convert_",
)


class NodeResolver:
    """Формирует читаемые пути вида «Группа / Подгруппа: Описание»."""

    def __init__(self, hard_nodes_structure, config_handler):
        self.config_handler = config_handler
        # Словарь для быстрого поиска: {"ParamName": ["Parent1", "Parent2"]}
        self._path_index = {}
        self._build_index(hard_nodes_structure or [])

    def _build_index(self, nodes, current_path=None):
        """Рекурсивно обходит структуру и сохраняет путь до каждого Parameter."""
        if current_path is None:
            current_path = []

        for node in nodes:
            if not isinstance(node, dict):
                continue

            name = node.get('Name')
            node_type = node.get('Type')

            if node_type == 'Parameter':
                self._path_index[name] = list(current_path)
            elif node_type == 'Group' and 'Nodes' in node:
                self._build_index(node['Nodes'], current_path + [name])

    def get_formatted_info(self, param_name: str) -> str:
        info = self.config_handler.get_param_info(param_name) or {}
        description = str(info.get("description") or "").strip()

        path_parts = self._path_index.get(param_name)
        prefix = " / ".join(path_parts) if path_parts else param_name

        if not description:
            return prefix

        # Убираем из описания все сегменты пути
        clean_desc = description
        if path_parts:
            # Сначала самые длинные сегменты: «ОУ1 ТЗНП» раньше, чем «ТЗНП»
            for part in sorted(path_parts, key=len, reverse=True):
                for sep in (": ", "/", " / ", ":"):
                    pattern = part + sep
                    while clean_desc.startswith(pattern):
                        clean_desc = clean_desc[len(pattern):].strip()
                if clean_desc.startswith(part) and (
                    len(clean_desc) == len(part)
                    or clean_desc[len(part)] in (' ', ':', '/')
                ):
                    clean_desc = clean_desc[len(part):].strip().lstrip(':').lstrip('/').strip()

        clean_desc = clean_desc.lstrip(':').lstrip('/').strip()
        return f"{prefix}: {clean_desc}" if clean_desc else prefix

    def get_all_formatted_info(self) -> List[str]:
        """Список строк «Группа / Подгруппа: Описание» для всех параметров."""
        return [self.get_formatted_info(name) for name in self._path_index]


class OrderHandler:

    def __init__(self, config_handler=None, extension_handler=None, root_path='',
                 unit_type=DEFAULT_UNIT_TYPE, time_unit=DEFAULT_TIME_UNIT,
                 convert_step=True):
        self.data, self.path = load_packet_json(root_path, "grouping.json")

        self.settings_group1 = []
        self._extrude_settings_group1()

        if config_handler:
            self.config_handler = config_handler
        else:
            meta, _ = load_packet_json(root_path, "meta.json")
            self.config_handler = MainConfigHandler(meta)

        self.extension_handler = extension_handler

        # Пересчёт значений уставок в выбранную систему единиц
        self.unit_type = unit_type or DEFAULT_UNIT_TYPE
        self.time_unit = time_unit or DEFAULT_TIME_UNIT
        # Преобразовывать ли шаг коэффициентом (для тестов можно выключить)
        self.convert_step = bool(convert_step)
        self.unit_converter = UnitConverter(
            self.config_handler, self.extension_handler,
            self.unit_type, self.time_unit)

        self.mapping = {}
        self._create_mapping_from_structure()

        self.fsu_signals = []
        self.fsu_di_signals = []
        self.fsu_out_signals = []
        self.resolver = None

        self.all_nodes_sigs = None
        self.general_sigs_of_func_logic = []

        # Кэш множеств имён параметров по деревьям (для is_in_*_tree)
        self._tree_names_cache = {}

    # ------------------------------------------------------------------ уставки

    def _extrude_settings_group1(self):
        """Извлекает структуру «Группа уставок 1» из GROUPING.json."""
        setting_tree = next(
            (node for node in self.data if node.get("Name") == TREE_SETTINGS), None)
        if setting_tree is None:
            raise ValueError(f"В grouping.json отсутствует дерево {TREE_SETTINGS}")

        settings = next(
            (node for node in setting_tree.get("Nodes", [])
             if node.get("Name") == "Группа уставок 1"), None)
        if settings is None:
            Logger.warning("В grouping.json нет группы «Группа уставок 1»")
            self.settings_group1 = []
            return

        self.settings_group1 = settings.get("Nodes", [])

    def get_data_by_fb_name(self, fb_name):
        for settings in self.settings_group1:
            if settings.get("Name") == fb_name:
                return settings
        return None

    def parse_options(self, options_str):
        """Парсит строку вида '0 - Вывод, 1 - По ЭМО1, ЭМО2' в словарь {код: текст}."""
        if not options_str:
            return {}

        result = {}
        pattern = r'(\d+)\s*[–—-]\s*(.*?)(?=\s*\d+\s*[–—-]|$)'
        for match in re.finditer(pattern, options_str):
            result[match.group(1)] = match.group(2).strip().rstrip(',')
        return result

    @staticmethod
    def _is_clean_step(step, max_significant=3) -> bool:
        """«Ровный» ли шаг (0,001 / 0,005 / 0,01 / 5).

        Только по такому шагу имеет смысл выравнивать число знаков после
        запятой. «Кривой» шаг (например, пересчитанный 8,333e-7 или
        0,00054645) выравнивание не задаёт — иначе диапазон и значение по
        умолчанию обрастали бы бессмысленными нулями.
        """
        try:
            value = Decimal(f"{float(step):.12g}").normalize()
        except (InvalidOperation, ValueError, TypeError):
            return False

        if value == 0:
            return False

        return len(value.as_tuple().digits) <= max_significant

    @staticmethod
    def _min_decimals(value, limit=8) -> int:
        """Минимум знаков после запятой, чтобы не потерять значение."""
        text = format_value(value)
        if 'e' in text:          # экспоненциальная запись — точность не критична
            return limit
        return len(text.split(',')[1]) if ',' in text else 0

    @staticmethod
    def _decimals_count(step) -> int:
        """Количество знаков после запятой в шаге уставки."""
        try:
            text = format(Decimal(str(step)).normalize(), 'f')
        except Exception:
            return 0
        return len(text.split('.')[1]) if '.' in text else 0

    def _format_step_value(self, value, decimals: int) -> str:
        try:
            return f"{float(value):.{decimals}f}".replace('.', ',')
        except (TypeError, ValueError):
            return str(value)

    def _conversion_needed(self, parameter_name) -> bool:
        """Нужен ли пересчёт значений этого параметра."""
        return self.unit_converter.scale_factor(parameter_name) is not None

    def _convert_number(self, parameter_name, raw_value):
        """Пересчитывает число (None, если значение не числовое)."""
        number = to_float(raw_value)
        if number is None:
            return None
        return self.unit_converter.convert(parameter_name, number)

    @staticmethod
    def _format_converted(value, decimals=None) -> str:
        """Форматирует пересчитанное значение с точностью по шагу.

        Число знаков после запятой задаётся шагом уставки (например, при шаге
        0,005 получаем «0,000...300,000»), поэтому нули НЕ отбрасываются:
        иначе диапазон и значение по умолчанию выглядели бы несогласованно.
        """
        if value is None:
            return '-'
        number = float(value)
        # Совсем малые величины в фиксированной записи дают «0» — показываем
        # экспоненту (например, шаг 4,5e-9 о.е.).
        if decimals is None or (number and abs(number) < 1e-6):
            return format_value(value)

        return f"{number:.{decimals}f}".replace('.', ',')

    def prepare_data_for_table(self, parameter_name, info=None, apply_conversion=True):
        """Строка таблицы уставок: (ключ, наименование, обозначение, диапазон,
        ед. изм., шаг, значение по умолчанию, пустое поле).

        Args:
            parameter_name: имя параметра (ключ в meta.json/EXTENSION.json).
            info: описание параметра; по умолчанию берётся из meta.json.
            apply_conversion: пересчитывать ли значения в выбранную систему
                единиц. Для источника fsu-information.json — False: там
                значения и шаг уже в о.е. и берутся как есть, без коэффициентов.
        """
        if info is None:
            info = self.config_handler.get_param_info(parameter_name)
        if not info:
            raise KeyError(f"Параметр отсутствует в meta.json: {parameter_name}")

        # Внешний источник (fsu-information.json): значения уже в своих единицах
        external_source = info is not None and not apply_conversion

        description = str(info.get("description") or "")
        short_description = description.split("_", 1)[1] if "_" in description else description

        col0 = parameter_name
        col1 = f"{info.get('fullDescription', '')} ({short_description}) "
        col2 = info.get("appliedDescription", "")

        note = str(info.get("note") or "")
        step = info.get("step")
        min_value = info.get("minValue")
        max_value = info.get("maxValue")
        default_value = info.get("defaultValue")

        options = {}
        is_sgf = bool(note)
        convert = apply_conversion and self._conversion_needed(parameter_name)

        # Пересчитанные значения (только для режима пересчёта)
        converted_min = converted_max = converted_default = converted_step = None
        if convert:
            converted_min = self._convert_number(parameter_name, min_value)
            converted_max = self._convert_number(parameter_name, max_value)
            converted_default = self._convert_number(parameter_name, default_value) if default_value else None
            converted_step = self._convert_number(parameter_name, step) if step else None

        # Точность диапазона и значения по умолчанию диктует шаг: пересчитанный,
        # если шаг пересчитывается, иначе исходный. Выравниваем только по
        # «ровному» шагу; дополнительно не теряем значащие цифры, если шаг
        # крупнее самих значений.
        decimals = None
        if external_source:
            step_for_decimals = step
        elif convert and self.convert_step and converted_step:
            step_for_decimals = converted_step
        else:
            step_for_decimals = step

        if step_for_decimals and self._is_clean_step(step_for_decimals):
            decimals = min(8, self._decimals_count(step_for_decimals))
            candidates = ([converted_min, converted_max, converted_default, min_value, max_value, default_value]
                          if not external_source else [min_value, max_value, default_value])
            for candidate in candidates:
                number = to_float(candidate)
                if number is not None:
                    decimals = max(decimals, self._min_decimals(number))
            decimals = min(8, decimals)

        def format_raw(raw_value):
            """Значение источника без пересчёта (точность — по шагу)."""
            number = to_float(raw_value)
            if number is None:
                return '' if raw_value is None else str(raw_value)
            return self._format_converted(number, decimals)

        # --- Значение / Диапазон ---
        if note:
            options = self.parse_options(note)
            col3 = "note_" + str(options)
        elif convert:
            if converted_min is not None and converted_max is not None:
                col3 = (f"{self._format_converted(converted_min, decimals)}..."
                        f"{self._format_converted(converted_max, decimals)}")
            else:
                col3 = '-'
        elif external_source:
            if min_value is not None and max_value is not None:
                col3 = f"{format_raw(min_value)}...{format_raw(max_value)}"
            else:
                col3 = '-'
        elif step and min_value is not None and max_value is not None:
            legacy_decimals = self._decimals_count(step)
            col3 = (f"{self._format_step_value(min_value, legacy_decimals)}..."
                    f"{self._format_step_value(max_value, legacy_decimals)}")
        elif min_value is not None and max_value is not None:
            col3 = f"{min_value}...{max_value}"
        else:
            col3 = '-'

        # --- Единицы измерения ---
        if external_source:
            col4 = normalize_unit_label(str(info.get("units") or "")) or "-"
        else:
            col4 = (self.unit_converter.unit_label(parameter_name)
                    or str(info.get("units") or "") or "-")

        # --- Шаг ---
        # При convert_step=False шаг берётся из meta.json как есть (без
        # коэффициента) — режим для проверки пересчёта.
        if note:
            col5 = "-"
        elif convert and self.convert_step and converted_step is not None:
            col5 = self._format_converted(converted_step, decimals)
        elif external_source:
            col5 = format_raw(step) if step else "-"
        elif step:
            col5 = self._format_step_value(step, self._decimals_count(step))
        else:
            col5 = "-"

        enum500 = self.extension_handler.find_enum_by_parameter_name(parameter_name)
        if enum500:
            col5 = "-"

        # --- Значение по умолчанию ---
        col6 = "-"
        if default_value:
            if is_sgf:
                # SGF-параметр: заменяем код на текстовое описание
                col6 = options.get(str(default_value), default_value)
            elif convert and converted_default is not None:
                col6 = self._format_converted(converted_default, decimals)
            elif external_source:
                col6 = format_raw(default_value)
            elif step:
                col6 = self._format_step_value(default_value, self._decimals_count(step))
            else:
                col6 = default_value

        return col0, col1, col2, col3, col4, col5, col6, ''

    def build_fsu_row(self, parameter_name, fsu_description, variable=None):
        """Строка таблицы по данным fsu-information.json (значения в о.е.).

        Коэффициенты не применяются: Min/Max/Step/DefaultValue и Units берутся
        из fsu как есть. Из meta.json добираются только справочные поля,
        которых в fsu нет (note с вариантами перечисления).

        По имени трансформации (Current/Voltage/Resistance) к значениям
        добавляется суффикс (Iном/Uном/Zном) и проставляется А (втор.)/
        В (втор.)/Ом (втор.). Для null-трансформации ед.изм. = о.е.
        """
        meta_info = self.config_handler.get_param_info(parameter_name) or {}
        transformation_name = fsu_description.get("Transformation")
        suffix, preferred_units = self._fsu_transformation_info(transformation_name)

        raw_units = str(fsu_description.get("Units") or "")
        # Если ответ не зависит от трансформации (null / time / любое другое) —
        # предпочтительные единицы имеют приоритет. Если их нет и raw_units
        # пустая — проставляем "о.е." (случай перечислений без Units в fsu).
        if preferred_units is not None:
            fsu_units = preferred_units
        elif raw_units:
            fsu_units = raw_units
        else:
            fsu_units = "о.е."

        info = {
            "name": parameter_name,
            "description": str(fsu_description.get("Description") or ""),
            "fullDescription": str(fsu_description.get("FullDescription") or ""),
            "appliedDescription": str(fsu_description.get("AppliedDescription") or ""),
            "units": fsu_units,
            "minValue": self._fsu_number(fsu_description.get("Min")),
            "maxValue": self._fsu_number(fsu_description.get("Max")),
            "step": self._fsu_number(fsu_description.get("Step")),
            "defaultValue": self._fsu_number(fsu_description.get("DefaultValue")),
            "note": meta_info.get("note") or "",
            "type": meta_info.get("type"),
        }

        try:
            col0, col1, col2, col3, col4, col5, col6, col7 = self.prepare_data_for_table(
                parameter_name, info=info, apply_conversion=False)
        except KeyError as error:
            Logger.warning(f"Строка уставки пропущена: {error}")
            return None

        # Если есть суффикс — добавляем Iном/Uном/Zном к значениям
        if suffix:
            col3 = self._apply_fsu_suffix(col3, suffix, use_parens=True)
            col5 = self._apply_fsu_suffix(col5, suffix, use_parens=False)
            col6 = self._apply_fsu_suffix(col6, suffix, use_parens=False)
            # Подпись единиц уже проставлена через preferred_units в info["units"]

        return {
            "col0": col0, "col1": col1, "col2": col2, "col3": col3,
            "col4": col4, "col5": col5, "col6": col6, "col7": col7,
        }


    @staticmethod
    def _fsu_transformation_info(transformation_name):
        """Определяет тип величины по имени трансформации.

        Returns:
            (suffix, unit_label) или (None, None) — если суффикс не нужен.
            suffix — 'Iном', 'Uном', 'Zном' или None.
            unit_label — 'А (втор.)', 'В (втор.)', 'Ом (втор.)', 'о.е.' или None (оставить как в fsu).
        """
        if transformation_name is None:
            return None, "о.е."
        if "Current" in transformation_name:
            return "Iном", "А (втор.)"
        if "Voltage" in transformation_name:
            return "Uном", "В (втор.)"
        if "Resistance" in transformation_name:
            return "Zном", "Ом (втор.)"
        # Время (Top_ms_s_min) и прочее — без изменений
        return None, None

    @staticmethod
    def _apply_fsu_suffix(value_str, suffix, use_parens):
        """Добавляет суффикс к строке значения.

        Если суффикса нет, возвращает строку без изменений.
        Для суффикса Iном/Uном/Zном:
          если use_parens=True: '(0,04...30,00)Iном'
          если use_parens=False: '0,01Iном'
        """
        if not suffix:
            return value_str
        text = str(value_str) if value_str is not None else ""
        if not text:
            return text
        if use_parens:
            # Диапазон вида "0,04...30,00" → "(0,04...30,00)Iном"
            if text.startswith('(') and text.endswith(')'):
                inner = text[1:-1]
                return f'({inner}){suffix}'
            else:
                return f'({text}){suffix}'
        else:
            # Шаг или значение по умолчанию: "0,01" → "0,01Iном"
            return f'{text}{suffix}'

    @staticmethod
    def _fsu_number(value):
        """Нормализует значение из fsu: False/True → 0/1, пустое → ''."""
        if value is None:
            return ''
        text = str(value).strip()
        if text in ("False", "false"):
            return '0'
        if text in ("True", "true"):
            return '1'
        return text

    def build_settings_blocks_from_fsu(self, fsu_information):
        """Блоки уставок по функциональным блокам из fsu-information.json."""
        return fsu_information.get_blocks(self.build_fsu_row)

    def parse_rza_structure(self, data: List[Dict[str, Any]], all_struct: bool = True) -> List[Dict[str, Any]]:
        """Преобразует дерево уставок в список блоков для генерации таблиц.

        all_struct=True — обрабатывается весь SettingsTree,
        all_struct=False — data уже является группой уставок/блоком.
        """

        def is_simple_group(node: Dict) -> bool:
            """Группа простая, если не содержит дочерних групп (только параметры)."""
            if not node.get('Nodes'):
                return True
            return not any(child.get('Type') == 'Group' for child in node['Nodes'])

        def create_row(param_name: str):
            try:
                col0, col1, col2, col3, col4, col5, col6, col7 = \
                    self.prepare_data_for_table(param_name)
            except KeyError as error:
                Logger.warning(f"Строка уставки пропущена: {error}")
                return None

            return {
                "col0": col0,   # обозначение ключа
                "col1": col1,   # наименование с кратким обозначением
                "col2": col2,   # обозначение ФСУ / ИЧМ
                "col3": col3,   # значение / диапазон
                "col4": col4,   # ед. изм.
                "col5": col5,   # шаг
                "col6": col6,   # значение по умолчанию
                "col7": col7,   # выставленное значение
            }

        def process_group(node: Dict) -> List[Dict]:
            result_blocks = []

            # Служебные группы не выводим
            name = node.get('Name', '')
            if name.startswith("GOOSE") or name.startswith("ВКл:"):
                return []

            if is_simple_group(node):
                rows = [create_row(child.get('Name', ''))
                        for child in node.get('Nodes', [])
                        if child.get('Type') == 'Parameter']
                result_blocks.append({
                    "type": "simple",
                    "func_name": name,
                    "rows": [row for row in rows if row],
                })
            else:
                complex_block = {
                    "type": "complex",
                    "func_name": name,
                    "sub_functions": [],
                }
                for child in node.get('Nodes', []):
                    if child.get('Type') != 'Group':
                        continue
                    sub_rows = [create_row(param.get('Name', ''))
                                for param in child.get('Nodes', [])
                                if param.get('Type') == 'Parameter']
                    complex_block["sub_functions"].append({
                        "subtitle": child.get('Name', ''),
                        "rows": [row for row in sub_rows if row],
                    })
                result_blocks.append(complex_block)

            return result_blocks

        final_output = []
        if not data:
            return final_output

        if all_struct:
            settings_tree = data[0]
            top_nodes = settings_tree.get('Nodes', [])
            if not top_nodes:
                return final_output

            for func_group in top_nodes[0].get('Nodes', []):
                if func_group.get('Type') == 'Group':
                    final_output.extend(process_group(func_group))
        else:
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get('Type') == 'Group':
                    final_output.extend(process_group(item))

        return final_output

    # ------------------------------------------------------------------ маппинг

    def _create_mapping_from_structure(self) -> Dict[str, str]:
        """Соответствие «имя ФБ в описании latex» → «имя группы в пакете поддержки».

        Для М500 имена верхних групп совпадают с обозначениями ФБ,
        поэтому маппинг — тождественный.
        """
        self.mapping = {
            group.get("Name"): group.get("Name")
            for group in self.settings_group1
            if isinstance(group, dict) and group.get("Name")
        }
        return self.mapping

    def get_setting_group1(self):
        return self.settings_group1

    def get_mapping(self):
        return self.mapping

    # ------------------------------------------------------------- сигналы ФСУ

    def _tree(self, tree_name):
        """Возвращает список узлов дерева по имени (или пустой список)."""
        for datum in self.data:
            if datum.get("Name") == tree_name:
                return datum.get("Nodes", [])
        Logger.warning(f"В grouping.json отсутствует дерево {tree_name}")
        return []

    def _drag_all_sigs_of_func_logic(self, tree_name=TREE_FB_LOGIC_INPUTS):
        self.all_nodes_sigs = self._tree(tree_name)

    def _drag_gen_sigs_of_func_logic(self, tree_name="MeasurementsTree"):
        for node in self._tree(tree_name):
            if node.get("Name") == "Сигналы функциональной логики":
                self.general_sigs_of_func_logic = node.get("Nodes", [])
                break

    def get_general_inputs(self, rza_nodes_names):
        """Общие сигналы (не относящиеся к конкретному ФБ) из дерева входов."""
        if self.resolver is None:
            self.resolver = NodeResolver(self._tree(TREE_HARDWARE_INPUTS),
                                         self.config_handler)
        result = []
        for inputs_node in self._tree(TREE_HARDWARE_INPUTS):
            if inputs_node.get("Name") in rza_nodes_names:
                continue
            for param_node in inputs_node.get("Nodes", []):
                result.append(self.resolver.get_formatted_info(param_node.get('Name')))
        return result

    def get_fsu_signals(self):
        """(сигналы ФБ логики, общие сигналы) для матрицы дискретных входов."""
        inputs_hard_nodes = self._tree(TREE_HARDWARE_INPUTS)
        self.resolver = NodeResolver(inputs_hard_nodes, self.config_handler)

        rza_nodes_names = []
        result = []
        for inputs_node in self._tree(TREE_FB_LOGIC_INPUTS):
            rza_nodes_names.append(inputs_node.get("Name"))
            for param_node in inputs_node.get("Nodes", []):
                result.append(self.resolver.get_formatted_info(param_node.get('Name')))

        gen_signs = self.get_general_inputs(rza_nodes_names)
        return result, gen_signs

    def get_fsu_hmi_buttons(self):
        """Список сигналов для функциональных клавиш."""
        resolver = NodeResolver(self._tree(TREE_HMI_BUTTONS), self.config_handler)
        return resolver.get_all_formatted_info()

    def get_fsu_out_signals(self):
        """Выходные сигналы функциональной логики, сгруппированные по функциям."""
        if self.fsu_out_signals:
            return self.fsu_out_signals

        def collect_flat_params(node):
            """Параметры размера 1 из узла и всех вложенных групп."""
            params = []
            for child in node.get("Nodes", []):
                if child.get("Type") == "Parameter":
                    info = self.config_handler.get_param_info(child.get("Name")) or {}
                    if info.get("size") == 1:
                        params.append(info.get("appliedDescription", ""))
                elif child.get("Type") == "Group":
                    params.extend(collect_flat_params(child))
            return params

        sigs_of_func_logic = []
        for node in self._tree(TREE_DIGITAL_SIGNALS):
            if node.get("Name") == "Сигналы функциональной логики":
                sigs_of_func_logic = node.get("Nodes", [])
                break

        functions_dict = {}
        for signal in sigs_of_func_logic:
            signal_name = signal.get("Name", "")

            if (signal_name == "Общие сигналы ФС"
                    or "GOOSE" in signal_name
                    or "ВКл:" in signal_name
                    or "ВКн:" in signal_name):
                continue

            function_name = signal_name.split("_")[0]
            subfunctions = [
                {"name": node.get("Name"), "data": collect_flat_params(node)}
                for node in signal.get("Nodes", [])
                if node.get("Type") == "Group"
            ]

            functions_dict.setdefault(
                function_name, {"function": function_name, "subfunctions": []}
            )["subfunctions"].extend(subfunctions)

        self.fsu_out_signals = list(functions_dict.values())
        return self.fsu_out_signals

    # --------------------------------------------------------------- слоты/платы

    def get_slots_data(self):
        """Параметры статусов по слотам (ключ — имя слота)."""
        slots = []
        for node in self._tree(TREE_DIGITAL_SIGNALS):
            if "Слот" not in node.get("Name", ""):
                continue

            param_names = []
            for item in node.get("Nodes", []):
                if item.get("Type") == "Parameter":
                    param_names.append(item.get("Name"))
                elif item.get("Type") == "Group":
                    param_names.extend(
                        nested.get("Name")
                        for nested in item.get("Nodes", [])
                        if nested.get("Type") == "Parameter"
                    )
            slots.append({node.get("Name"): param_names})

        return slots

    def get_digital_signals_for_led(self):
        """Список сигналов для назначения на светодиоды."""
        excluded_nodes = {"Обобщенные сигналы", "Периферийные блоки"}
        nodes = [node for node in self._tree(TREE_DIGITAL_SIGNALS)
                 if node.get("Name") not in excluded_nodes]

        signals = []
        for parameter_name in self.extract_parameters(nodes):
            info = self.config_handler.get_param_info(parameter_name)
            if not info:
                continue

            if "VirtualKey_" in parameter_name or "VirtualButton_" in parameter_name:
                parent_group = self.find_virt_key_desc(parameter_name)
                signals.append(f"{parent_group} ({info.get('appliedDescription', '')})")
                continue

            param_name = info.get("name", "")
            if info.get("size") != 1:
                continue
            if self.config_handler.is_group(info, "setting"):
                continue
            if any(marker in param_name for marker in EXCLUDED_SIGNAL_MARKERS):
                continue

            signals.append(info.get("appliedDescription", ""))

        return signals

    def extract_parameters(self, nodes):
        """Плоский список имён параметров из дерева групп."""
        if not isinstance(nodes, list):
            return []

        signal_names = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get('Type') == 'Parameter':
                if node.get('Name'):
                    signal_names.append(node['Name'])
            elif node.get('Type') == 'Group':
                signal_names.extend(self.extract_parameters(node.get('Nodes', [])))
        return signal_names

    def find_virt_key_desc(self, target_name):
        """Возвращает имя родительской группы для виртуальной кнопки/клавиши."""

        def search(nodes, parent_group_name=None):
            if not isinstance(nodes, list):
                return None
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if node.get('Type') == 'Group':
                    result = search(node.get('Nodes', []), parent_group_name=node.get('Name'))
                    if result:
                        return result
                elif node.get('Type') == 'Parameter' and node.get('Name') == target_name:
                    return parent_group_name
            return None

        return search(self.data)

    # ------------------------------------------------------------ конфигурация

    def get_data_for_configuration(self):
        """Сбор сигналов для раздела «Конфигурация» (структура для Word)."""
        exclude_nodes = {
            "Установка полномочий переключения на станционном уровне (LocSta)",
            "Установка режима симуляции для получения GOOSE и SV от испытательных систем (Sim)",
            "Синхронизация времени",
            "Модуль ЦП",
        }

        def is_excluded_by_pattern(name: str) -> bool:
            return (
                ("Слот" in name and "Измерительный модуль" in name)
                or ("Слот" in name and "Модуль питания" in name)
                or ("Слот" in name and "Центральный процессор" in name)
            )

        config_tree = self._tree(TREE_CONFIGURATION)
        if not config_tree:
            return []

        def process_node(node):
            node_name = node.get('Name', '')
            if node_name in exclude_nodes or is_excluded_by_pattern(node_name):
                return []

            if node.get('Type') != 'Group':
                return []

            children = node.get('Nodes', [])
            direct_params = [child for child in children if child.get('Type') == 'Parameter']
            sub_groups = [child for child in children if child.get('Type') == 'Group']

            nested_tables = []
            for sub_group in sub_groups:
                nested_tables.extend(process_node(sub_group))

            if direct_params:
                current_table = {
                    'title': node_name,
                    'rows': [{'name': param.get('Name'), 'value': ''}
                             for param in direct_params],
                }
                return [current_table] + nested_tables

            return nested_tables

        result = []
        for root_node in config_tree:
            root_name = root_node.get('Name', '')
            if (root_node.get('Type') == 'Group'
                    and root_name not in exclude_nodes
                    and not is_excluded_by_pattern(root_name)):
                tables = process_node(root_node)
                if tables:
                    result.append({'main_title': root_name, 'tables': tables})

        return result

    # -------------------------------------------------------------- регистрация

    def get_data_for_registration(self):
        """Структура раздела «Настройка регистрации»."""
        nodes = [node for node in self._tree(TREE_DIGITAL_SIGNALS)
                 if node.get("Name") != "Периферийные блоки"]
        return self.build_configuration_structure(nodes)

    def build_configuration_structure(self, data):
        """Формирует иерархию «раздел → подразделы → таблицы параметров»."""
        def process_group(group_node):
            group_name = group_node.get('Name')
            children = group_node.get('Nodes', [])

            direct_params = [child for child in children if child.get('Type') == 'Parameter']
            sub_groups = [child for child in children if child.get('Type') == 'Group']

            subsection = {'title': group_name, 'tables': []}

            if direct_params:
                subsection['tables'].append({
                    'title': group_name,
                    'parameters': [param.get('Name') for param in direct_params],
                })

            for sub_group in sub_groups:
                subsection['tables'].extend(process_group(sub_group)['tables'])

            return subsection

        result = []
        for root in [item for item in data if item.get('Type') == 'Group']:
            section = {'main_title': root.get('Name'), 'subsections': []}

            for child in root.get('Nodes', []):
                if child.get('Type') == 'Group':
                    section['subsections'].append(process_group(child))

            direct_params = [child for child in root.get('Nodes', [])
                             if child.get('Type') == 'Parameter']
            if direct_params:
                section['subsections'].append({
                    'title': root.get('Name'),
                    'tables': [{
                        'title': root.get('Name'),
                        'parameters': [param.get('Name') for param in direct_params],
                    }],
                })

            result.append(section)

        return result

    # ------------------------------------------------------- поиск по деревьям

    def _tree_parameter_names(self, tree_name):
        """Множество имён параметров дерева (строится один раз)."""
        cached = self._tree_names_cache.get(tree_name)
        if cached is not None:
            return cached

        names = set()
        stack = list(self._tree(tree_name))
        while stack:
            node = stack.pop()
            if not isinstance(node, dict):
                continue
            if node.get("Type") == "Parameter":
                names.add(node.get("Name"))
            if node.get("Nodes"):
                stack.extend(node["Nodes"])

        self._tree_names_cache[tree_name] = names
        return names

    def _is_in_tree(self, tree_name, parameter_name) -> bool:
        if not parameter_name:
            return False
        return parameter_name in self._tree_parameter_names(tree_name)

    def is_in_outputs_tree(self, parameter_name):
        return self._is_in_tree(TREE_HARDWARE_OUTPUTS, parameter_name)

    def is_in_inputs_tree(self, parameter_name):
        return self._is_in_tree(TREE_HARDWARE_INPUTS, parameter_name)

    def is_in_hmi_sign_tree(self, parameter_name):
        return self._is_in_tree(TREE_HMI_SIGNALS, parameter_name)

    def is_in_digit_sign_tree(self, parameter_name):
        return self._is_in_tree(TREE_DIGITAL_SIGNALS, parameter_name)
