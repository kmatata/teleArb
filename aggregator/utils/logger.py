import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from get_env_vars import load_environment_variables
import pytz
import threading

load_environment_variables()


LOG_DIR = os.getenv("MONITOR_LOGDIR")
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1 MB
BACKUP_COUNT = 18
MAX_LOG_AGE_HOURS = 2
eat_tz = pytz.timezone("Africa/Nairobi")
now = datetime.now(eat_tz)


class Logger:
    _instance = None
    _loggers = {}
    _lock = threading.Lock()

    def __init__(self, name):
        with self._lock:
            if name not in self._loggers:
                self.logger = logging.getLogger(name)
                self.logger.propagate = False  # Prevent double logging
                self.setup_logging()
                self._loggers[name] = self.logger
            else:
                self.logger = self._loggers[name]

    def setup_logging(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        # Only add handlers if none exist
        if not self.logger.handlers:
            log_file = os.path.join(
                LOG_DIR, f"{self.logger.name}_{now.strftime('%Y-%m-%d')}.log"
            )
            file_handler = RotatingFileHandler(
                log_file, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT
            )
            console_handler = logging.StreamHandler()

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(f"\n{message}\n")

    def info(self, message):
        self.logger.info(f"\n{message}\n")

    def warning(self, message):
        self.logger.warning(f"\n{message}\n")

    def error(self, message, exc_info=False):
        self.logger.error(f"\n{message}\n", exc_info=exc_info)

    def critical(self, message, exc_info=True):
        self.logger.critical(f"\n{message}\n", exc_info=exc_info)

    @staticmethod
    def clear_old_logs():
        current_time = datetime.now()
        for filename in os.listdir(LOG_DIR):
            file_path = os.path.join(LOG_DIR, filename)
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if current_time - file_modified > timedelta(hours=MAX_LOG_AGE_HOURS):
                print("removing old logs")
                os.remove(file_path)
