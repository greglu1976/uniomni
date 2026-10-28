"""Логгер приложения: вывод в окно GUI и в файл logs/app.log.

Файловое логирование работает независимо от GUI, поэтому приложение
(и отдельные модули) можно использовать из скриптов и тестов.
"""

import time

import dearpygui.dearpygui as dpg

from utils.paths import project_path

LOG_FILE = project_path("logs", "app.log")


class Logger:
    TEXT_COLORS = {
        "INFO": (80, 80, 80, 255),
        "WARNING": (255, 102, 0, 255),
        "ERROR": (255, 0, 0, 255),
    }

    visible_levels = {
        "INFO": True,
        "WARNING": True,
        "ERROR": True,
    }

    log_container = None      # группа, в которую добавляются строки
    log_scroll_container = None  # child_window для прокрутки

    # Dear PyGui нельзя трогать до создания контекста: вызов add_text без
    # контекста не бросает исключение, а роняет процесс (segfault).
    gui_enabled = False

    @classmethod
    def set_container(cls, container_tag, scroll_container_tag=None):
        cls.log_container = container_tag
        cls.log_scroll_container = scroll_container_tag
        cls.gui_enabled = True

    @classmethod
    def disable_gui(cls):
        """Отключает вывод в GUI (например, перед destroy_context)."""
        cls.gui_enabled = False

    # ------------------------------------------------------------- уровни

    @classmethod
    def info(cls, message):
        cls._add_log("INFO", message)

    @classmethod
    def warning(cls, message):
        cls._add_log("WARNING", message)

    @classmethod
    def error(cls, message):
        cls._add_log("ERROR", message)

    # ---------------------------------------------------------- внутреннее

    @classmethod
    def _add_log(cls, level, message):
        message = str(message)
        cls._write_to_file(level, message)

        if not cls.gui_enabled or not cls.visible_levels.get(level, True):
            return

        try:
            dpg.add_text(
                f"[{time.strftime('%H:%M:%S')}] [{level}] {message}",
                color=cls.TEXT_COLORS[level],
                parent=cls.log_container,
            )
            if cls.log_scroll_container:
                dpg.set_y_scroll(cls.log_scroll_container, -1.0)
        except Exception:
            # GUI ещё не создан (или уже закрыт) — сообщение осталось в файле
            pass

    @classmethod
    def _write_to_file(cls, level, message):
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as file:
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n")
        except OSError:
            # Логирование не должно ронять приложение
            pass

    # ------------------------------------------------------------ действия

    @classmethod
    def clear_logs(cls):
        """Очищает окно логов и файл лога."""
        if cls.gui_enabled:
            try:
                if cls.log_container and dpg.does_item_exist(cls.log_container):
                    dpg.delete_item(cls.log_container, children_only=True)
            except Exception:
                pass

        try:
            if LOG_FILE.exists():
                LOG_FILE.write_text("", encoding="utf-8")
        except OSError:
            pass
