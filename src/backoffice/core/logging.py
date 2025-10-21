from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from .context import request_id_ctx_var, user_id_ctx_var

_LOGGERS_INITIALIZED: bool = False


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        # Ensure standard keys are present
        if "level" not in log_record:
            log_record["level"] = record.levelname
        if "logger" not in log_record:
            log_record["logger"] = record.name
        if "message" not in log_record:
            log_record["message"] = record.getMessage()
        # Useful extras from record if present
        for key in ("request_id", "user_id", "path", "method"):
            value = getattr(record, key, None)
            if value is not None:
                log_record[key] = value


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    global _LOGGERS_INITIALIZED
    if _LOGGERS_INITIALIZED:
        return

    root = logging.getLogger()
    root.setLevel(level.upper())

    # Remove default handlers (e.g., added by uvicorn)
    for h in list(root.handlers):
        root.removeHandler(h)

    stream_handler = logging.StreamHandler(sys.stdout)

    if fmt.lower() == "json":
        formatter = JsonFormatter("%(asctime)s %(level)s %(name)s %(message)s")
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )

    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(ContextVarsFilter())
    root.addHandler(stream_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(level.upper())
    logging.getLogger("uvicorn.access").setLevel(level.upper())
    logging.getLogger("uvicorn.error").setLevel(level.upper())
    logging.getLogger("aiokafka").setLevel(level.upper())
    logging.getLogger("botocore").setLevel("WARNING")

    _LOGGERS_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class ContextVarsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        # Inject contextvars into every record
        try:
            record.request_id = request_id_ctx_var.get()
        except Exception:
            record.request_id = "-"
        try:
            record.user_id = user_id_ctx_var.get()
        except Exception:
            record.user_id = "-"
        return True
