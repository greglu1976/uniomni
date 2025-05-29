# ГЕНЕРАЦИЯ И ЗАПОЛНЕНИЕ ШАБЛОНА БЛАНКА УСТАВОК
import os

from docxtpl import DocxTemplate
from docx import Document

from docx_handler import add_new_section, add_new_section_landscape
from tables import add_table_settings, add_table_reg, add_table_fks, add_table_leds_new, add_table_mtrx_ins, add_table_mtrx_outs, add_table_binaries

def fill_template(fsu, hardware):

    doc = DocxTemplate("temp.docx")

    # Формируем контекст для Jinja2
    context = {
        "fsu": fsu,
        "hardware": hardware,
    }
 
    # Заполняем документ
    doc.render(context)
    doc.save("Бланк уставок.docx")


def create_template(fsu, hardware):

    doc = Document('origin.docx')

    ############################################################################
    # СОЗДАЕМ РАЗДЕЛ С КОНФИГУРАЦИЕЙ ВХОДОВ ВЫХОДОВ
    add_new_section(doc)

    p = doc.add_paragraph('КОНФИГУРАЦИЯ ДИСКРЕТНЫХ ВХОДОВ И РЕЛЕ')
    p.style = 'ДОК Заголовок 1'

    p = doc.add_paragraph('Модули дискретных входов'+r'{% for plate in hardware.get_hw_plates() if hardware.get_hw_plates() %}' + r'{% if plate.get_inputs() %}')
    p.style = 'ДОК Заголовок 2'


    p = doc.add_paragraph(r'Слот М{{ plate.get_slot() }}. Тип платы {{ plate.get_name() }}'+r'{% for items in plate.get_inputs() %}')
    p.style = 'ДОК Заголовок 3'


    p = doc.add_paragraph(r'Дискретный вход {{ loop.index }}')
    p.style = 'ДОК Таблица Название'

    add_table_binaries(doc)

    p = doc.add_paragraph(r'{% endfor %}{% endif %}{% endfor %}')
    p.style = 'TAGS'

    #################################################################################
    p = doc.add_paragraph('Модули выходных реле'+r'{% for plate in hardware.get_hw_plates() if hardware.get_hw_plates() %}' + r'{% if plate.get_outputs() %}')
    p.style = 'ДОК Заголовок 2'


    p = doc.add_paragraph(r'Слот М{{ plate.get_slot() }}. Тип платы {{ plate.get_name() }}'+r'{% for items in plate.get_outputs() %}')
    p.style = 'ДОК Заголовок 3'

    p = doc.add_paragraph(r'Реле {{ loop.index }}')
    p.style = 'ДОК Таблица Название'

    add_table_binaries(doc)

    p = doc.add_paragraph(r'{% endfor %}{% endif %}{% endfor %}')
    p.style = 'TAGS'

    ############################################################################
    # СОЗДАЕМ РАЗДЕЛ С УСТАВКАМИ РЗА
    add_new_section(doc)

    p = doc.add_paragraph('УСТАВКИ РЗА')
    p.style = 'ДОК Заголовок 1'
    p = doc.add_paragraph('Группа уставок №1'+r'{% for fb in fsu.get_fbs() %}')
    p.style = 'ДОК Заголовок 2'


    p = doc.add_paragraph(r'{{ fb.get_description() }}{% for func in fb.functions %}'
                        r'{% if func.get_settings_for_bu() %}')
    p.style = 'ДОК Заголовок 3'

    p = doc.add_paragraph(r'{{ func.get_description() }}{% if func.get_name() %} ({{ func.get_name() }}){% endif %}'
                        r'{% endif %}{% endfor %}')
    p.style = 'ДОК Таблица Название'



    #p = doc.add_paragraph(r'{{ fb.get_description() }}{% for func in fb.functions if func.get_settings_for_bu() %}')
    #p.style = 'ДОК Заголовок 3'

    #p = doc.add_paragraph(r'{{ func.get_description() }}{% if func.get_name() %} ({{ func.get_name() }}){% endif %}')
    #p.style = 'ДОК Таблица Название'

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

    p = doc.add_paragraph(r'{% for input_plate in hardware.get_inputs() if hardware.get_inputs() %}')
    p.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{{ input_plate.desc }}')
    p.style = 'ДОК Таблица Название'

    inputs_ = fsu.get_fsu_inputs_list()
    inputs = set([item['Полное наименование сигнала'] for item in inputs_])
    inputs = sorted(list(inputs))

    add_table_mtrx_ins(doc, inputs)

    p = doc.add_paragraph(r'{% endfor %}')
    p.style = 'TAGS'   

    ############################### ВЫХОДНЫЕ РЕЛЕ ####################################

    p = doc.add_paragraph('Выходные реле')
    p.style = 'ДОК Заголовок 2'

    text = doc.add_paragraph('Возможно подключение до пяти сигналов на одно выходное реле.')
    text.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{% for output_plate in hardware.get_outputs() if hardware.get_outputs() %}')
    p.style = 'ДОК Текст'

    p = doc.add_paragraph(r'{{ output_plate.desc }}')
    p.style = 'ДОК Таблица Название'

    statuses_ = fsu.get_fsu_statuses()
    statuses = set([item['Полное наименование сигнала'] for item in statuses_])
    statuses = sorted(list(statuses))

    add_table_mtrx_outs(doc, statuses)

    p = doc.add_paragraph(r'{% endfor %}')
    p.style = 'TAGS' 


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

    #statuses_ = fsu.get_fsu_statuses() # Выше вычисляются statuses
    #statuses = set([item['Полное наименование сигнала'] for item in statuses_])
    #statuses = list(statuses)

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
    choices = sorted(list(choices))

    add_table_fks(doc, choices)

    p = doc.add_paragraph(r'{% endfor %}')
    p.style = 'TAGS'

    ##################################################################

    doc.save("temp.docx")
