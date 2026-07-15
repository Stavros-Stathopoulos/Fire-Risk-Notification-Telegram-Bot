"""Structured JSONL action logging.

Every log record is appended as one JSON object per line to
LOG_DIR/actions.jsonl. The file rotates at midnight; one week of history
is kept (actions.jsonl.YYYY-MM-DD), after which the oldest day is deleted
so storage use stays bounded.

Modules attach machine-readable context via the standard `extra` kwarg:

    log.info("Saved map", extra={"action": "fetch.saved", "path": str(dest)})

Those extra fields end up as top-level keys in the JSON object.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

from firemap import config

# Attributes present on every LogRecord — anything else was passed via `extra`
# and should be emitted as a structured field.
_STANDARD_ATTRS = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime", "taskName"}


class JsonlFormatter(logging.Formatter):
    """Format a LogRecord as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                entry[key] = value
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def setup_logging() -> None:
    """Log human-readable lines to stderr and JSONL to LOG_DIR/actions.jsonl."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    root.addHandler(console)

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    jsonl = TimedRotatingFileHandler(
        config.LOG_DIR / "actions.jsonl",
        when="midnight",
        backupCount=config.LOG_RETENTION_DAYS - 1,  # current file + backups = a week
        encoding="utf-8",
    )
    jsonl.setFormatter(JsonlFormatter())
    root.addHandler(jsonl)
