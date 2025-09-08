# класс описывающий железо устройства

from general import InOutPart

from configdata import *

class Hardware:
    def __init__(self, versions_bu, info):

        self.versions_bu = versions_bu
        self._info = info

        self.terminal_short_name = ''                   # короткое обозначение терминала, например ЮНИТ-М300-Т
        self.terminal_description = info['title_name']  # описание терминала на титульном листе
        #self.num_of_bins = {'B001':8, 'В001':8, 'B021':14, 'В021':14, 'K001':8, 'К001':8, 'K002':8, 'К002':8, 'P02c':1, 'Р02с':1,} # здесь храним тип плат и количество входов выходов на ней

        self.hmi_short_name = '' # короткое обозначение ИЧМ, например ЮНИТ-ИЧМ
        self._order_code_parsed = []
        self.hmi_fks = ['ЮНИТ-ИЧМ', ]
        self.hmi_leds = ['ЮНИТ-ИЧМ',]

        self.inputs = []
        self.outputs = []
        self.hw_plates = []
        self._parse_code_ied()
        self._parse_code_hmi()
        # захардкоженные данные по синхронизации устройства - полагается одни на все устройства
        self.config_sync = ConfigSync() 
        self.config_cpu = ConfigCPU()
        self.config_disturb = ConfigDisturb()         

    def _parse_code_ied(self):
        if self._info['order_card_ied']=='':
            return
        parts = self._info['order_card_ied'].split('-')
        self._order_code_parsed = parts
        self.terminal_short_name = f"{parts[0]}-{parts[1]}-{parts[2]}"

        # ИНИЦИАЛИЗИРУЕМ ПЛАТЫ ВХОДОВ ВЫХОДОВ ПО КОДУ ЗАКАЗА
        inouts = InOutPart(self._info['order_card_ied'])
        self.hw_plates = inouts.get_plates()

        for plate in self.hw_plates:
            if 'B' in plate.get_name():
                dict_temp = {'desc': f'Слот М{plate.get_slot()}. Тип платы {plate.get_name()}',
                'num_of_inputs':plate.get_num_of_inputs()}
                self.inputs.append(dict_temp)
                continue
            if 'K' in plate.get_name() or 'P' in plate.get_name():
                dict_temp = {'desc': f'Слот М{plate.get_slot()}. Тип платы {plate.get_name()}',
                'num_of_outputs':plate.get_num_of_outputs()}
                self.outputs.append(dict_temp)
                continue            
      
    def _parse_code_hmi(self):
        if self._info['order_card_hmi']=='':
            return
        parts = self._info['order_card_hmi'].split('-')
        self.hmi_short_name = f"{parts[0]}-{parts[1]}"

        for i, part in enumerate(parts[3:], start=1):  # start=4 для нумерации с 4
            #print(f"{i}. {part}")  # Пример обработки
            if part.startswith('C') or part.startswith('С'):
                temp = f'Модуль расширения на 16 светодиодов №{i}'
                self.hmi_leds.append(temp)               
            if part.startswith('K') or part.startswith('К'):
                temp = f'Модуль расширения на 16 функциональных кнопок №{i}'
                self.hmi_fks.append(temp)

    def get_hmi_fks(self):
        return self.hmi_fks

    def get_hmi_leds(self):
        return self.hmi_leds        

    def get_inputs(self):
        return self.inputs

    def get_outputs(self):
        return self.outputs   

    def get_desc_for_bu(self):
        return self.terminal_description +'\n«' + self.terminal_short_name + '»'   

    def get_code_for_bu(self):
        return self._info['code_bu'] 

    def get_terminal_short_name(self):
        return self.terminal_short_name

    def get_versions_for_bu(self):
        return self.versions_bu  

    def get_hw_plates(self):
        return self.hw_plates

    def get_order_code_parsed(self):
        return self._order_code_parsed

    @property
    def info(self):
        return self._info    

################################################# ГЕТТЕРЫ ЗАХАРДКОЖЕННЫХ ДАННЫХ ОПИСАНИЯ КОНФИГУРАЦИИ
    def get_config_sync(self):
        return self.config_sync.get_info()

    def get_config_cpu(self):
        return self.config_cpu.get_info()

    def get_config_disturb(self):
        return self.config_disturb.get_info()