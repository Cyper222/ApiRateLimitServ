import json
import logging
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in {"msg", "args", "levelname", "levelno", "pathname", "filename", "module",
                       "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                       "created", "msecs", "relativeCreated", "thread", "threadName",
                       "processName", "process", "name"}:
                continue
            base[key] = value
        return json.dumps(base, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())





