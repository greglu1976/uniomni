"""Общие помощники формирования LaTeX (экранирование и форматирование ячеек)."""

import ast

from logger.logger import Logger

# LaTeX-символы, которые обязательно экранируются в текстовых ячейках
_LATEX_SPECIALS = (
    ('\\', r'\textbackslash{}'),
    ('&', r'\&'),
    ('%', r'\%'),
    ('#', r'\#'),
    ('_', r'\_'),
)


def escape_latex(text):
    """Экранирует специальные символы LaTeX в текстовой ячейке."""
    text = "" if text is None else str(text)
    for char, replacement in _LATEX_SPECIALS:
        text = text.replace(char, replacement)
    return text


def escape_name(text):
    """Экранирование наименования уставки (дефисы не трогаем)."""
    text = escape_latex(text)
    return text.replace('>>', r'\verb|>>|').replace('<<', r'\verb|<<|')


def format_numeric(value, escape_percent=False):
    """Форматирует числовую ячейку LaTeX (дефис → тире)."""
    text = "" if value is None else str(value)
    text = text.replace('-', r'--')
    if escape_percent:
        text = text.replace('%', r'\%')
    return text


def format_mark(value):
    """Форматирует ячейку-признак (+ / - / *)."""
    text = "" if value is None else str(value)
    return text.replace('-', r'--').replace('*', r'$\ast$')


def note_sort_key(item):
    """Ключ сортировки значений «note» (числовые ключи раньше текстовых)."""
    key = item[0]
    return (0, int(key)) if str(key).isdigit() else (1, str(key))


def parse_note_to_latex(note_str):
    """'note_{"0": "a", "1": "b"}' → 'a \\\\ b', иначе строка как есть."""
    if not isinstance(note_str, str) or not note_str.startswith("note_"):
        return "" if note_str is None else str(note_str)

    try:
        note_dict = ast.literal_eval(note_str[5:])
        if not isinstance(note_dict, dict):
            return str(note_dict)
        values = [str(value) for _, value in sorted(note_dict.items(), key=note_sort_key)]
    except (ValueError, SyntaxError, TypeError) as error:
        Logger.warning(f"Не удалось разобрать значения уставки: {error}")
        return note_str

    return " \\\\ ".join(values)
