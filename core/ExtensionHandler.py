import json

class ExtensionHandler:

    def __init__(self, root_path = ''):
        with open(root_path+"EXTENSION.json", 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def find_enum_by_parameter_name(self, name):
        # 1. Ищем имя Enum по имени Параметра
        pars = self.data.get("Parameters", []) # Защита, если ключа нет
        #print(pars)
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

    def find_trans_by_parameter_name(self, name):
        # 1. Ищем имя Enum по имени Параметра
        pars = self.data.get("Parameters", []) # Защита, если ключа нет
        #print(pars)
        enum_name = None
        
        for par in pars:
            # Используем .get(), чтобы не упасть, если ключа "Parameter" нет в словаре
            if par.get("Parameter") == name:
                enum_name = par.get("Transformation")
                break
      
        # Если параметр вообще не найден или у него нет поля Enum
        if not enum_name:
            return None, None 

        trans = self.data.get("Transformations", []) 


        for en in trans:
            # Сравниваем имя Enum из параметра с именем в списке Enums
            units_data = en.get("AvailableUnits")
            str = " / ".join(item["Units"] for item in units_data)
            if en.get("Transformation") == enum_name:
                return en.get("InitialDeclarationUnits"), str  # Возвращаем найденные значения
        
        # Если цикл закончился, значит Enum с таким именем не найден в разделе "Enums"
        return None, None 

    def find_units_by_type(self, name, unit_type="Secondary"):
        """
        unit_type: 'Primary' | 'Secondary' | 'Relative'
        Возвращает строку с единицей нужного типа или None.
        """
        pars = self.data.get("Parameters", [])
        trans_name = None
        for par in pars:
            if par.get("Parameter") == name:
                trans_name = par.get("Transformation")
                break
        if not trans_name:
            return None

        for en in self.data.get("Transformations", []):
            if en.get("Transformation") != trans_name:
                continue
            for u in en.get("AvailableUnits", []):
                if u.get("Type") == unit_type:
                    return u.get("Units")
            return None
        return None

#a = ExtensionHandler()
#m = a.find_enum_by_parameter_name("Supervision_TimeSource")
#print(m)