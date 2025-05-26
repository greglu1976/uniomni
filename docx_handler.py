# вынесено сюда всякое создание разделов 

from docx.enum.section import WD_ORIENTATION

def add_new_section(doc):
    # Создаем раздел для РЗА
    # Добавляем разрыв раздела
    section = doc.sections[-1]  # Получаем текущий раздел
    doc.add_section(section.start_type)  # Добавляем новый раздел
    return doc

def add_new_section_landscape(doc):
    # Создаем раздел для РЗА
    # Добавляем разрыв раздела
    current_section = doc.sections[-1]  # Получаем текущий раздел
    new_section = doc.add_section()
    # Копируем параметры из текущего раздела
    new_section.left_margin = current_section.left_margin
    new_section.right_margin = current_section.right_margin
    new_section.top_margin = current_section.top_margin
    new_section.bottom_margin = current_section.bottom_margin
    new_section.header_distance = current_section.header_distance
    new_section.footer_distance = current_section.footer_distance
    # Меняем ориентацию на альбомную
    new_section.orientation = WD_ORIENTATION.LANDSCAPE
    # Меняем размеры страницы
    new_section.page_width = current_section.page_height
    new_section.page_height = current_section.page_width
    return doc

def add_new_section_test(doc):
    # Получаем текущий раздел
    current_section = doc.sections[-1]

    # Добавляем новый раздел
    new_section = doc.add_section()

    # Устанавливаем альбомную ориентацию
    new_section.orientation = WD_ORIENTATION.LANDSCAPE
    new_section.page_width = current_section.page_height
    new_section.page_height = current_section.page_width

    # Отключаем связь с предыдущими колонтитулами
    new_section.header.is_linked_to_previous = False
    new_section.footer.is_linked_to_previous = False

    # Создаем новые колонтитулы для альбомной ориентации
    header = new_section.header
    footer = new_section.footer

    # Добавляем содержимое в колонтитулы
    header_para = header.paragraphs[0]
    footer_para = footer.paragraphs[0]

    # Здесь добавьте необходимое содержимое колонтитулов
    header_para.text = "Ваш верхний колонтитул"
    footer_para.text = "Ваш нижний колонтитул"

    # Устанавливаем стиль и форматирование для колонтитулов
    header_para.style = 'Header'  # или ваш собственный стиль
    footer_para.style = 'Footer'  # или ваш собственный стиль


