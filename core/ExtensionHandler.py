import json

class ExtensionHandler:

    def __init__(self):
        with open("EXTENSION.json", 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def find_enum_by_parameter_name(self, name):
        print(self.data.get(name))


        pass


a = ExtensionHandler()
a.find_enum_by_parameter_name("Supervision_TimeSource")