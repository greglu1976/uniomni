"""Экспорт раздела «Уставки» бланка в LaTeX.

Формируется самостоятельный .tex-файл: заголовок, перечень таблиц уставок
по функциональным блокам и подписи столбцов — те же данные, что и в docx
(с учётом выбранной системы единиц).
"""

from core.UnitConverter import DEFAULT_UNIT_TYPE, UNIT_TYPE_TITLES
from utils.latex import escape_latex, escape_name, format_numeric, parse_note_to_latex

SECTION_TITLE = 'УСТАВКИ РЗиА'

# Спецификация столбцов longtable: наименование, диапазон, ед. изм., шаг, умолчание
COLUMN_SPEC = (
    r'|>{\centering\arraybackslash}p{5.2cm}'
    r'|>{\centering\arraybackslash}p{3.2cm}'
    r'|>{\centering\arraybackslash}p{1.8cm}'
    r'|>{\centering\arraybackslash}p{1.5cm}'
    r'|>{\centering\arraybackslash}p{2.4cm}|'
)

HEADER_ROW = (
    r'\textbf{Наименование} & \textbf{Значение / Диапазон} & '
    r'\textbf{Ед. изм.} & \textbf{Шаг} & '
    r'\textbf{Значение по умолчанию} \\ \hline'
)

PREAMBLE = r"""% Раздел «Уставки» бланка настроек. Файл самостоятельный, но при
% необходимости можно включить его в проект РЭ через \input{}, взяв часть
% между маркерами «начало/конец раздела».
\documentclass[10pt,a4paper,landscape]{article}
\usepackage{iftex}
\ifPDFTeX
  \usepackage[T2A]{fontenc}
  \usepackage[utf8]{inputenc}
  \usepackage[russian]{babel}
\else
  \usepackage{fontspec}
  \usepackage[russian]{babel}
\fi
\usepackage{array}
\usepackage{longtable}
\usepackage[margin=12mm]{geometry}
\setlength{\parindent}{0pt}
\begin{document}
"""

POSTAMBLE = "\\end{document}\n"


def _row_latex(row):
    """Строка таблицы уставок в LaTeX."""
    name = row.get('display_name') or row.get('col1') or ''
    cells = [
        r'\centering ' + escape_name(name),
        r'\centering ' + parse_note_to_latex(row.get('col3')),
        r'\centering ' + format_numeric(row.get('col4'), escape_percent=True),
        r'\centering ' + format_numeric(row.get('col5')),
        r'\centering \arraybackslash ' + format_numeric(row.get('col6')),
    ]
    return ' & '.join(cells) + ' \\\\\n'


def _table_latex(rows):
    """Таблица longtable с повторяющейся шапкой."""
    lines = [f'\\begin{{longtable}}{{{COLUMN_SPEC}}}', '\\hline', HEADER_ROW,
             '\\endfirsthead', '\\hline', HEADER_ROW, '\\endhead']
    lines.extend(_row_latex(row) for row in rows)
    lines.append('\\end{longtable}')
    return lines


SECTION_START_MARKER = "% ======================= начало раздела «Уставки» ======================="
SECTION_END_MARKER = "% ======================= конец раздела «Уставки» ========================"


def build_settings_section(setting_blanc):
    """Строки LaTeX для всех таблиц уставок (без преамбулы документа)."""
    lines = [
        SECTION_START_MARKER,
        f'\\begin{{center}}{{\\Large\\bfseries {SECTION_TITLE}}}\\end{{center}}',
        '',
    ]

    for fb_key in setting_blanc.maps:
        table = setting_blanc.get_table_settings_latex(fb_key)
        if not table:
            continue

        func_name = table.get('func_name', fb_key)
        short_name = func_name.split('_')[0]
        title = setting_blanc.abbr_dict.get(short_name, short_name)
        lines.append(f'\\subsection*{{{escape_latex(title)}}}')

        if table.get('type') == 'simple':
            lines.extend(_table_latex(table.get('rows', [])))
        else:
            for sub_func in table.get('sub_functions', []):
                subtitle = sub_func.get('subtitle', '')
                if subtitle:
                    lines.append(f'\\subsubsection*{{{escape_latex(subtitle)}}}')
                lines.extend(_table_latex(sub_func.get('rows', [])))

        lines.append('')

    lines.append(SECTION_END_MARKER)
    return lines


def build_settings_document(setting_blanc, unit_type=DEFAULT_UNIT_TYPE):
    """Полный текст .tex-документа с разделом «Уставки»."""
    device = setting_blanc.device_data
    units_title = UNIT_TYPE_TITLES.get(unit_type, unit_type)

    info_line = (
        f"Устройство: {escape_latex(device.get('name', ''))} \\quad "
        f"Код заказа: {escape_latex(setting_blanc.code)} \\quad "
        f"Единицы уставок: {escape_latex(units_title)}"
    )

    lines = [PREAMBLE, f'\\noindent {info_line}\\par\\medskip', '']
    lines.extend(build_settings_section(setting_blanc))
    lines.append(POSTAMBLE)
    return '\n'.join(lines)
