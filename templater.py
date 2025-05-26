import os

from docxtpl import DocxTemplate
from docx import Document

from docx_handler import add_new_section, add_new_section_landscape
from tables import add_table_settings, add_table_reg, add_table_fks, add_table_leds_new

def fill_template(fsu, hardware):

    doc = DocxTemplate("temp.docx")

    # Формируем контекст для Jinja2
    context = {
        "fsu": fsu,
        "hardware": hardware,
    }
 
    # Заполняем документ
    doc.render(context)
    doc.save("output.docx")


def create_template(fsu, hardware):

    doc = Document('origin.docx')

    ############################################################################
    # СОЗДАЕМ РАЗДЕЛ С УСТАВКАМИ РЗА
    add_new_section(doc)

    p = doc.add_paragraph('УСТАВКИ РЗА')
    p.style = 'ДОК Заголовок 1'
    p = doc.add_paragraph('Группа уставок №1'+r'{% for fb in fsu.get_fbs() %}')
    p.style = 'ДОК Заголовок 2'

    p = doc.add_paragraph(r'{{ fb.get_description() }}{% for func in fb.functions if func.get_settings_for_bu() %}')
    p.style = 'ДОК Заголовок 3'

    p = doc.add_paragraph(r'{{ func.get_description() }}{% if func.get_name() %} ({{ func.get_name() }}){% endif %}')
    p.style = 'ДОК Таблица Название'

    add_table_settings(doc)

    p = doc.add_paragraph(r'{% endfor %}{% endfor %}')
    p.style = 'TAGS'    

    #############################################################################
    # СОЗДАЕМ РАЗДЕЛ С ПАРАМЕТРАМИ РЕГИСТРАЦИИ
    add_new_section_landscape(doc)

    p = doc.add_paragraph('НАСТРОЙКА ПАРАМЕТРОВ РЕГИСТРАЦИИ')
    p.style = 'ДОК Заголовок 1'

    text = doc.add_paragraph('Возможна регистрация не более 200 сигналов.')
    text.style = 'ДОК Текст'

    p = doc.add_paragraph('Сигналы для регистрации')
    p.style = 'ДОК Таблица Название'

    add_table_reg(doc)

    #############################################################################
    # СОЗДАЕМ РАЗДЕЛ С ПАРАМЕТРИРОВАНИЕ ДИСКРЕТНЫХ ВХОДОВ И ВЫХОДНЫХ РЕЛЕ
    add_new_section_landscape(doc) # Создаем раздел для матрицы вх/вых
    # Добавляем заголовок
    p = doc.add_paragraph('ПАРАМЕТРИРОВАНИЕ ДИСКРЕТНЫХ ВХОДОВ И ВЫХОДНЫХ РЕЛЕ')
    p.style = 'ДОК Заголовок 1'

    p = doc.add_paragraph('Дискретные входы')
    p.style = 'ДОК Заголовок 2'

    text = doc.add_paragraph('Для дискретного входа возможно подключение только одного сигнала.')
    text.style = 'ДОК Текст'



    #############################################################################
    # СОЗДАЕМ РАЗДЕЛ НАСТРОЙКА СВЕТОДИОДОВ И ФУНКЦИОНАЛЬНЫХ КЛАВИШ
    add_new_section_landscape(doc) # Создаем раздел для матрицы вх/вых
    # Добавляем заголовок
    p = doc.add_paragraph('НАСТРОЙКА СВЕТОДИОДОВ И ФУНКЦИОНАЛЬНЫХ КЛАВИШ')
    p.style = 'ДОК Заголовок 1'

    ###############################################################
    p = doc.add_paragraph('Светодиоды')
    p.style = 'ДОК Заголовок 2'

    text = doc.add_paragraph('Для светодиода возможно подключение до пяти сигналов.')
    text.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{% for leds_unit in hardware.get_hmi_leds() if hardware.get_hmi_leds() %}')
    p.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{{ leds_unit }}')
    p.style = 'ДОК Таблица Название'

    statuses_ = fsu.get_fsu_statuses()
    statuses = set([item['Полное наименование сигнала'] for item in statuses_])
    statuses = list(statuses)

    add_table_leds_new(doc, statuses)

    p = doc.add_paragraph(r'{% endfor %}')
    p.style = 'TAGS'    

    ###############################################################
    p = doc.add_paragraph('Функциональные клавиши')
    p.style = 'ДОК Заголовок 2'

    text = doc.add_paragraph('Для функциональной клавиши возможно подключение только одного управляющего сигнала.')
    text.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{% for fks_unit in hardware.get_hmi_fks() if hardware.get_hmi_fks() %}')
    p.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{{ fks_unit }}')
    p.style = 'ДОК Таблица Название'

    choices_ = fsu.get_fsu_control_list()
    choices = set([item['Наименование сигналов на ФСУ'] for item in choices_])
    choices = list(choices)

    add_table_fks(doc, choices)

    p = doc.add_paragraph(r'{% endfor %}')
    p.style = 'TAGS'

    ##################################################################



    doc.save("temp.docx")
