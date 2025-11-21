import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import gzip
import shutil

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(name=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # === Консольный вывод ===
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # === файловый вывод с ротацией и gzip ===
    log_file = LOG_DIR / "bot.log"

    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
        utc=False,
    )
    file_handler.setFormatter(formatter)

    # === gzip архивирование старых логов ===
    def namer(default_name):
        return default_name + ".gz"

    def rotator(source, dest):
        with open(source, "rb") as f_in:
            with gzip.open(dest, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)

    file_handler.namer = namer
    file_handler.rotator = rotator

    logger.addHandler(file_handler)
    return logger
