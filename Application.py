"""Приложение Omni for M500: графический интерфейс (Dear PyGui)."""

import traceback
from pathlib import Path

import dearpygui.dearpygui as dpg

import gui.themes as themes
from core.DeviceDataManager import DeviceDataManager
from core.LatexDoc import LatexDoc
from core.Manual2 import Manual
from core.SettingBlanc2 import SettingBlanc
from core.UnitConverter import (
    DEFAULT_TIME_UNIT,
    DEFAULT_UNIT_TYPE,
    TIME_UNIT_CHOICES,
    TIME_UNIT_TITLES,
    UNIT_TYPE_TITLES,
)
from logger.logger import Logger
from utils.additional import create_directories

WINDOW_TITLE = "Omni for M500 v0.0.4 28.10.26 deepseek edition"

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
        with dpg.window(label="Главное окно", width=400, height=545, pos=[20, 20]):
            self.device_combo = dpg.add_combo(
                label="Устройство",
                items=[],
                width=300,
                enabled=False,
            )
            dpg.add_spacer(height=5)

            dpg.add_separator()
            dpg.add_spacer(height=5)

            dpg.add_text("Единицы уставок")
            self.unit_combo = dpg.add_combo(
                items=list(UNIT_TYPE_TITLES.values()),
                default_value=UNIT_TYPE_TITLES[DEFAULT_UNIT_TYPE],
                width=300,
            )
            dpg.add_spacer(height=5)

            dpg.add_text("Единицы времени")
            self.time_combo = dpg.add_combo(
                items=[TIME_UNIT_TITLES.get(unit, unit) for unit in TIME_UNIT_CHOICES],
                default_value=TIME_UNIT_TITLES.get(DEFAULT_TIME_UNIT, DEFAULT_TIME_UNIT),
                width=300,
            )
            dpg.add_spacer(height=5)

            self.step_checkbox = dpg.add_checkbox(
                label="Преобразовывать Шаг",
                default_value=True,
            )
            self.fsu_checkbox = dpg.add_checkbox(
                label="Генерировать из fsu-information",
                default_value=True,
            )
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

        dpg.create_viewport(title=WINDOW_TITLE, width=1400, height=620)
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

    def _selected_unit_type(self):
        """Выбранная в интерфейсе система единиц уставок."""
        title = dpg.get_value(self.unit_combo)
        for unit_type, unit_title in UNIT_TYPE_TITLES.items():
            if unit_title == title:
                return unit_type
        return DEFAULT_UNIT_TYPE

    def _selected_time_unit(self):
        """Выбранные в интерфейсе единицы времени (в списке показывается «с»)."""
        title = dpg.get_value(self.time_combo)
        for unit, unit_title in TIME_UNIT_TITLES.items():
            if unit_title == title:
                return unit
        return DEFAULT_TIME_UNIT

    def _convert_step(self):
        """Нужно ли пересчитывать шаг уставки коэффициентом."""
        return bool(dpg.get_value(self.step_checkbox))

    def _use_fsu(self):
        """Брать ли уставки из fsu-information.json (иначе — из GROUPING/meta)."""
        return bool(dpg.get_value(self.fsu_checkbox))

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
        unit_type = self._selected_unit_type()
        time_unit = self._selected_time_unit()
        source = ('fsu-information (значения и шаг как в файле, в о.е.)'
                  if self._use_fsu() else
                  f'GROUPING/meta ({UNIT_TYPE_TITLES[unit_type]}, время: {time_unit})')
        Logger.info(f"Начинаем создавать бланк уставок — источник: {source}...")
        SettingBlanc(self.device_data, unit_type=unit_type,
                     time_unit=time_unit,
                     convert_step=self._convert_step(),
                     use_fsu=self._use_fsu()).get_blanc()

    def renew_setting_tables_re(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_setting_tables_re)

    def _task_renew_setting_tables_re(self):
        Logger.info(f"Обновляем таблицы с уставками в РЭ "
                    f"({UNIT_TYPE_TITLES[self._selected_unit_type()]}, "
                    f"время: {self._selected_time_unit()}, "
                    f"шаг преобразуется: {'да' if self._convert_step() else 'нет'}, "
                    f"источник: {'fsu-information' if self._use_fsu() else 'GROUPING/meta'})...")
        Manual(device_data=self.device_data,
               unit_type=self._selected_unit_type(),
               time_unit=self._selected_time_unit(),
               convert_step=self._convert_step(),
               use_fsu=self._use_fsu()).renew_setting_tables_re()
        Logger.info('Таблицы с уставками в РЭ обновлены')

    def renew_sum_table_latex(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_sum_table_latex)

    def _task_renew_sum_table_latex(self):
        Logger.info('Обновляем таблицу сигналов в РЭ...')
        Manual(device_data=self.device_data,
               unit_type=self._selected_unit_type(),
               time_unit=self._selected_time_unit(),
               convert_step=self._convert_step(),
               use_fsu=self._use_fsu()).renew_sum_table_latex()
        Logger.info('Таблица сигналов в РЭ обновлена')

    def renew_abbrs(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_abbrs)

    def _task_renew_abbrs(self):
        result = Manual(device_data=self.device_data,
                        unit_type=self._selected_unit_type(),
                        time_unit=self._selected_time_unit(),
               convert_step=self._convert_step()).renew_abbrs()
        if result in (None, 'ok', 'noabbrs'):
            Logger.info('Перечень сокращений в РЭ обновлен')
        else:
            Logger.error('При обновлении перечня сокращений РЭ возникли ошибки')

    def renew_abbrs_ru(self):
        if not self._require_device():
            return
        self._safe(self._task_renew_abbrs_ru)

    def _task_renew_abbrs_ru(self):
        result = Manual(device_data=self.device_data,
                        unit_type=self._selected_unit_type(),
                        time_unit=self._selected_time_unit(),
               convert_step=self._convert_step()).renew_abbrs_ru()
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
