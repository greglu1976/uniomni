# класс описывающий железо устройства

class Hardware:
    def __init__(self, versions_bu, info,):

        self.versions_bu = versions_bu
        self.info = info

        self.terminal_short_name = ''                   # короткое обозначение терминала, например ЮНИТ-М300-Т
        self.terminal_description = info['title_name']  # описание терминала на титульном листе
        self.num_of_bins = {'B001':8, 'В001':8, 'B021':14, 'В021':14, 'K001':8, 'К001':8, 'K002':8, 'К002':8, 'P02c':1, 'Р02с':1,} # здесь храним тип плат и количество входов выходов на ней

        self.hmi_short_name = '' # короткое обозначение ИЧМ, например ЮНИТ-ИЧМ

        self.hmi_fks = ['ЮНИТ-ИЧМ', ]
        self.hmi_leds = ['ЮНИТ-ИЧМ',]

        self.inputs = []
        self.outputs = []

        self._parse_code_ied()
        self._parse_code_hmi()

    def _parse_code_ied(self):
        if self.info['order_card_ied']=='':
            return
        parts = self.info['order_card_ied'].split('-')
        self.terminal_short_name = f"{parts[0]}-{parts[1]}-{parts[2]}"

        for i, part in enumerate(parts[3:], start=1):  # start=4 для нумерации с 4
            #print(f"{i}. {part}")  # Пример обработки

            if part.startswith('K') or part.startswith('К') or part=='P02c' or part=='Р02с' : # значит плата выходов
                dict_temp = {'desc': f'Слот М{i}. Тип платы {part}',
                'num_of_outputs':self.num_of_bins.get(part)}
                self.outputs.append(dict_temp)
                continue

            if part.startswith('B') or part.startswith('В'): # значит плата выходов
                dict_temp = {'desc': f'Слот М{i}. Тип платы {part}', 
                'num_of_inputs':self.num_of_bins.get(part)}
                self.inputs.append(dict_temp)
                continue            
  

    def _parse_code_hmi(self):
        if self.info['order_card_hmi']=='':
            return
        parts = self.info['order_card_hmi'].split('-')
        self.hmi_short_name = f"{parts[0]}-{parts[1]}"

        for i, part in enumerate(parts[3:], start=1):  # start=4 для нумерации с 4
            print(f"{i}. {part}")  # Пример обработки
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
        return self.info['code_bu'] 

    def get_terminal_short_name(self):
        return self.terminal_short_name

    def get_versions_for_bu(self):
        print(self.versions_bu)
        return self.versions_bu         