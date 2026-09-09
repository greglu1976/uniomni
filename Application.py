import dearpygui.dearpygui as dpg

import gui.themes as themes

from logger.logger import Logger


from core.DeviceDataManager import DeviceDataManager
from core.SettingBlanc2 import SettingBlanc

from core.Manual2 import Manual

from core.LatexDoc import LatexDoc
from utils.additional import create_directories, save_obj, load_obj

class Application:
    def __init__(self):

        self.device_data = None

        self.device_data_manager = DeviceDataManager()
        self.devices_data = self.device_data_manager.get_all_devices()

        # Создаём список строк для отображения
        self.display_names = [
            f"Устройство: {device['name']}, Версия: {device['version']}"
            for device in self.devices_data
        ]

        self.init_button = None  # Будет хранить идентификатор кнопки
        self.setup_gui()

        self.load_config_callback()

        
    def setup_gui(self):
        dpg.create_context()

        # Подключаем светлую тему
        light_theme = themes.create_theme_imgui_light()
        dpg.bind_theme(light_theme)        
        # Настройка шрифтов
        with dpg.font_registry():
            default_font = dpg.add_font("gui/Montserrat-Regular.ttf", 15)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=default_font)
        dpg.bind_font(default_font)
        

        # Главное окно
        with dpg.window(label="Главное окно", width=400, height=400, pos=[20, 20]):
           
            # Сохраняем идентификатор комбобокса
            self.device_combo = dpg.add_combo(
                label="Устройство",
                items=[],
                width=300,
                enabled=False
            )
            dpg.add_spacer(height=5)

            # Сохраняем идентификатор кнопки
            #self.init_button = dpg.add_button(
                #label="Инициализировать устройство",
                #callback=self.create_device,
                #enabled=False,
                #width=300
            #)

            dpg.add_separator() 
            dpg.add_spacer(height=5)             
            dpg.add_button(label="Создать бланк уставок в docx", callback=self.generate_setting_blanc_docx, width=300)
            dpg.add_spacer(height=5)
            dpg.add_separator() 
            dpg.add_spacer(height=5)           
            dpg.add_button(label="Обновить таблицы с уставками в РЭ", callback=self.renew_setting_tables_re, width=300)
            dpg.add_button(label="Обновить таблицу сигналов в РЭ", callback=self.renew_sum_table_latex, width=300)
            dpg.add_button(label="Обновить перечень сокращений в РЭ", callback=self.renew_abbrs, width=300)            
            dpg.add_spacer(height=5)   
            dpg.add_separator()
            dpg.add_spacer(height=5)   

            dpg.add_button(label="Обновить перечень сокращений в РУ", callback=self.renew_abbrs_ru, width=300)
            dpg.add_spacer(height=5)
            dpg.add_separator() 
            dpg.add_spacer(height=5)  
            dpg.add_button(label="Очистить логи", callback=Logger.clear_logs, width=300)

            dpg.add_button(
                label="Перезагрузить config.ini",
                callback=self.load_config_callback,
                width=300
            )

            dpg.add_spacer(height=5)
            dpg.add_separator() 
            dpg.add_spacer(height=5) 

            dpg.add_button(
                label="Собрать в один файл latex (raw.tex)",
                callback=self.gen_raw_latex,
                width=300
            )

        # Окно логов
        heigh = 450
        with dpg.window(label="Логи", width=900, height=heigh, pos=[430, 20], tag="log_window"):
            with dpg.child_window(tag="log_container", height=heigh-35):
                dpg.add_group(tag="log_content")  # для добавления строк

        Logger.set_container("log_content", "log_window")
        
        dpg.create_viewport(title="Omni for M500 v0.0.2 09.09.26", width=1400, height=550)
        dpg.setup_dearpygui()

    def renew_abbrs_ru(self):
        self.start_device_task()
        manual = Manual(device_data=self.device_data)
        if manual.renew_abbrs_ru()==0:
            Logger.info('Перечень сокращений в РУ обновлен')
        else:
            Logger.error('При обновлении перечня сокращений РУ возникли ошибки')               

    def renew_abbrs(self):
        self.start_device_task()
        manual = Manual(device_data=self.device_data)
        manual.renew_abbrs()
        Logger.info('Перечень сокращений в РЭ обновлен')

    def generate_setting_blanc_docx(self):
        self.start_device_task()
        Logger.info('Начинаем создавать бланк уставок...')
        setting_blanc = SettingBlanc(self.device_data)
        setting_blanc.get_blanc()
        #Logger.info('Бланк уставок в docx создан')

    def renew_setting_tables_re(self):
        self.start_device_task()
        manual = Manual(device_data=self.device_data)
        manual.renew_setting_tables_re()
        Logger.info('Таблицы с уставками в РЭ обновлены')

    def renew_sum_table_latex(self):
        self.start_device_task()
        manual = Manual(device_data=self.device_data)
        manual.renew_sum_table_latex()
        #Logger.info('Суммарная таблица сигналов приложения в РЭ обновлена')

    #def add_to_sqlite(self):
        #Logger.info('Запуск задачи обновления БД')
        #process_all_xlsx_files("db")
        #Logger.info('Задача обновления БД завершена')

#######################################################################
######################################################################

    def load_config_callback(self):
        """Обработчик загрузки конфига"""
        #if self.device_manager.load_config():
        #devices = self.device_manager.get_device_names()
        #devices = self.device_names_with_versions
        devices = self.display_names
        if devices:
            # Используем сохраненные идентификаторы
            dpg.configure_item(self.device_combo, items=devices, enabled=True)
            #dpg.configure_item(self.init_button, enabled=True)
            Logger.info("Конфигурация загружена успешно")
        else:
            Logger.warning("Устройства не найдены в конфигурации")
        #else:
            #Logger.error("Ошибка загрузки конфигурации")

    def start_device_task(self):
        """Запуск задачи устройства"""

        selected_text = dpg.get_value(self.device_combo)

        if not selected_text:
            Logger.error("Устройство не выбрано")
            return

        # Создаем словарь для быстрого поиска
        display_to_device_map = {
            f"Устройство: {device['name']}, Версия: {device['version']}": device
            for device in self.devices_data
        }

        # Находим устройство по отображаемому тексту
        device = display_to_device_map.get(selected_text)
        if device is None:
            Logger.error("Выбранное устройство не найдено в конфигурации")
            return

        Logger.info(f"Выбрано устройство: {device['name']} v{device['version']}")


        # Получаем данные устройства
        self.device_data = self.device_data_manager.get_device_by_name_and_version(
            name=device['name'], 
            version=device['version']
        )
        
        if not self.device_data:
            Logger.error(f"Не удалось получить данные для устройства {device['name']} v{device['version']}")
            return False


    def gen_raw_latex(self):

        Logger.info('Пытаемся создать единый файл latex')

        if not self.is_device_selected():
            Logger.warning('Устройство не выбрано')
            return
        if self.device_data is None:
            self.start_device_task()

        create_directories()
        # Сохраняем в файл объект РЭ
        #save_obj(self.re_)

        path =self.device_data["path_to_latex_desc"] + '/_manual_latex'

        LatexDoc(path)
        Logger.info('Проект latex для РЭ создан. См. папку latex_build')        
        #process_all_xlsx_files("db")
        #Logger.info('Задача обновления БД завершена')

#######################################################################

    #def create_device(self):
        # Создаем устройство
        #self.start_device_task()

        #order_code = self.device_data["order_code"]
        #full_description = self.device_data["full_description"]
        #order_code_hmi = self.device_data["order_code_hmi"]
        
        #self.device = Device(
            ##order_code=order_code, 
            #full_description=full_description, 
            #order_code_hmi=order_code_hmi
        #)

        # Проверяем, что устройство успешно инициализировалось
       #if self.device is None:
            #Logger.error("Ошибка: устройство не было создано")
            #return False
        
        # Дополнительные проверки (если есть в классе Device)
        #if hasattr(self.device, 'is_initialized'):
            #if not self.device.is_initialized:
                #Logger.error("Устройство создано, но не инициализировано корректно")
                #return False
        
        #Logger.info(f"Устройство: {self.device_data['name']} v{self.device_data['version']} успешно инициализировано")
        #return True

    def is_device_selected(self):
        """Проверяет, выбрано ли устройство и инициализированы ли его данные"""
        # Проверяем, что в комбобоксе что-то выбрано
        selected_text = dpg.get_value(self.device_combo)
        if not selected_text:
            return False
        return True
    
    def run(self):
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()