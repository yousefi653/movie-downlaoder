import logging
import logging.handlers
import os
import sys

_CONFIGURED = False

CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FILE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%H:%M:%S"

_QUIET_LOGGERS = ("pymongo", "urllib3", "requests", "simple_useragent.core", "simple_header.core")


def setup_logging(level=None, log_file="logs/app.log", quiet=False):
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = (
        level
        or os.getenv("LOG_LEVEL", "INFO")
        or "INFO"
    ).upper()
    numeric_level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(min(numeric_level, logging.DEBUG))
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.CRITICAL if quiet else numeric_level)
    console.setFormatter(logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(console)

    try:
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(file_handler)
    except OSError as exc:
        root.warning("Could not attach file log handler (%s): %s", log_file, exc)

    for name in _QUIET_LOGGERS:
        logging.getLogger(name).disabled = True

    _CONFIGURED = True
    logging.getLogger(__name__).debug(
        "Logging configured (console=%s, file=%s)", level_name, log_file
    )
