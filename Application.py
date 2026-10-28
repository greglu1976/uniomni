"""Приложение Omni for M500: графический интерфейс (Dear PyGui)."""

import traceback
from pathlib import Path

import dearpygui.dearpygui as dpg

import gui.themes as themes
from core.DeviceDataManager import DeviceDataManager
from core.LatexDoc import LatexDoc
from core.Manual2 import Manual
from core.SettingBlanc2 import SettingBlanc
from logger.logger import Logger
from utils.additional import create_directories

WINDOW_TITLE = "Omni for M500 v0.0.4 28.10.26"

LOG_SCROLL_TAG = "log_container"
LOG_CONTENT_TAG = "log_content"


class Application:
    def __init__(self):
        self.device_data = None

        self.device_data_manager = DeviceDataManager()
        self.devices_data = self.device_data_manager.get_all_devices()

        # Строки для выпадающего списка устройств
        self.display_names = [
            f"Устройство: {device['name']}, Версия: {device['version']}"
            for device in self.devices_data
        ]

        self.setup_gui()
        self.load_config_callback()

    # --------------------------------------------------------------- GUI

    def setup_gui(self):
        dpg.create_context()

        light_theme = themes.create_theme_imgui_light()
        dpg.bind_theme(light_theme)

        with dpg.font_registry():
            default_font = dpg.add_font("gui/Montserrat-Regular.ttf", 15)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=default_font)
        dpg.bind_font(default_font)

        # Главное окно
        with dpg.window(label="Главное окно", width=400, height=400, pos=[20, 20]):
            self.device_combo = dpg.add_combo(
                label="Устройство",
                items=[],
                width=300,
                enabled=False,
            )
            dpg.add_spacer(height=5)

            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="Создать бланк уставок в docx",
                           callback=self.generate_setting_blanc_docx, width=300)
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="Обновить таблицы с уставками в РЭ",
                           callback=self.renew_setting_tables_re, width=300)
            dpg.add_button(label="Обновить таблицу сигналов в РЭ",
                           callback=self.renew_sum_table_latex, width=300)
            dpg.add_button(label="Обновить перечень сокращений в РЭ",
                           callback=self.renew_abbrs, width=300)
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="Обновить перечень сокращений в РУ",
                           callback=self.renew_abbrs_ru, width=300)
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="Очистить логи", callback=Logger.clear_logs, width=300)
            dpg.add_button(label="Перезагрузить config.ini",
                           callback=self.load_config_callback, width=300)
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="Собрать в один файл latex (raw.tex)",
                           callback=self.gen_raw_latex, width=300)

        # Окно логов
        log_window_height = 450
        with dpg.window(label="Логи", width=900, height=log_window_height,
                        pos=[430, 20], tag="log_window"):
            with dpg.child_window(tag=LOG_SCROLL_TAG, height=log_window_height - 35):
                dpg.add_group(tag=LOG_CONTENT_TAG)

        Logger.set_container(LOG_CONTENT_TAG, LOG_SCROLL_TAG)

        dpg.create_viewport(title=WINDOW_TITLE, width=1400, height=550)
        dpg.setup_dearpygui()

    # ------------------------------------------------------------ задачи

    @staticmethod
    def _safe(task):
        """Выполняет задачу, не выпуская исключение в callback Dear PyGui."""
        try:
            task()
        except Exception as error:
            Logger.error(f"Ошибка выполнения задачи: {error}")
            Logger.error(traceback.format_exc())

    def _require_device(self):
        """Проверяет, что устройство выбрано, и загружает его данные."""
        selected_text = dpg.get_value(self.device_combo)
        if not selected_text:
            Logger.error("Устройство не выбрано")
            return False

        display_to_device_map = {
            f"Устройство: {device['name']}, Версия: {device['version']}": device
            for device in self.devices_data
        }
        device = display_to_device_map.get(selected_text)
        if device is None:
            Logger.error("Выбранное устройство не найдено в конфигурации")
            return False

        self.device_data = self.device_data_manager.get_device_by_name_and_version(
            name=device['name'], version=device['version'])
        if not self.device_data:
            Logger.error(f"Не удалось получить данные для устройства "
                         f"{device['name']} v{device['version']}")
            return False

        Logger.info(f"Выбрано устройство: {device['name']} v{device['version']}")
        return True

    # --------------------------------------------------------- обработчики

    def generate_setting_blanc_docx(self):
        if not self._require_device():
            return
        self._safe(self._task_setting_blanc_docx)

    def _task_setting_blanc_docx(self):
        Logger.info('Начинаем создавать бланк уставок...')
        SettingBlanc(self.device_data).get_blanc()

    def renew_setting_tables_re(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_setting_tables_re)

    def _task_renew_setting_tables_re(self):
        Logger.info('Обновляем таблицы с уставками в РЭ...')
        Manual(device_data=self.device_data).renew_setting_tables_re()
        Logger.info('Таблицы с уставками в РЭ обновлены')

    def renew_sum_table_latex(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_sum_table_latex)

    def _task_renew_sum_table_latex(self):
        Logger.info('Обновляем таблицу сигналов в РЭ...')
        Manual(device_data=self.device_data).renew_sum_table_latex()
        Logger.info('Таблица сигналов в РЭ обновлена')

    def renew_abbrs(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_abbrs)

    def _task_renew_abbrs(self):
        result = Manual(device_data=self.device_data).renew_abbrs()
        if result in (None, 'ok', 'noabbrs'):
            Logger.info('Перечень сокращений в РЭ обновлен')
        else:
            Logger.error('При обновлении перечня сокращений РЭ возникли ошибки')

    def renew_abbrs_ru(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_abbrs_ru)

    def _task_renew_abbrs_ru(self):
        result = Manual(device_data=self.device_data).renew_abbrs_ru()
        if result == 0:
            Logger.info('Перечень сокращений в РУ обновлен')
        else:
            Logger.error('При обновлении перечня сокращений РУ возникли ошибки')

    def gen_raw_latex(self):
        if not self._require_device():
            return
        self._safe(self._task_gen_raw_latex)

    def _task_gen_raw_latex(self):
        Logger.info('Пытаемся создать единый файл latex')
        if not create_directories():
            Logger.error('Не удалось подготовить каталог сборки latex')
            return

        path_to_latex_desc = (self.device_data.get("path_to_latex_desc") or '').strip()
        if not path_to_latex_desc:
            Logger.error('В конфигурации устройства не задан path_to_latex_desc')
            return

        LatexDoc(Path(path_to_latex_desc) / '_manual_latex')
        Logger.info('Проект latex для РЭ создан. См. папку latex_build')

    # ------------------------------------------------------- конфигурация

    def load_config_callback(self):
        """Обработчик перечитывания devices.ini."""
        try:
            self.devices_data = self.device_data_manager.get_all_devices()
            self.display_names = [
                f"Устройство: {device['name']}, Версия: {device['version']}"
                for device in self.devices_data
            ]
        except Exception as error:
            Logger.error(f"Ошибка загрузки конфигурации: {error}")
            return

        if self.display_names:
            dpg.configure_item(self.device_combo, items=self.display_names, enabled=True)
            Logger.info("Конфигурация загружена успешно")
        else:
            Logger.warning("Устройства не найдены в конфигурации")

    # ----------------------------------------------------------- запуск

    def run(self):
        dpg.show_viewport()
        dpg.start_dearpygui()
        Logger.disable_gui()
        dpg.destroy_context()
