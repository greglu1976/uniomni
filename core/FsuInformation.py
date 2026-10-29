"""Доступ к fsu-information.json пакета поддержки.

Файл описывает функциональную схему (ФСУ) и функциональные блоки устройства:
151 блок с иерархией (ParentId), русскими названиями (DisplayName) и
переменными. У переменных-уставок есть Min/Max/Step/DefaultValue/Units, причём
значения заданы в о.е. (в отличие от meta.json, где они в первичных единицах).

Используется как альтернативный (по умолчанию — основной) источник структуры
и данных для бланка уставок и таблиц РЭ.
"""

from collections import defaultdict

from logger.logger import Logger
from utils.paths import load_packet_json

SETTING_GROUP = "setting"
DEFAULT_SCHEMA_NAME = "ФСУ"


class FsuInformation:
    """Чтение fsu-information.json и сборка блоков уставок по ФБ."""

    def __init__(self, root_path=''):
        self.data, self.path = load_packet_json(root_path, "fsu-information.json")

        schema = self.data.get("FunctionalSchemaInformation") or {}
        self.schema_name = str(schema.get("Name") or DEFAULT_SCHEMA_NAME).strip()
        self.schema_variables = schema.get("Variables") or []

        self.blocks = self.data.get("FunctionalBlocksInformation") or []
        self._by_id = {block.get("Id"): block for block in self.blocks}
        self._children = defaultdict(list)
        for block in self.blocks:
            self._children[block.get("ParentId")].append(block)

    @classmethod
    def try_load(cls, root_path=''):
        """Загружает файл, если он есть в пакете; иначе None (без исключения)."""
        try:
            return cls(root_path)
        except FileNotFoundError:
            Logger.warning("В пакете поддержки нет fsu-information.json — "
                           "уставки будут взяты из GROUPING.json/meta.json")
            return None

    # ------------------------------------------------------------ выборки

    @property
    def root_blocks(self):
        """Функциональные блоки верхнего уровня (в порядке файла)."""
        return [block for block in self.blocks
                if block.get("ParentId") not in self._by_id]

    def child_blocks(self, block):
        return self._children.get(block.get("Id"), [])

    @staticmethod
    def _block_name(block):
        return str(block.get("DisplayName") or block.get("Name") or "").strip()

    @staticmethod
    def _iter_settings(variables):
        """Перебирает переменные-уставки: (имя, описание, переменная)."""
        for variable in variables or []:
            description = variable.get("Description") or {}
            group = str(description.get("Group") or "").strip().lower()
            if group == SETTING_GROUP:
                yield variable.get("Name"), description, variable

    def count_settings(self, block):
        return sum(1 for _ in self._iter_settings(block.get("Variables")))

    # ------------------------------------------------------------- блоки

    def get_blocks(self, build_row):
        """Собирает блоки уставок для бланка/РЭ.

        Args:
            build_row: функция (имя, описание из fsu, переменная) -> строка
                таблицы (dict col0..col7) или None, если строку пропускаем.

        Returns:
            Список блоков в структуре, совместимой с parse_rza_structure():
            {'type': 'simple'|'complex', 'func_name': ..., 'rows': [...]}
            и для complex — 'sub_functions': [{'subtitle': ..., 'rows': [...]}].
        """
        blocks = []

        schema_rows = self._rows(self.schema_variables, build_row)
        if schema_rows:
            blocks.append({
                "type": "simple",
                "func_name": self.schema_name,
                "rows": schema_rows,
            })

        for root in self.root_blocks:
            block = self._make_block(root, build_row)
            if block:
                blocks.append(block)

        Logger.info(f"fsu-information: блоков уставок {len(blocks)}")
        return blocks

    def _rows(self, variables, build_row):
        rows = []
        for name, description, variable in self._iter_settings(variables):
            row = build_row(name, description, variable)
            if row:
                rows.append(row)
        return rows

    def _subtree_rows(self, block, build_row):
        """Уставки блока и всех вложенных в него блоков."""
        rows = self._rows(block.get("Variables"), build_row)
        for child in self.child_blocks(block):
            rows.extend(self._subtree_rows(child, build_row))
        return rows

    def _make_block(self, block, build_row):
        name = self._block_name(block)
        direct_rows = self._rows(block.get("Variables"), build_row)

        sub_functions = []
        for child in self.child_blocks(block):
            child_rows = self._subtree_rows(child, build_row)
            if child_rows:
                sub_functions.append({
                    "subtitle": self._block_name(child),
                    "rows": child_rows,
                })

        if not direct_rows and not sub_functions:
            return None

        if not sub_functions:
            return {"type": "simple", "func_name": name, "rows": direct_rows}

        result = {"type": "complex", "func_name": name,
                  "sub_functions": sub_functions}
        if direct_rows:
            # Собственные уставки блока выводим отдельной таблицей,
            # чтобы не терять их (в GROUPING такие уставки сейчас пропадают).
            result["rows"] = direct_rows
        return result
