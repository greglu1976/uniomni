"""Выпадающие списки (content controls) для шаблонов Word.

Все три публичные функции — add_formatted_dropdown2, add_formatted_dropdown2_10pt
и add_formatted_dropdown3 — собираются одним внутренним построителем.

Важно: каждому content control присваивается уникальный w:id и непустые
w:alias/w:tag. Раньше id вычислялся как hash(alias), а alias всегда был
пустой строкой (hash("") == 0), из-за чего в документе оказывались тысячи
контролов с w:id="0".
"""

import copy
import itertools

from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Pt

from logger.logger import Logger

# Сквозной счётчик уникальных идентификаторов content control
_CONTROL_IDS = itertools.count(1)

# Кэш разобранных XML-шаблонов: списки вариантов повторяются в каждой ячейке
# (сотни контролов с одним и тем же набором из сотен сигналов).
_TEMPLATE_CACHE = {}
_TEMPLATE_CACHE_LIMIT = 32

# Разделители в общем списке сигналов
_INPUTS_HEADER_VALUE = "INPUTS_HEADER"
_CONTROLS_HEADER_VALUE = "CONTROLS_HEADER"
_SPACER_VALUE = "SPACER"


def _xml_attr(value):
    """Готовит строку для подстановки в XML-атрибут."""
    text = "" if value is None else str(value)
    # Убираем символы, недопустимые в XML 1.0 — иначе parse_xml падает
    text = "".join(ch for ch in text if ch in "\t\n\r" or ord(ch) >= 0x20)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _list_items_xml(choices):
    """XML-элементы списка для последовательности вариантов."""
    result = []
    for choice in choices or []:
        value = _xml_attr(choice)
        if not value:
            continue
        result.append(f'<w:listItem w:displayText="{value}" w:value="{value}"/>')
    return "".join(result)


_LRU_ITEMS = {}


def _cached_items_xml(choices):
    """Кэшированный XML списка вариантов (строки хэшируются один раз)."""
    key = tuple(choices or ())
    cached = _LRU_ITEMS.get(key)
    if cached is not None:
        return cached
    if len(_LRU_ITEMS) >= _TEMPLATE_CACHE_LIMIT:
        _LRU_ITEMS.clear()
    cached = _list_items_xml(key)
    _LRU_ITEMS[key] = cached
    return cached


def _disabled_item(display_text, value):
    return (
        f'<w:listItem w:displayText="{_xml_attr(display_text)}" '
        f'w:value="{value}" w:disabled="true"/>'
    )


def _build_xml(items_xml, default, alias, instruction_text, font_half_points,
               pin_font_size=False):
    """Собирает XML content control с выпадающим списком.

    pin_font_size=True добавляет <w:rPr> внутрь <w:sdtPr>: этот кегль Word
    применяет к тексту, который подставляется при выборе пункта. Без него в
    плотных таблицах выбранное значение показывается кеглем таблицы, а не
    списка (для 10-пт списков это заметно).
    """
    pin_properties = ''
    if pin_font_size:
        pin_properties = (
            '<w:rPr>'
            f'<w:sz w:val="{font_half_points}"/>'
            f'<w:szCs w:val="{font_half_points}"/>'
            '</w:rPr>'
        )

    return f'''
        <w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:sdtPr>
                <w:alias w:val="{_xml_attr(alias)}"/>
                <w:tag w:val="{_xml_attr(alias)}"/>
                <w:id w:val="0"/>
                <w:dropDownList>
                    <w:listItem w:displayText="{_xml_attr(default)}" w:value="{_xml_attr(default)}"/>
                    {items_xml}
                </w:dropDownList>
                <w:showingPlcHdr/>
                {pin_properties}
                <w:placeholder>
                    <w:docPart w:val="{_xml_attr(instruction_text)}"/>
                </w:placeholder>
            </w:sdtPr>
            <w:sdtContent>
                <w:r>
                    <w:rPr>
                        <w:color w:val="A0A0A0"/>
                        <w:sz w:val="{font_half_points}"/>
                        <w:szCs w:val="{font_half_points}"/>
                        <w:spacing w:val="10"/>
                    </w:rPr>
                    <w:t>{_xml_attr(default)}</w:t>
                </w:r>
            </w:sdtContent>
        </w:sdt>
    '''


def _get_template(key, xml):
    template = _TEMPLATE_CACHE.get(key)
    if template is None:
        template = parse_xml(xml)
        if len(_TEMPLATE_CACHE) >= _TEMPLATE_CACHE_LIMIT:
            _TEMPLATE_CACHE.clear()
        _TEMPLATE_CACHE[key] = template
    return template


def _insert_dropdown(paragraph, items_xml, default, alias, instruction_text,
                     font_half_points=24, cache_key=None, pin_font_size=False):
    """Вставляет content control в параграф.

    Returns:
        bool: True, если список вставлен, False — если пришлось откатиться
        на обычный текст (описано в логе).
    """
    key = cache_key or (id(items_xml), default, alias, instruction_text,
                        font_half_points, pin_font_size)

    try:
        template = _get_template(
            key,
            _build_xml(items_xml, default, alias, instruction_text,
                       font_half_points, pin_font_size),
        )
        sdt = copy.deepcopy(template)
    except Exception as error:  # некорректный XML — не роняем генерацию документа
        Logger.error(f"Не удалось создать выпадающий список: {error}")
        return False

    control_id = next(_CONTROL_IDS)
    sdt_properties = sdt.find(qn("w:sdtPr"))
    sdt_properties.find(qn("w:id")).set(qn("w:val"), str(control_id))

    # Пустые alias/tag делали все контролы неотличимыми друг от друга
    # для любого инструмента, который ищет их по тегу.
    if not alias:
        unique_alias = f"Dropdown{control_id}"
        sdt_properties.find(qn("w:alias")).set(qn("w:val"), unique_alias)
        sdt_properties.find(qn("w:tag")).set(qn("w:val"), unique_alias)

    paragraph._p.append(sdt)
    return True


def _append_text_fallback(paragraph, default, font_half_points=24):
    """Резервный вариант: обычный текст вместо выпадающего списка."""
    run = paragraph.add_run(f"[{default}]")
    run.font.size = Pt(font_half_points / 2)


def add_formatted_dropdown2(paragraph, choices, default="Не назначено", alias="",
                            instruction_text=""):
    """Выпадающий список (12 пт) с одним набором вариантов."""
    items_xml = _cached_items_xml(choices)
    inserted = _insert_dropdown(
        paragraph=paragraph,
        items_xml=items_xml,
        default=default,
        alias=alias,
        instruction_text=instruction_text,
        font_half_points=24,
        cache_key=(tuple(choices or ()), default, alias, instruction_text, 24),
    )
    if not inserted:
        _append_text_fallback(paragraph, default)


def add_formatted_dropdown2_10pt(paragraph, choices, default="Не назначено", alias="",
                                 instruction_text=""):
    """Выпадающий список шрифтом 10 пт (для плотных таблиц)."""
    items_xml = _cached_items_xml(choices)
    inserted = _insert_dropdown(
        paragraph=paragraph,
        items_xml=items_xml,
        default=default,
        alias=alias,
        instruction_text=instruction_text,
        font_half_points=20,
        cache_key=(tuple(choices or ()), default, alias, instruction_text, 20, True),
        # Кегль фиксируем в sdtPr, иначе выбранное значение выводится кеглем таблицы
        pin_font_size=True,
    )
    if not inserted:
        _append_text_fallback(paragraph, default, font_half_points=20)


def add_formatted_dropdown3(paragraph, inputs_choices, controls_choices=(),
                            default="Не назначено", alias="", instruction_text="",
                            first_divider="Сигналы РЗиА",
                            second_divider="Общие сигналы ФС"):
    """Выпадающий список из двух групп сигналов с заголовками-разделителями."""
    inputs_choices = tuple(inputs_choices or ())
    controls_choices = tuple(controls_choices or ())

    parts = []
    if inputs_choices:
        parts.append(_disabled_item(
            f"──────── {first_divider} ────────", _INPUTS_HEADER_VALUE))
        parts.append(_cached_items_xml(inputs_choices))

    if controls_choices:
        if inputs_choices:
            parts.append(_disabled_item(" ", _SPACER_VALUE))
        parts.append(_disabled_item(
            f"────── {second_divider} ──────", _CONTROLS_HEADER_VALUE))
        parts.append(_cached_items_xml(controls_choices))

    inserted = _insert_dropdown(
        paragraph=paragraph,
        items_xml="".join(parts),
        default=default,
        alias=alias,
        instruction_text=instruction_text,
        font_half_points=24,
        cache_key=(inputs_choices, controls_choices, default, alias,
                   instruction_text, first_divider, second_divider),
    )
    if not inserted:
        _append_text_fallback(paragraph, default)
