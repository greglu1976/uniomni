# ГЕНЕРАЦИЯ И ЗАПОЛНЕНИЕ ШАБЛОНА СУММАРНОЙ ТАБЛИЦЫ СИГНАЛОВ

from docx import Document
from docxtpl import DocxTemplate

from tables import add_summ_table2
from docx_handler import add_new_section_landscape


def create_summ_table(fsu, isVirtKey=False,isVirtSwitch=False, isStatuses=False, isSysStatuses=False):

    doc = Document('origin_summ.docx')

    add_new_section_landscape(doc)

    p = doc.add_paragraph('Перечень сигналов ФСУ, предназначенных для конфигурирования устройства')
    p.style = 'ДОК Таблица Название'

    add_summ_table2(doc, isVirtKey,isVirtSwitch, isStatuses, isSysStatuses)


    doc.save("summ_table_templ.docx")

    doc2 = DocxTemplate("summ_table_templ.docx")

    # Формируем контекст для Jinja2
    context = {
        "fsu": fsu,
    }
 
    # Заполняем документ
    doc2.render(context)
    doc2.save("Таблица сигналов.docx")