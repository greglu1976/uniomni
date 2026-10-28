"""Пересчёт значений уставок между системами единиц пакета поддержки.

Данные для пересчёта целиком берутся из EXTENSION.json (описание трансформаций)
и meta.json (значения параметров-коэффициентов):

* `Units` / `Type` — система единиц: Primary (первичные), Secondary (вторичные),
  Relative (о.е.), MultiplicationCoefficient (множители времени);
* `Coefficient` — масштаб единицы отображения (например, 0.001 для «кВ» и «сек»);
* `CoefficientParameter` — параметр-коэффициент (CtRatio; для сопротивления —
  отношение Kтн/Kтт, для времени отсутствует);
* `BasisParameter` — базовое значение (NominalSecondaryValue).

Модель пересчёта (проверена на пакете М500):

    base   = value / P            # приведение к вторичным единицам
    target = base * f             # f зависит от типа единиц:
        Primary   -> P * C        # первичные, с масштабом единицы (В -> кВ)
        Secondary -> C            # вторичные
        Relative  -> 1 / B        # о.е.
        MultiplicationCoefficient -> C

Примеры: 2400 А (первич.) -> 2 А (вторич.) -> 2 о.е.;
22000 В (первич., «кВ») -> 22 кВ -> 10 В (вторич.) -> 0.1 о.е.;
549 Ом (первич.) -> 300 Ом (вторич.) -> 3 о.е.; 1000 мс -> 1 сек.
"""

import math
from decimal import Decimal, localcontext

from logger.logger import Logger

UNIT_TYPE_PRIMARY = "Primary"
UNIT_TYPE_SECONDARY = "Secondary"
UNIT_TYPE_RELATIVE = "Relative"
UNIT_TYPE_MULTIPLIER = "MultiplicationCoefficient"

# Человекочитаемые названия для интерфейса
UNIT_TYPE_TITLES = {
    UNIT_TYPE_PRIMARY: "Первичные",
    UNIT_TYPE_SECONDARY: "Вторичные",
    UNIT_TYPE_RELATIVE: "Относительные (о.е.)",
}

# По умолчанию — вторичные (как было настроено в TARGET_UNIT_TYPE)
DEFAULT_UNIT_TYPE = UNIT_TYPE_SECONDARY


def to_float(value, default=None):
    """Приводит значение из JSON/meta к float (или возвращает default)."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace(',', '.')
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def format_value(value, significant_digits=6):
    """Форматирует число для таблицы: до N значащих цифр, с запятой.

    Длинные хвосты после пересчёта (0.45454545…) не нужны в бланке,
    поэтому ограничиваем число значащих цифр и убираем лишние нули.
    """
    if value is None:
        return '-'
    if isinstance(value, str):
        return value

    number = float(value)
    if number == 0:
        return '0'

    # Очень маленькие/большие величины (например, шаг уставки после пересчёта
    # в о.е.) в обычной записи превращаются в «0» — показываем экспоненту.
    if abs(number) < 1e-6 or abs(number) >= 1e7:
        mantissa, exponent = f"{number:.3e}".split('e')
        mantissa = mantissa.rstrip('0').rstrip('.')
        return f"{mantissa}e{int(exponent)}".replace('.', ',')

    exponent = math.floor(math.log10(abs(number)))
    decimals = max(0, min(8, significant_digits - 1 - exponent))
    text = f"{number:.{decimals}f}"
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text.replace('.', ',') or '0'


def format_decimal(value, significant_digits=6):
    """Как format_value, но через Decimal — без потери точности на краях."""
    if value is None:
        return '-'
    if isinstance(value, str):
        return value
    try:
        with localcontext() as context:
            context.prec = significant_digits
            number = +Decimal(str(float(value)))
    except (ArithmeticError, ValueError):
        return format_value(value, significant_digits)

    text = format(number.normalize(), 'f')
    return text.replace('.', ',')


class UnitScale:
    """Одна система единиц конкретной трансформации."""

    __slots__ = ("label", "unit_type", "coefficient",
                 "coefficient_parameter", "coefficient_value",
                 "basis_parameter", "basis_value")

    def __init__(self, unit_entry, coefficient_value=None, basis_value=None):
        self.label = str(unit_entry.get("Units") or "").strip()
        self.unit_type = unit_entry.get("Type")
        self.coefficient = to_float(unit_entry.get("Coefficient"), 1.0) or 1.0
        self.coefficient_parameter = unit_entry.get("CoefficientParameter")
        self.coefficient_value = coefficient_value
        self.basis_parameter = unit_entry.get("BasisParameter")
        self.basis_value = basis_value

    def to_base(self, value):
        """Переводит значение из этой системы единиц во вторичные (базовые)."""
        if self.unit_type == UNIT_TYPE_PRIMARY:
            return value / self.coefficient_value if self.coefficient_value else value
        if self.unit_type == UNIT_TYPE_RELATIVE:
            return value * self.basis_value if self.basis_value else value
        if self.unit_type == UNIT_TYPE_MULTIPLIER:
            return value / self.coefficient if self.coefficient else value
        # Secondary — уже базовые единицы
        return value

    def from_base(self, value):
        """Переводит значение из вторичных единиц в эту систему единиц."""
        if self.unit_type == UNIT_TYPE_PRIMARY:
            result = value * self.coefficient_value if self.coefficient_value else value
            return result * self.coefficient
        if self.unit_type == UNIT_TYPE_RELATIVE:
            return value / self.basis_value if self.basis_value else value
        return value * self.coefficient


class UnitConverter:
    """Пересчёт значений одного пакета поддержки в выбранную систему единиц."""

    def __init__(self, config_handler, extension_handler,
                 target_type=DEFAULT_UNIT_TYPE):
        self.config_handler = config_handler
        self.extension_handler = extension_handler
        self.target_type = target_type or DEFAULT_UNIT_TYPE
        self._cache = {}
        self._warned = set()

    # ------------------------------------------------------------ служебное

    def set_target_type(self, target_type):
        if target_type == self.target_type:
            return
        self.target_type = target_type or DEFAULT_UNIT_TYPE
        self._cache.clear()

    def _parameter_number(self, parameter_name):
        if not parameter_name:
            return None
        info = self.config_handler.get_param_info(parameter_name)
        if not info:
            return None
        return to_float(info.get("defaultValue"))

    def _make_scale(self, unit_entry):
        coefficient_value = self._parameter_number(unit_entry.get("CoefficientParameter"))
        basis_value = self._parameter_number(unit_entry.get("BasisParameter"))
        return UnitScale(unit_entry, coefficient_value, basis_value)

    def _resolve(self, parameter_name):
        """Возвращает (исходная шкала, целевая шкала, подпись единиц).

        Если для параметра нет трансформации или в ней нет выбранной системы
        единиц (например, для времени), целевая шкала равна None — значения
        не пересчитываются, подпись остаётся как в meta.json.
        """
        cached = self._cache.get(parameter_name)
        if cached is not None:
            return cached

        info = self.config_handler.get_param_info(parameter_name) or {}
        declared = str(info.get("units") or "").strip()

        transformation = self.extension_handler.find_transformation_by_parameter_name(parameter_name)
        if not transformation:
            result = (None, None, declared)
            self._cache[parameter_name] = result
            return result

        scales = [self._make_scale(unit) for unit in transformation.get("AvailableUnits") or []]
        source = next((scale for scale in scales if scale.label == declared), None)
        target = next((scale for scale in scales if scale.unit_type == self.target_type), None)

        if source is None:
            # Подпись в meta.json не совпала ни с одной системой единиц —
            # не рискуем пересчитывать.
            if declared not in self._warned:
                self._warned.add(declared)
                Logger.warning(f"Не найдена система единиц {declared!r} в "
                               f"трансформации {transformation.get('Transformation')}")
            result = (None, None, declared)
        elif target is None:
            # В этой трансформации нет выбранного типа единиц (время и т.п.)
            result = (source, None, declared or source.label)
        else:
            result = (source, target, target.label)

        self._cache[parameter_name] = result
        return result

    # ------------------------------------------------------------ публичное

    def unit_label(self, parameter_name):
        """Подпись единиц для выбранной системы (или исходная подпись)."""
        _source, _target, label = self._resolve(parameter_name)
        return label

    def scale_factor(self, parameter_name):
        """Множитель пересчёта или None, если пересчёт не требуется.

        None возвращается, когда трансформации нет, целевой системы единиц нет
        или множитель равен единице (тогда форматирование остаётся прежним).
        """
        source, target, _label = self._resolve(parameter_name)
        if source is None or target is None:
            return None

        factor = target.from_base(source.to_base(1.0))
        if factor is None:
            return None
        if abs(factor - 1.0) < 1e-12:
            return None
        return factor

    def convert(self, parameter_name, value):
        """Пересчитывает числовое значение в выбранную систему единиц."""
        number = to_float(value)
        if number is None:
            return value

        source, target, _label = self._resolve(parameter_name)
        if source is None or target is None:
            return number

        return target.from_base(source.to_base(number))

    def describe(self, parameter_name):
        """(подпись единиц, множитель или None) — для диагностики и тестов."""
        return self.unit_label(parameter_name), self.scale_factor(parameter_name)
