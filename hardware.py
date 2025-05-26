# класс описывающий железо устройства

class Hardware:
    def __init__(self, order_card=''):
        self.order_card = order_card
        self.hmi_fks = ['ЮНИТ-ИЧМ', 'Плата ФК №1']
        self.hmi_leds = ['ЮНИТ-ИЧМ', 'Плата СД №1']

        self.inputs = [{'desc':'Слот М8. Тип платы В021', 'num_of_inputs':14},]


    def get_hmi_fks(self):
        return self.hmi_fks

    def get_hmi_leds(self):
        return self.hmi_leds        