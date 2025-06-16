import os
import time
import threading

import dearpygui.dearpygui as dpg
import themes

# Класс Logger для демонстрации
class Logger:
    COLORS = {
        "INFO": (100, 200, 255),
        "WARNING": (255, 255, 100),
        "ERROR": (255, 100, 100)
    }
    
    visible_levels = {
        "INFO": True,
        "WARNING": True,
        "ERROR": True
    }
    
    log_container = None
    log_window = None
    
    @classmethod
    def set_container(cls, container_tag, window_tag):
        cls.log_container = container_tag
        cls.log_window = window_tag
    
    @classmethod
    def info(cls, message):
        cls._add_log("INFO", message)
    
    @classmethod
    def warning(cls, message):
        cls._add_log("WARNING", message)
    
    @classmethod
    def error(cls, message):
        cls._add_log("ERROR", message)
    
    @classmethod
    def _add_log(cls, level, message):
        if cls.visible_levels.get(level, True):
            timestamp = time.strftime("%H:%M:%S")
            with dpg.group(parent=cls.log_container):
                with dpg.group(horizontal=True):
                    with dpg.drawlist(width=15, height=15):
                        dpg.draw_rectangle((0, 0), (15, 15), fill=cls.COLORS[level], rounding=2)
                    dpg.add_text(f"[{timestamp}] [{level}] {message}")
    
    @classmethod
    def refresh_display(cls):
        dpg.delete_item(cls.log_container, children_only=True)
    
    @classmethod
    def set_search_filter(cls, text):
        pass  # Реализуйте поиск при необходимости
    
    @classmethod
    def clear_logs(cls):
        dpg.delete_item(cls.log_container, children_only=True)
    
    @classmethod
    def save_logs_to_file(cls):
        pass  # Реализуйте сохранение в файл при необходимости


# Создаем окно
dpg.create_context()

# Подключаем светлую тему
light_theme = themes.create_theme_imgui_light()
dpg.bind_theme(light_theme)

with dpg.font_registry():
    with dpg.font("Roboto-Regular.ttf", 15, default_font=True, tag="Default font") as f:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
    
dpg.bind_font("Default font")

# Функции задач
def background_task():
    Logger.info("Задача началась")
    helper_function()
    error_function()
    Logger.info("Задача завершена")

def button_callback():
    threading.Thread(target=background_task, daemon=True).start()

def helper_function():
    Logger.info("Вызвана helper_function()")
    Logger.warning("Предупреждаю!")

def error_function():
    Logger.error("Произошла ошибка!")

# Функции GUI
def toggle_level(sender, app_data, user_data):
    Logger.visible_levels[user_data] = app_data
    Logger.refresh_display()

def on_search_input(sender):
    search_text = dpg.get_value(sender)
    Logger.set_search_filter(search_text)

def clear_logs():
    Logger.clear_logs()

def save_logs():
    Logger.save_logs_to_file()

# Создание GUI
with dpg.window(label="Главное окно", width=400, height=250):
    dpg.add_button(label="Запустить задачу", callback=button_callback)
    dpg.add_button(label="Очистить логи", callback=clear_logs)
    dpg.add_button(label="Сохранить логи", callback=save_logs)

    dpg.add_separator()
    dpg.add_text("Фильтры:")

    # INFO строка
    with dpg.group(horizontal=True):
        dpg.add_checkbox(label="INFO", default_value=True, callback=toggle_level, user_data="INFO")
        with dpg.drawlist(width=15, height=15):
            dpg.draw_rectangle((0, 0), (15, 15), fill=Logger.COLORS["INFO"], rounding=2)

    # WARNING строка
    with dpg.group(horizontal=True):
        dpg.add_checkbox(label="WARNING", default_value=True, callback=toggle_level, user_data="WARNING")
        with dpg.drawlist(width=15, height=15):
            dpg.draw_rectangle((0, 0), (15, 15), fill=Logger.COLORS["WARNING"], rounding=2)

    # ERROR строка
    with dpg.group(horizontal=True):
        dpg.add_checkbox(label="ERROR", default_value=True, callback=toggle_level, user_data="ERROR")
        with dpg.drawlist(width=15, height=15):
            dpg.draw_rectangle((0, 0), (15, 15), fill=Logger.COLORS["ERROR"], rounding=2)

    dpg.add_separator()
    dpg.add_input_text(label="Поиск по логам", callback=on_search_input)

with dpg.window(label="Логи", width=600, height=300, pos=[400, 0]):
    with dpg.child_window(tag="log_window", height=250):
        dpg.add_group(tag="log_container")

# Настройка Logger после создания всех элементов
Logger.set_container("log_container", "log_window")

# Создание и отображение viewport
dpg.create_viewport(title="Логгер", width=1000, height=400)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()