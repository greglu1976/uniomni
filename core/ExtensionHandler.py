import json

class ExtensionHandler:

    def __init__(self):
        with open("EXTENSION.json", 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def find_enum_by_parameter_name(self, name):
        # 1. Ищем имя Enum по имени Параметра
        pars = self.data.get("Parameters", []) # Защита, если ключа нет
        enum_name = None
        
        for par in pars:
            # Используем .get(), чтобы не упасть, если ключа "Parameter" нет в словаре
            if par.get("Parameter") == name:
                enum_name = par.get("Enum")
                break
        
        # Если параметр вообще не найден или у него нет поля Enum
        if not enum_name:
            return None 

        # 2. Ищем значения по имени Enum
        enums = self.data.get("Enums", [])
        for en in enums:
            # Сравниваем имя Enum из параметра с именем в списке Enums
            if en.get("Enum") == enum_name:
                return en.get("Value")  # Возвращаем найденные значения
        
        # Если цикл закончился, значит Enum с таким именем не найден в разделе "Enums"
        return None


#a = ExtensionHandler()
#m = a.find_enum_by_parameter_name("Supervision_TimeSource")
#print(m)