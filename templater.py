
from docxtpl import DocxTemplate


def fill_template(fsu):

    doc = DocxTemplate("templ.docx")



    #for func in fb.functions:

    # Формируем контекст для Jinja2
    context = {
        "fsu": fsu,
    }

    #print(func.get_iec_name(), func.get_name(), func.get_description())
    #print('=================================')   
    # Заполняем документ
    doc.render(context)



    doc.save("output.docx")