from utils.paths import load_packet_json


class ExtensionHandler:
    """Доступ к EXTENSION.json пакета поддержки (перечисления, трансформации, единицы)."""

    def __init__(self, root_path=""):
        self.data, self.path = load_packet_json(root_path, "EXTENSION.json")

        # Индексы по имени: раньше на каждый вызов выполнялся линейный поиск
        # по списку из тысяч элементов, а вызывается это на каждую уставку.
        self._parameters = {
            item.get("Parameter"): item
            for item in self.data.get("Parameters", [])
        }
        self._enums = {
            item.get("Enum"): item
            for item in self.data.get("Enums", [])
        }
        self._transformations = {
            item.get("Transformation"): item
            for item in self.data.get("Transformations", [])
        }

    def _transformation_name(self, parameter_name):
        parameter = self._parameters.get(parameter_name) or {}
        return parameter.get("Transformation")

    def find_enum_by_parameter_name(self, name):
        """Возвращает список значений перечисления для параметра или None."""
        parameter = self._parameters.get(name) or {}
        enum_name = parameter.get("Enum")
        if not enum_name:
            return None

        enum = self._enums.get(enum_name)
        return enum.get("Value") if enum else None

    def find_transformation_by_parameter_name(self, name):
        """Возвращает описание трансформации параметра (или None)."""
        parameter = self._parameters.get(name) or {}
        return self._transformations.get(parameter.get("Transformation"))

    def find_trans_by_parameter_name(self, name):
        """Возвращает (единицы из InitialDeclarationUnits, "ед1 / ед2 / ...").

        Второй элемент — строка со всеми доступными единицами трансформации;
        если данных нет, оба элемента равны None.
        """
        transformation_name = self._transformation_name(name)
        if not transformation_name:
            return None, None

        transformation = self._transformations.get(transformation_name)
        if not transformation:
            return None, None

        available_units = [
            unit.get("Units", "")
            for unit in transformation.get("AvailableUnits", [])
        ]
        units_text = " / ".join(available_units)
        return transformation.get("InitialDeclarationUnits"), units_text

    def find_units_by_type(self, name, unit_type="Secondary"):
        """Возвращает строку с единицей нужного типа или None.

        unit_type: 'Primary' | 'Secondary' | 'Relative'
        """
        transformation_name = self._transformation_name(name)
        if not transformation_name:
            return None

        transformation = self._transformations.get(transformation_name)
        if not transformation:
            return None

        for unit in transformation.get("AvailableUnits", []):
            if unit.get("Type") == unit_type:
                return unit.get("Units")

        return None
