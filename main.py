"""Точка входа приложения Omni for M500."""

import traceback

from Application import Application
from logger.logger import Logger


def main():
    try:
        app = Application()
        app.run()
    except Exception as error:
        # Сообщение попадёт в logs/app.log даже если GUI не поднялся
        Logger.error(f"Критическая ошибка запуска: {error}")
        Logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
