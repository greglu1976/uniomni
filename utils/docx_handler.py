"""Работа с документом Word: секции и стили."""

from docx.enum.section import WD_ORIENTATION, WD_SECTION
from docx.shared import Inches, Mm


def add_new_section(doc):
    """Добавляет портретную секцию."""
    # Разрыв страницы перед созданием новой секции
    doc.add_paragraph()

    new_section = doc.add_section(WD_SECTION.NEW_PAGE)

    new_section.orientation = WD_ORIENTATION.PORTRAIT
    new_section.page_width = Inches(8.3)
    new_section.page_height = Inches(11.7)

    # Поля (мм)
    new_section.left_margin = Mm(25)
    new_section.right_margin = Mm(10)
    new_section.top_margin = Mm(10)
    new_section.bottom_margin = Mm(10)
    new_section.gutter = Mm(0)  # переплёт
    new_section.header_distance = Mm(4)

    return doc


def add_new_section_landscape(doc):
    """Добавляет альбомную секцию."""
    # Разрыв страницы перед созданием новой секции
    doc.add_paragraph()

    new_section = doc.add_section(WD_SECTION.NEW_PAGE)

    new_section.orientation = WD_ORIENTATION.LANDSCAPE
    new_section.page_width = Inches(11.7)
    new_section.page_height = Inches(8.2)

    # Поля (мм)
    new_section.left_margin = Mm(10)
    new_section.right_margin = Mm(10)
    new_section.top_margin = Mm(25)
    new_section.bottom_margin = Mm(10)
    new_section.header_distance = Mm(15)

    return doc


def get_style_id(document, style_name):
    """Возвращает style_id стиля с кэшированием на документе.

    `paragraph.style = "Имя"` в python-docx каждый раз ищет стиль по имени
    среди всех стилей документа (и ещё раз — стиль по умолчанию). На тысячах
    ячеек таблиц это давало десятки секунд генерации.
    """
    cache = document.__dict__.setdefault('_style_id_cache', {})
    if style_name not in cache:
        cache[style_name] = document.styles[style_name].style_id
    return cache[style_name]


def set_paragraph_style(document, paragraph, style_name):
    """Назначает стиль параграфу, минуя повторный поиск стиля по имени."""
    paragraph._p.get_or_add_pPr().style = get_style_id(document, style_name)
    return paragraph


def add_paragraph(document, text='', style_name=None):
    """Добавляет параграф и, при необходимости, назначает ему стиль."""
    paragraph = document.add_paragraph(text)
    if style_name:
        set_paragraph_style(document, paragraph, style_name)
    return paragraph


def set_table_style(document, table, style_name):
    """Назначает стиль таблице, минуя повторный поиск стиля по имени."""
    table._tbl.tblPr.style = get_style_id(document, style_name)
    return table
