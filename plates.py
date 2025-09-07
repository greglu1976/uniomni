# ДАННЫЕ ПО ПЛАТАМ
# возможно далее будут собираться из xlsx файла
# пока так

def get_K002_data(slot):
    return {
    'general_data':{ 'Наименование': 'Отказ модуля', 'Обозначение':f'Слот М{slot}. Отказ модуля'

    }
}


def get_plate_data(name, slot):
    if name == 'K002':
        return get_K002_data(slot)