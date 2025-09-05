# описаны объекты вида диск вход выход , платы ввода вывода

# БОЛВАНКИ ОПИСАНИЯ ДИСКРЕТОВ
class Bin_Input:
    def __init__(self, slot, binary_number):
        self.binary_number = binary_number
        self.slot = slot

    def get_info(self):
        l = [
        {'Описание':'Режим работы входа', 'Наименование ПО':f'Слот М{self.slot}. ДВ{self.binary_number}. Режим', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 = Не активен\n 1 = Активен', 'Ед. изм.':'-', 'Шаг':'-', 'Значение по умолчанию':'Не активен'},
        {'Описание':'Задержка срабатывания входа', 'Наименование ПО':f'Слот М{self.slot}. ДВ{self.binary_number}. Задержка сраб.', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 100', 'Ед. изм.':'мс', 'Шаг':'1', 'Значение по умолчанию':'20'},
        {'Описание':'Режим инверсии входа', 'Наименование ПО':f'Слот М{self.slot}. ДВ{self.binary_number}. Инверсия', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 = Не предусмотрено\n 1 = Предусмотрено', 'Ед. изм.':'-', 'Шаг':'-', 'Значение по умолчанию':'Не предусмотрено'},
        {'Описание':'Назначение входа', 'Наименование ПО':f'Слот М{self.slot}. ДВ{self.binary_number}. Описание', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 31', 'Ед. изм.':'Символ', 'Шаг':'-', 'Значение по умолчанию':'-'}
        ]
        return l
    def get_number(self):
        return self.binary_number     

class Bin_Output:
    def __init__(self, slot, binary_number):
        self.binary_number = binary_number
        self.slot = slot

    def get_info(self):
        l = [
        {'Описание':'Режим работы реле', 'Наименование ПО':f'Слот М{self.slot}. Реле{self.binary_number}. Режим', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 = Выведено\n 1 = Без фиксации\n 2 = С фиксацией\n 3 = Импульсный', 'Ед. изм.':'-', 'Шаг':'-', 'Значение по умолчанию':'Без фиксации'},
        {'Описание':'Длительность импульса', 'Наименование ПО':f'Слот М{self.slot}. Реле{self.binary_number}. Дл. имп.', 'Наименование ФСУ':'T1', 'Значение / Диапазон':' 10 ... 10000', 'Ед. изм.':'мс', 'Шаг':'10', 'Значение по умолчанию':'1000'},
        {'Описание':'Назначение реле', 'Наименование ПО':f'Слот М{self.slot}. Реле{self.binary_number}. Описание', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 31', 'Ед. изм.':'Символ', 'Шаг':'-', 'Значение по умолчанию':'-'}]
        return l
    def get_number(self):
        return self.binary_number         

# ПРЕДСТАВЛЕНИЕ ВХОДА НАПРЯЖЕНИЯ
class VoltInput:
    def __init__(self, slot, binary_number):
        self.binary_number = binary_number
        self.slot = slot
    def get_info(self):
        l = [
        {'Описание':'Вид представляемой величины', 'Наименование ПО':f'Вид представляемой величины {self.binary_number}', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 6', 'Ед. изм.':'-', 'Шаг':'1', 'Значение по умолчанию':'0'},
        {'Описание':'Тип измерительного датчика', 'Наименование ПО':f'Тип измерительного датчика {self.binary_number}', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 4', 'Ед. изм.':'-', 'Шаг':'1', 'Значение по умолчанию':'0'},
        {'Описание':'Вид замера (фазное/линейное)', 'Наименование ПО':f'Вид замера (фазное/линейное) {self.binary_number}', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 2', 'Ед. изм.':'-', 'Шаг':'1', 'Значение по умолчанию':'0'},
        ]
        return l
    def get_number(self):
        return self.binary_number         

# ПРЕДСТАВЛЕНИЕ ВХОДА ТОКА
class CurrInput:
    def __init__(self, slot, binary_number):
        self.binary_number = binary_number
        self.slot = slot
    def get_info(self):
        l = [
        {'Описание':'Вид представляемой величины', 'Наименование ПО':f'Вид представляемой величины {self.binary_number}', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 6', 'Ед. изм.':'-', 'Шаг':'1', 'Значение по умолчанию':'0'},
        {'Описание':'Тип измерительного датчика', 'Наименование ПО':f'Тип измерительного датчика {self.binary_number}', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 4', 'Ед. изм.':'-', 'Шаг':'1', 'Значение по умолчанию':'0'},
        {'Описание':'Вид замера (фазное/линейное)', 'Наименование ПО':f'Вид замера (фазное/линейное) {self.binary_number}', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 2', 'Ед. изм.':'-', 'Шаг':'1', 'Значение по умолчанию':'0'},
        ]
        return l
    def get_number(self):
        return self.binary_number   

# ОПИСАНИЕ ОБЩЕЙ ИНФОРМАЦИИ
class GeneralInfo():
    def __init__(self, type):
        self.type = type
    def get_info(self):
        info = []
        if  self.type == 'P02c':
            info = [{'Описание':'Напряжение несимметрии', 'Наименование ПО':'U несимм. пит.', 'Наименование ФСУ':'-', 'Значение / Диапазон':' 0 ... 220', 'Ед. изм.':'В', 'Шаг':'10', 'Значение по умолчанию':'0'},
            {'Описание':'Формирование синхросигнала от PPS', 'Наименование ПО':'Формирование синхросигнала от PPS', 'Наименование ФСУ':'-', 'Значение / Диапазон':'  0 = Введено\n 1 = Выведено', 'Ед. изм.':'-', 'Шаг':'-', 'Значение по умолчанию':'Выведено'}]  
        return info

# ОПИСАНИЕ ПЛАТ

class Plate():
    def __init__(self, name, rus_name, inputs_number, outputs_number, volts_number, curr_number, slot):

        self.name = name # Тип платы B001, K002 и т.д.
        self.rus_name = rus_name        
        self.inputs = []
        self.outputs =[]
        self.volts = []
        self.currents =[]        
        self.gen_info = []
        self.inputs_number = inputs_number
        self.outputs_number = outputs_number
        self.volts_number = volts_number 
        self.curr_number = curr_number                 
        self.slot = slot

        self._start()

    def _start(self):
        if self.name == 'P02c':
            obj_info = GeneralInfo('P02c')
            self.gen_info = obj_info.get_info()
        # Общий счетчик для всех циклов
        counter = 1            
        
        for i in range(self.inputs_number):
            temp = Bin_Input(self.slot, counter)
            obj_in = temp.get_info()
            self.inputs.append(obj_in)
            counter += 1  # увеличиваем после каждого элемента
        
        for a in range(self.outputs_number):
            temp = Bin_Output(self.slot, counter)
            obj_out = temp.get_info()
            self.outputs.append(obj_out)
            counter += 1  # увеличиваем после каждого элемента
        
        for k in range(self.volts_number):
            temp = VoltInput(self.slot, counter)
            obj_volts = temp.get_info()
            self.volts.append(obj_volts)
            counter += 1  # увеличиваем после каждого элемента
        
        for t in range(self.curr_number):
            temp = CurrInput(self.slot, counter)
            obj_currs = temp.get_info()
            self.currents.append(obj_currs)
            counter += 1  # увеличиваем после каждого элемента

    def get_name(self):
        if self.name.startswith('B'):
            return f'Модуль дискретных входов ({self.name})'
        elif self.name.startswith('K'): 
            return f'Модуль выходных реле ({self.name})'
        elif self.name.startswith('P'): 
            return f'Модуль питания ({self.name})'  
        elif self.name.startswith('M'): 
            return f'Измерительный модуль ({self.name})'        
        return self.name
    def get_slot(self):
        return self.slot
    def get_num_of_inputs(self):
        return self.inputs_number
    def get_num_of_outputs(self):
        return self.outputs_number
    def get_inputs(self):
        return self.inputs
    def get_outputs(self):
        return self.outputs
    def get_info(self):
        return self.gen_info
    def get_volts(self):
        return self.volts
    def get_currents(self):
        return self.currents

class InOutPart():
    def __init__(self, order_card_ied):
        self.order_card_ied = order_card_ied
        self.plates = []
        self._start()

    def _start(self):    
        parts = self.order_card_ied.split('-')
        main_name = second_name = ''
        for i, part in enumerate(parts[3:], start=1):
            if part == 'B001' or part =='В001':
                plate = Plate('B001', 'В001', 8, 0, 0, 0, i)
                self.plates.append(plate)
                continue   
            if part == 'B021' or part =='В021':
                plate = Plate('B021', 'В021', 14, 0, 0, 0, i)
                self.plates.append(plate)
                continue 
            if part == 'K001' or part =='К001':
                plate = Plate('K001', 'К001', 0, 8, 0, 0, i)
                self.plates.append(plate)
                continue 
            if part == 'K002' or part =='К002':
                plate = Plate('K002', 'К002', 0, 8, 0, 0, i)
                self.plates.append(plate)
                continue 
            if part == 'P02c' or part =='Р02с':
                plate = Plate('P02c', 'Р02с', 0, 0, 0, 0, i)
                self.plates.append(plate)
                continue

            if part.startswith('M') or part.startswith('М'):
                main_name = part.split('.')[0]
                second_name = part.split('.')[1]               
                if main_name == 'М046' or main_name =='M046':
                    plate = Plate('M046', 'М046', 0, 0, 6, 4, i)
                    self.plates.append(plate)
                    print('ADD1!')
                    continue
                if main_name == 'М090' or main_name =='M090':
                    plate = Plate('M090', 'М090', 0, 0, 6, 4, i)
                    self.plates.append(plate)
                    print('ADD!')                
                    continue            
    def get_plates(self):
        #for plate in self.plates:
            #print(plate.get_name(), plate.get_slot())
        return self.plates