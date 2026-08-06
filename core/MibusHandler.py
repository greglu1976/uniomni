

# класс хэндлер файла MibusParameters_report.json

import json


class MibusHandler():
    def __init__(self):
        pass


    def __init__(self, root_path = ''):
        with open(root_path+"MibusParameters_report.json", 'r', encoding='utf-8') as f:
            self.data = json.load(f)


    def get_inputs(self):

            raw_inputs = None
            for datum in self.data:
                if datum["Name"] == "Входы ФБ логики, промежуточные переменные":
                    raw_inputs= datum 
                    break

            return raw_inputs.get('Parameters')    