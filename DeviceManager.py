import os
import configparser
from ast import literal_eval

class DeviceManager:
    def __init__(self):
        self.config = None
        self.devices = {}
        self.current_device = None
        self.general_settings = None        
        self.config_loaded = False

    def load_config(self, file_path='config.ini'):
        """Загрузка конфигурации"""
        self.config = configparser.ConfigParser()
        if os.path.exists(file_path):
            try:
                self.config.read(file_path, encoding='utf-8')

                # Получаем общие настройки
                self.general_settings = {'path_to_fsu': self.config.get('GENERAL', 'path_to_fsu', fallback=None)}

                self.devices = {}
                
                device_sections = [s for s in self.config.sections() 
                                 if s.startswith('DEVICE')]
                
                for section in device_sections:
                    try:
                        self.devices[section] = {
                            'name': self.config.get(section, 'name'),
                            'version': self.config.get(section, 'version'),
                            'path_to_latex_desc': self.config.get(section, 'path_to_latex_desc'),
                            'path_to_hardware_desc': self.config.get(section, 'path_to_hardware_desc'),
                            'fbs_list': literal_eval(self.config.get(section, 'fbs_list')),
                            'path_to_ru_desc': self.config.get(section, 'path_to_ru_desc')
                        }
                    except Exception as e:
                        continue
                
                self.config_loaded = True
                return True
            except Exception as e:
                return False
        return False

    def get_device_names(self):
        """Получение списка устройств"""
        return [f"{d['name']} v{d['version']}" for d in self.devices.values()]

    def get_general_settings(self):
        return self.general_settings

    def set_current_device(self, device_name):
        """Установка текущего устройства"""
        for section, device in self.devices.items():
            if f"{device['name']} v{device['version']}" == device_name:
                self.current_device = {**device, 'section': section}
                return True
        return False
