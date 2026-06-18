"""Logging estruturado para o backend FastAPI."""

from __future__ import annotations

import json
import logging
from logging import LogRecord
from logging.handlers import RotatingFileHandler
from typing import Any

import config


_RESERVED_LOG_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class JsonFormatter(logging.Formatter):
    """Formatter JSON simples, sem dependencia externa."""

    def format(self, record: LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    """Configura console JSON e arquivo rotativo opcional."""

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if config.LOG_TO_FILE:
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                config.LOG_FILE,
                maxBytes=config.LOG_MAX_BYTES,
                backupCount=config.LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
        )

    formatter = JsonFormatter()
    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=config.LOG_LEVEL,
        handlers=handlers,
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(config.LOG_LEVEL)
    logging.getLogger("uvicorn.error").setLevel(config.LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    """Retorna logger nomeado; helper para padronizar imports."""

    return logging.getLogger(name)
