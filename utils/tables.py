"""Построение таблиц бланка уставок в документе Word.

Оставлены только функции, которые действительно используются приложением
(варианты *_core4 для актуального пакета поддержки и финальная таблица
с подписями). Легаси-функции для старых шаблонов М300 удалены.

Производительность (важно для документов в сотни таблиц):

* `row.cells` в python-docx каждый раз строит сетку всей таблицы —
  используется `row_cells()`, работающий напрямую с `tr.tc_lst`;
* текст, выравнивание и размер шрифта ставятся напрямую в XML: штатные
  сеттеры python-docx (`cell.text`, `paragraph.alignment`, `run.font.size`)
  на каждой ячейке перебирают списки дочерних элементов и дают в сумме
  десятки секунд на документ.
"""

from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.table import _Cell

from .docx_handler import set_paragraph_style, set_table_style
from .dropdowns import (
    add_formatted_dropdown2,
    add_formatted_dropdown2_10pt,
    add_formatted_dropdown3,
)

# Стили, которые обязаны присутствовать в шаблоне origin.docx
STYLE_TABLE_HEADER = 'ДОК Таблица Заголовок'
STYLE_TABLE_GRID = 'Сетка таблицы51'
STYLE_TABLE_PLAIN = 'Стиль6'

ALIGN_CENTER = 'center'
ALIGN_LEFT = 'left'

_FIXED_LAYOUT = (
    r'<w:tblLayout xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:type="fixed"/>'
)

_XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

# Порядок дочерних элементов w:pPr: w:jc ставится перед этими элементами
_JC_SUCCESSORS = frozenset(qn(tag) for tag in (
    'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap',
    'w:outlineLvl', 'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange',
))

# Порядок дочерних элементов w:rPr: w:sz ставится перед этими элементами
_SZ_SUCCESSORS = frozenset(qn(tag) for tag in (
    'w:szCs', 'w:highlight', 'w:u', 'w:effect', 'w:bdr', 'w:shd', 'w:fitText',
    'w:vertAlign', 'w:rtl', 'w:cs', 'w:em', 'w:lang', 'w:eastAsianLayout',
    'w:specVanish', 'w:oMath',
))


def row_cells(row, table):
    """Ячейки строки без пересборки сетки таблицы.

    `row.cells` строит сетку всей таблицы при каждом обращении, из-за чего
    заполнение таблицы «по строкам» становится квадратичным. Здесь берутся
    непосредственно элементы `<w:tc>` строки.

    Внимание: для строк с горизонтальными объединениями число ячеек меньше
    числа колонок сетки — такие строки нужно обрабатывать до объединения.
    """
    return [_Cell(tc, table) for tc in row._tr.tc_lst]


# --------------------------------------------------------------- ячейки

def _make_text_run(text):
    """Создаёт элемент `w:r` с текстом (как это делает python-docx)."""
    run = OxmlElement('w:r')
    text_element = OxmlElement('w:t')
    text_element.text = text
    if len(text.strip()) < len(text):
        text_element.set(_XML_SPACE, 'preserve')
    run.append(text_element)
    return run


def _clear_runs(paragraph):
    paragraph_element = paragraph._p
    for run in paragraph_element.findall(qn('w:r')):
        paragraph_element.remove(run)
    return paragraph_element


def set_cell_text(cell, value):
    """Быстрая установка текста ячейки.

    Штатный `cell.text = ...` на каждую ячейку делает clear_content() через
    xpath — на документе это складывается в секунды.
    """
    text = "" if value is None else str(value)
    paragraph_element = _clear_runs(cell.paragraphs[0])
    if text:
        paragraph_element.append(_make_text_run(text))


def set_cell_multiline_text(cell, value):
    """Текст с переносами строк («\\\\n» и настоящий перевод строки)."""
    text = "" if value is None else str(value)
    text = text.replace('\\n', '\n')
    paragraph_element = _clear_runs(cell.paragraphs[0])

    for i, part in enumerate(text.split('\n')):
        if i > 0:
            run = OxmlElement('w:r')
            run.append(OxmlElement('w:br'))
            paragraph_element.append(run)
        if part:
            paragraph_element.append(_make_text_run(part))


def set_paragraph_alignment(paragraph, value=ALIGN_CENTER):
    """Выравнивание параграфа без дорогого поиска места вставки w:jc."""
    p_pr = paragraph._p.get_or_add_pPr()
    jc = p_pr.find(qn('w:jc'))
    if jc is None:
        jc = OxmlElement('w:jc')
        for child in p_pr:
            if child.tag in _JC_SUCCESSORS:
                child.addprevious(jc)
                break
        else:
            p_pr.append(jc)
    jc.set(qn('w:val'), value)


def set_runs_font_size(table, size_pt):
    """Единый размер шрифта для текста всех ячеек таблицы."""
    half_points = str(int(round(size_pt * 2)))
    sz_tag = qn('w:sz')
    rpr_tag = qn('w:rPr')
    paragraph_tag = qn('w:p')
    run_tag = qn('w:r')

    for row in table.rows:
        # Объединённые (vMerge=continue) ячейки пропускаем: они рисуются
        # элементом выше, а размер шрифта задаётся в нём же.
        for tc in row._tr.tc_lst:
            if tc.get(qn('w:vMerge')) == 'continue':
                continue
            for paragraph in tc.iter(paragraph_tag):
                for run in paragraph.findall(run_tag):
                    r_pr = run.find(rpr_tag)
                    if r_pr is None:
                        r_pr = OxmlElement('w:rPr')
                        run.insert(0, r_pr)
                    sz = r_pr.find(sz_tag)
                    if sz is None:
                        sz = OxmlElement('w:sz')
                        for child in r_pr:
                            if child.tag in _SZ_SUCCESSORS:
                                child.addprevious(sz)
                                break
                        else:
                            r_pr.append(sz)
                    sz.set(qn('w:val'), half_points)


# -------------------------------------------------------------- элементы

def _set_fixed_layout(table):
    """Фиксирует ширину столбцов в XML таблицы."""
    tbl_pr = table._tbl.tblPr
    if tbl_pr is None:
        return
    for element in tbl_pr.xpath('./w:tblLayout'):
        tbl_pr.remove(element)
    tbl_pr.append(parse_xml(_FIXED_LAYOUT))


def _set_column_widths(table, widths):
    """Задаёт ширину столбцов, не строя сетку таблицы.

    Ширина проставляется и в `w:tblGrid` (по ней Word считает фиксированную
    раскладку), и в ячейках. Для объединённых ячеек берётся ширина первой
    занимаемой колонки — остальное определяется gridSpan и сеткой.
    """
    for grid_col, width in zip(table._tbl.tblGrid.gridCol_lst, widths):
        grid_col.w = width

    for row in table.rows:
        column = 0
        for tc in row._tr.tc_lst:
            if column >= len(widths):
                break
            _Cell(tc, table).width = widths[column]
            column += tc.grid_span


def set_table_borders(table):
    """Рисует одинарные границы по всем сторонам таблицы."""
    tbl_borders = OxmlElement('w:tblBorders')
    for border_name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '8')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'auto')
        tbl_borders.append(border)

    tbl_pr = table._tbl.tblPr
    if tbl_pr is None:
        tbl_pr = OxmlElement('w:tblPr')
        table._tbl.insert(0, tbl_pr)
    tbl_pr.append(tbl_borders)


def set_repeat_table_header(row):
    """Повторять строку как заголовок таблицы на каждой странице."""
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement('w:tblHeader')
    tbl_header.set(qn('w:val'), "true")
    tr_pr.append(tbl_header)
    return row


def set_cell_vertical_alignment(cell: _Cell, align="center"):
    """Вертикальное выравнивание содержимого ячейки."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_valign = OxmlElement('w:vAlign')
    tc_valign.set(qn('w:val'), align)
    tc_pr.append(tc_valign)


def _format_header_cell(doc, cell, text=None):
    """Оформление ячейки заголовка таблицы."""
    if text is not None:
        set_cell_text(cell, text)
    paragraph = cell.paragraphs[0]
    set_paragraph_style(doc, paragraph, STYLE_TABLE_HEADER)
    set_cell_vertical_alignment(cell, align="center")
    set_paragraph_alignment(paragraph, ALIGN_CENTER)


####################################################################################
################################ УСТАВКИ ###########################################
####################################################################################

TABLE_WIDTHS_SETTINGS = (
    Inches(0.25), Inches(1.7), Inches(1.8), Inches(0.6), Inches(0.8),
    Inches(1.4), Inches(1), Inches(1), Inches(1), Inches(1),
)


def add_table_settings_core4(doc):
    """Пустая таблица уставок (10 столбцов, две строки заголовка)."""
    table = doc.add_table(rows=2, cols=10)
    set_table_style(doc, table, STYLE_TABLE_GRID)
    table.allow_autofit = False
    _set_fixed_layout(table)

    header_texts = [
        '№', 'Наименование', 'Значение / Диапазон', 'Ед. изм.', 'Шаг',
        'Значение по умолчанию', 'Группы уставок',
    ]
    header_cells = row_cells(table.rows[0], table)
    for cell, text in zip(header_cells, header_texts):
        _format_header_cell(doc, cell, text)

    set_repeat_table_header(table.rows[0])

    second_row = row_cells(table.rows[1], table)
    for idx, number in zip((6, 7, 8, 9), ('1', '2', '3', '4')):
        set_cell_text(second_row[idx], number)
        set_paragraph_alignment(second_row[idx].paragraphs[0], ALIGN_CENTER)

    for col_idx in range(6):
        table.cell(0, col_idx).merge(table.cell(1, col_idx))
    table.cell(0, 6).merge(table.cell(0, 9))

    _set_column_widths(table, TABLE_WIDTHS_SETTINGS)
    set_runs_font_size(table, 10)
    return table


####################################################################################
############################ МАТРИЦА ДИСКРЕТНЫХ ВХОДОВ #############################
####################################################################################

TABLE_WIDTHS_MTRX_INS = (Inches(2), Inches(4))


def add_table_mtrx_ins_core4(doc, slot_name, inputs_list, sigs, di_sigs):
    """Матрица дискретных входов слота: вход → назначенный сигнал (dropdown)."""
    if not inputs_list:
        return None

    table = doc.add_table(rows=len(inputs_list) + 1, cols=2)
    set_table_style(doc, table, STYLE_TABLE_PLAIN)
    table.allow_autofit = False
    _set_fixed_layout(table)

    header_cells = row_cells(table.rows[0], table)
    _format_header_cell(doc, header_cells[0], 'Дискретный вход')
    _format_header_cell(doc, header_cells[1], 'Назначенный сигнал')
    set_repeat_table_header(table.rows[0])

    for idx, input_desc in enumerate(inputs_list):
        cells = row_cells(table.rows[idx + 1], table)

        set_cell_text(cells[0], input_desc)
        set_paragraph_alignment(cells[0].paragraphs[0], ALIGN_LEFT)

        right_paragraph = cells[1].paragraphs[0]
        add_formatted_dropdown3(
            paragraph=right_paragraph,
            inputs_choices=sigs,
            controls_choices=di_sigs,
        )
        set_paragraph_alignment(right_paragraph, ALIGN_CENTER)

    _set_column_widths(table, TABLE_WIDTHS_MTRX_INS)
    return table


####################################################################################
############################ МАТРИЦА ВЫХОДНЫХ РЕЛЕ #################################
####################################################################################

TABLE_WIDTHS_MTRX_OUTS = (
    Inches(2), Inches(1.7), Inches(1.7), Inches(1.7), Inches(1.7), Inches(1.7),
)


def add_table_mtrx_outs_core4(doc, outputs_list, sigs_list):
    """Матрица выходных реле слота (5 сигналов на реле)."""
    if not outputs_list:
        return None

    table = doc.add_table(rows=len(outputs_list) + 2, cols=6)
    set_table_style(doc, table, STYLE_TABLE_PLAIN)
    table.allow_autofit = False
    _set_fixed_layout(table)

    header_cells = row_cells(table.rows[0], table)
    _format_header_cell(doc, header_cells[0], 'Выходное реле')
    _format_header_cell(doc, header_cells[1], 'Назначенные сигналы')
    for cell in header_cells[2:]:
        _format_header_cell(doc, cell)

    second_row = row_cells(table.rows[1], table)
    for i in range(1, 6):
        _format_header_cell(doc, second_row[i], str(i))

    table.cell(0, 0).merge(table.cell(1, 0))
    table.cell(0, 1).merge(table.cell(0, 5))

    for idx, output_name in enumerate(outputs_list):
        cells = row_cells(table.rows[idx + 2], table)

        set_cell_text(cells[0], output_name)
        set_paragraph_alignment(cells[0].paragraphs[0], ALIGN_LEFT)

        for col_idx in range(1, 6):
            paragraph = cells[col_idx].paragraphs[0]
            add_formatted_dropdown2(paragraph=paragraph, choices=sigs_list)
            set_paragraph_alignment(paragraph, ALIGN_CENTER)

    set_repeat_table_header(table.rows[0])
    set_repeat_table_header(table.rows[1])

    _set_column_widths(table, TABLE_WIDTHS_MTRX_OUTS)
    return table


####################################################################################
############################ СВЕТОДИОДЫ ############################################
####################################################################################

TABLE_WIDTHS_LEDS = (
    Inches(1.2), Inches(1.2), Inches(1.0), Inches(1.5),
    Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5),
)


def add_table_leds_new_core4(doc, statuses, led_count=16):
    """Таблица настройки светодиодов (режим, цвет, до 5 сигналов)."""
    table = doc.add_table(rows=1 + led_count, cols=8)
    set_table_style(doc, table, STYLE_TABLE_PLAIN)
    table.allow_autofit = False
    _set_fixed_layout(table)

    headers = [
        'Светодиод', 'Режим работы', 'Цвет',
        'Назначенный сигнал 1', 'Назначенный сигнал 2', 'Назначенный сигнал 3',
        'Назначенный сигнал 4', 'Назначенный сигнал 5',
    ]
    header_cells = row_cells(table.rows[0], table)
    for cell, text in zip(header_cells, headers):
        _format_header_cell(doc, cell, text)
    set_repeat_table_header(table.rows[0])

    for row_idx in range(1, 1 + led_count):
        cells = row_cells(table.rows[row_idx], table)

        set_cell_text(cells[0], f'Светодиод {row_idx}')
        set_paragraph_alignment(cells[0].paragraphs[0], ALIGN_CENTER)

        mode_paragraph = cells[1].paragraphs[0]
        add_formatted_dropdown2(
            paragraph=mode_paragraph,
            choices=["С фиксацией"],
            default='Без фиксации',
        )
        set_paragraph_alignment(mode_paragraph, ALIGN_CENTER)

        color_paragraph = cells[2].paragraphs[0]
        add_formatted_dropdown2(
            paragraph=color_paragraph,
            choices=['Зеленый'],
            default='Красный',
        )
        set_paragraph_alignment(color_paragraph, ALIGN_CENTER)

        for col_idx in range(3, 8):
            signal_paragraph = cells[col_idx].paragraphs[0]
            add_formatted_dropdown2(paragraph=signal_paragraph, choices=statuses)
            set_paragraph_alignment(signal_paragraph, ALIGN_CENTER)

    _set_column_widths(table, TABLE_WIDTHS_LEDS)
    return table


####################################################################################
############################ ФУНКЦИОНАЛЬНЫЕ КЛАВИШИ ################################
####################################################################################

TABLE_WIDTHS_FKS = (Inches(2), Inches(4))


def add_table_fks_core4(doc, choices, key_count=16):
    """Таблица настройки функциональных клавиш."""
    table = doc.add_table(rows=1 + key_count, cols=2)
    set_table_style(doc, table, STYLE_TABLE_PLAIN)
    table.allow_autofit = False
    _set_fixed_layout(table)

    header_cells = row_cells(table.rows[0], table)
    _format_header_cell(doc, header_cells[0], 'Функциональная клавиша')
    _format_header_cell(doc, header_cells[1], 'Назначенный сигнал')
    set_repeat_table_header(table.rows[0])

    for row_idx in range(1, 1 + key_count):
        cells = row_cells(table.rows[row_idx], table)

        set_cell_text(cells[0], f'Функциональная клавиша {row_idx}')
        set_paragraph_alignment(cells[0].paragraphs[0], ALIGN_CENTER)

        signal_paragraph = cells[1].paragraphs[0]
        add_formatted_dropdown2(paragraph=signal_paragraph, choices=choices)
        set_paragraph_alignment(signal_paragraph, ALIGN_CENTER)

    _set_column_widths(table, TABLE_WIDTHS_FKS)
    return table


####################################################################################
################################ КОНФИГУРАЦИЯ ######################################
####################################################################################

TABLE_WIDTHS_BINARIES = (
    Inches(0.28), Inches(1.23), Inches(1.4), Inches(1.5),
    Inches(0.55), Inches(0.45), Inches(0.9), Inches(1.05),
)


def add_table_binaries_core4(doc, data_rows):
    """Таблица раздела «Конфигурация» (дискретные входы/выходы и т.п.)."""
    if not data_rows:
        return None

    table = doc.add_table(rows=1 + len(data_rows), cols=8)
    set_table_style(doc, table, STYLE_TABLE_GRID)
    table.allow_autofit = False
    set_table_borders(table)
    _set_fixed_layout(table)

    headers = ['№', 'Описание', 'Обозначение ФСУ', 'Значение / Диапазон',
               'Ед. изм.', 'Шаг', 'Значение по умолчанию', 'Уставка']
    header_cells = row_cells(table.rows[0], table)
    for cell, text in zip(header_cells, headers):
        _format_header_cell(doc, cell, text)
    set_repeat_table_header(table.rows[0])

    for row_idx, row_data in enumerate(data_rows):
        cells = row_cells(table.rows[row_idx + 1], table)

        set_cell_text(cells[0], row_idx + 1)
        set_paragraph_alignment(cells[0].paragraphs[0], ALIGN_CENTER)

        set_cell_multiline_text(cells[1], row_data[0])
        for col_idx in range(2, 7):
            set_cell_text(cells[col_idx], row_data[col_idx - 1])
        set_cell_text(cells[7], '')

        for col_idx in range(3, 8):
            set_paragraph_alignment(cells[col_idx].paragraphs[0], ALIGN_CENTER)

    _set_column_widths(table, TABLE_WIDTHS_BINARIES)
    set_runs_font_size(table, 11)
    return table


####################################################################################
################################ РЕГИСТРАЦИЯ #######################################
####################################################################################

TABLE_WIDTHS_REG = (Inches(4.0), Inches(2.0), Inches(1.6), Inches(1.6), Inches(1.6))


def add_table_reg_core4(doc, data_rows):
    """Таблица раздела «Настройка регистрации»."""
    if not data_rows:
        return None

    table = doc.add_table(rows=2 + len(data_rows), cols=5)
    set_table_style(doc, table, 'Стиль7')
    table.allow_autofit = False
    _set_fixed_layout(table)

    header_cells = row_cells(table.rows[0], table)
    _format_header_cell(doc, header_cells[0], 'Параметр')
    _format_header_cell(doc, header_cells[1])
    _format_header_cell(doc, header_cells[2], 'Журнал событий регистрация')
    _format_header_cell(doc, header_cells[3], 'Осциллограф пуск')
    _format_header_cell(doc, header_cells[4], 'Осциллограф регистрация')
    set_repeat_table_header(table.rows[0])

    second_row = row_cells(table.rows[1], table)
    set_cell_text(second_row[0], 'Наименование')
    set_cell_text(second_row[1], 'Обозначение ФСУ')
    set_paragraph_alignment(second_row[0].paragraphs[0], ALIGN_CENTER)
    set_paragraph_alignment(second_row[1].paragraphs[0], ALIGN_CENTER)

    table.cell(0, 0).merge(table.cell(0, 1))
    table.cell(0, 2).merge(table.cell(1, 2))
    table.cell(0, 3).merge(table.cell(1, 3))
    table.cell(0, 4).merge(table.cell(1, 4))

    choices_reg = ["Введено"]
    choices_osc = ["По переднему фронту", "По заднему фронту", "По любому изменению"]

    for row_idx, row_data in enumerate(data_rows):
        cells = row_cells(table.rows[row_idx + 2], table)
        col1, col2, param_type = row_data

        set_cell_text(cells[0], col1)
        set_paragraph_alignment(cells[0].paragraphs[0], ALIGN_LEFT)

        set_cell_text(cells[1], col2)
        set_paragraph_alignment(cells[1].paragraphs[0], ALIGN_LEFT)

        add_formatted_dropdown2_10pt(
            paragraph=cells[2].paragraphs[0],
            choices=choices_osc,
            default="Не выполняется",
        )
        set_paragraph_alignment(cells[2].paragraphs[0], ALIGN_CENTER)

        if str(param_type) == '3':
            add_formatted_dropdown2_10pt(
                paragraph=cells[3].paragraphs[0],
                choices=choices_osc,
                default="Не выполняется",
            )
            add_formatted_dropdown2_10pt(
                paragraph=cells[4].paragraphs[0],
                choices=choices_reg,
                default="Выведено",
            )
        else:
            set_cell_text(cells[3], 'Не выполняется')
            set_cell_text(cells[4], 'Выведено')

        set_paragraph_alignment(cells[3].paragraphs[0], ALIGN_CENTER)
        set_paragraph_alignment(cells[4].paragraphs[0], ALIGN_CENTER)

    _set_column_widths(table, TABLE_WIDTHS_REG)
    set_runs_font_size(table, 10)

    set_repeat_table_header(table.rows[0])
    set_repeat_table_header(table.rows[1])
    return table


####################################################################################
############################ ФИНАЛЬНАЯ ТАБЛИЦА С ПОДПИСЯМИ #########################
####################################################################################

TABLE_WIDTHS_FINAL = (Inches(3), Inches(3))


def add_table_final(doc):
    """Таблица с подписями составителя."""
    table = doc.add_table(rows=4, cols=2)
    set_table_style(doc, table, 'Стиль5')
    table.allow_autofit = False
    _set_fixed_layout(table)

    for row_idx, label in enumerate([
        'ФИО составителя:',
        'Номер и дата составления:',
        'Дата выдачи:',
        'Дата окончания:',
    ]):
        set_cell_text(row_cells(table.rows[row_idx], table)[0], label)

    for row in table.rows:
        for cell, width in zip(row_cells(row, table), TABLE_WIDTHS_FINAL):
            cell.width = width
        row.height = Pt(20)
        row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY

    set_runs_font_size(table, 11)
    return table
