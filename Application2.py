import dearpygui.dearpygui as dpg
import threading
from logger import Logger



import themes

from utils import create_directories, save_obj, load_obj

from DeviceManager import DeviceManager
from ExploitationGuideLatex import ExploitationGuideLatex

from LatexDoc import LatexDoc

class Application:
    def __init__(self):
        self.device_manager = DeviceManager()
        self.init_button = None  # Будет хранить идентификатор кнопки
        self.setup_gui()
        self.re_ = None
        self.sum_table_type = 2  # По умолчанию выбран тип 2
        
    def setup_gui(self):
        dpg.create_context()
        # Подключаем светлую тему
        light_theme = themes.create_theme_imgui_light()
        dpg.bind_theme(light_theme)        
        # Настройка шрифтов
        with dpg.font_registry():
            default_font = dpg.add_font("Montserrat-Regular.ttf", 15)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=default_font)
        dpg.bind_font(default_font)
        
        # Главное окно
        with dpg.window(label="Главное окно", width=400, height=450):
            dpg.add_button(
                label="Считать config.ini",
                callback=self.load_config_callback,
                width=200
            )
            dpg.add_spacer(height=5)
            
            # Сохраняем идентификатор кнопки
            self.init_button = dpg.add_button(
                label="Инициализировать устройство",
                callback=self.start_device_task,
                enabled=False
            )

            dpg.add_button(label="Обновить таблицы с уставками в РЭ", callback=self.renew_setting_tables_re)
            
            # Группа для выбора типа суммарной таблицы
            with dpg.group(horizontal=True):
                dpg.add_text("Тип суммарной таблицы:")
                dpg.add_radio_button(
                    items=["Тип 1", "Тип 2"],
                    default_value="Тип 2",
                    callback=self.set_sum_table_type,
                    horizontal=True
                )
                
            dpg.add_button(label="Обновить суммарную таблицу сигналов приложения А в РЭ", callback=self.renew_sum_table_latex)
            dpg.add_button(label="Создать суммарную таблицу сигналов в docx", callback=self.generate_sum_table_docx)
            dpg.add_button(label="Создать бланк уставок в docx", callback=self.generate_setting_blanc_docx)
            dpg.add_button(label="Обновить перечень сокращений в РЭ", callback=self.renew_abbrs)
            dpg.add_button(label="Обновить перечень сокращений в РУ", callback=self.renew_abbrs_ru)
            dpg.add_spacer(height=10)
            dpg.add_button(label="Создать единый проект latex для РЭ", callback=self.create_raw_tex)
            dpg.add_button(label="Загрузить объект РЭ из latex_build", callback=self.load_tex)
            dpg.add_spacer(height=10)
            dpg.add_button(label="Очистить логи", callback=Logger.clear_logs)

            # Сохраняем идентификатор комбобокса
            self.device_combo = dpg.add_combo(
                label="Устройство",
                items=[],
                width=300,
                enabled=False
            )

        # Окно логов
        with dpg.window(label="Логи", width=800, height=400, pos=[400, 0], tag="log_window"):
            with dpg.child_window(tag="log_container", height=325):
                dpg.add_group(tag="log_content")  # для добавления строк

        Logger.set_container("log_content", "log_window")
        
        dpg.create_viewport(title="Omni v0.3.8 08.09.25", width=1215, height=450)
        dpg.setup_dearpygui()

    def set_sum_table_type(self, sender, app_data):
        """Установка типа суммарной таблицы"""
        self.sum_table_type = 2 if app_data == "Тип 2" else 1
        Logger.info(f"Выбран тип суммарной таблицы: {app_data}")

    def renew_abbrs_ru(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            self.re_.renew_abbrs_ru()
            Logger.info('Перечень сокращений в РУ обновлен')

    def renew_abbrs(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            self.re_.renew_abbrs()
            Logger.info('Перечень сокращений в РЭ обновлен')

    def generate_setting_blanc_docx(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            self.re_.generate_setting_blanc_docx()
            Logger.info('Бланк уставок в docx создан')

    def generate_sum_table_docx(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            self.re_.generate_sum_table_docx()
            Logger.info(f'Суммарная таблица сигналов в docx создана')

    def renew_setting_tables_re(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            self.re_.renew_setting_tables_re()
            Logger.info('Таблицы с уставками в РЭ обновлены')

    def renew_sum_table_latex(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            self.re_.renew_sum_table_latex(table_type=self.sum_table_type)
            Logger.info(f'Суммарная таблица сигналов приложения А (тип {self.sum_table_type}) в РЭ обновлена')

    def create_raw_tex(self):
        if self.re_ is None:
            Logger.error('Устройство не инициализировано!')
        else:
            Logger.warning('Папка latex_build будет очищена...')

            # Создаем директории
            create_directories()
            # Сохраняем в файл объект РЭ
            save_obj(self.re_)

            path = self.re_.path_to_latex_desc / '_manual_latex'
            raw_tex = LatexDoc(path)
            Logger.info('Проект latex для РЭ создан. См. папку latex_build')

    def load_tex(self):
        if self.re_ is not None:
            Logger.warning('Устройство будет перезаписано объектом РЭ из latex_build...')
        self.re_ = load_obj()    
        Logger.info(f'Объект РЭ по пути {self.re_.path_to_latex_desc} загружен из latex_build...')


    def load_config_callback(self):
        """Обработчик загрузки конфига"""
        if self.device_manager.load_config():
            devices = self.device_manager.get_device_names()
            if devices:
                # Используем сохраненные идентификаторы
                dpg.configure_item(self.device_combo, items=devices, enabled=True)
                dpg.configure_item(self.init_button, enabled=True)
                Logger.info("Конфигурация загружена успешно")
            else:
                Logger.warning("Устройства не найдены в конфигурации")
        else:
            Logger.error("Ошибка загрузки конфигурации")

    def start_device_task(self):
        """Запуск задачи устройства"""
        device_name = dpg.get_value(self.device_combo)
        if device_name and self.device_manager.set_current_device(device_name):
            # Получаем данные выбранного устройства
            device = self.device_manager.current_device
            # Используем полученные данные
            Logger.info(f"Выбрано устройство: {device['name']} v{device['version']}")
            Logger.info(f"Путь к документации: {device['path_to_ru_desc']}")
            # Пример работы со списком ФБС

            Logger.info(f"Обработка ФБС: {device['fbs_list']}")

            # Инициализация класса
            self.re_ = ExploitationGuideLatex(
                path_to_latex_desc=device['path_to_latex_desc'],
                path_to_fsu=self.device_manager.get_general_settings()['path_to_fsu'],
                fbs_list=device['fbs_list'],
                path_to_ru_desc = device['path_to_ru_desc'],
                path_to_hardware_desc = device['path_to_hardware_desc'])
            # Установка дополнительных путей
            #self.re_.set_path_to_hardware_desc(device['path_to_hardware_desc'])
            #self.re_.set_path_to_ru_desc(device['path_to_ru_desc'])
            Logger.info(f"Устройство: {device['name']} v{device['version']} инициализировано")

    def run(self):
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()