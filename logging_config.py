import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict


_RESERVED_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class JsonFormatter(logging.Formatter):
    """
    Simple JSON formatter for structured logs.

    Keeps the default timestamp formatting from logging.Formatter
    and encodes record data as JSON for downstream aggregation.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "message": record.getMessage(),
            "logger": record.name,
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_KEYS or key.startswith("_"):
                continue
            log_record[key] = value

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack"] = record.stack_info

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(app) -> None:
    """
    Configure structured logging for the given Flask app.

    Logs are written both to STDOUT and to a rotating file handler.
    """

    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    log_dir = app.config.get("LOG_DIR")
    max_bytes = int(app.config.get("LOG_MAX_BYTES", 5 * 1024 * 1024))
    backup_count = int(app.config.get("LOG_BACKUP_COUNT", 5))

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    formatter = JsonFormatter()

    handlers = []

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)
    handlers.append(stream_handler)

    if log_dir:
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"), maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)

    app.logger.handlers = []
    app.logger.setLevel(log_level)

    for handler in handlers:
        app.logger.addHandler(handler)

    # Keep Werkzeug quieter in production environments
    werkzeug_level = logging.WARNING if app.config["IS_PRODUCTION"] else logging.INFO
    logging.getLogger("werkzeug").setLevel(werkzeug_level)

