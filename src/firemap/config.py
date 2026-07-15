"""Central configuration.

Non-secret values have sane defaults and can be overridden via environment
variables. Secrets (Telegram credentials) MUST come from the environment —
never commit them. For local development put them in a .env file (git-ignored,
see .env.example); Docker Compose loads it automatically.
"""

import os
from pathlib import Path

# The package is installed (src layout), so paths can't be derived from
# __file__. Everything resolves against the working directory — the project
# root locally, /app in Docker — and can be overridden via environment.
WORK_DIR = Path.cwd()


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from .env in the working directory, if present.

    Real environment variables take precedence, so Docker/CI overrides work.
    """
    env_file = WORK_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.split("#")[0].strip().strip("'\""))


_load_dotenv()

# --- Fetching ---------------------------------------------------------------
BASE_URL = os.environ.get(
    "BASE_URL", "https://civilprotection.gov.gr/sites/default/files"
)

# Some government sites reject requests without a browser-like User-Agent.
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
)

REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))  # seconds

# --- Storage ----------------------------------------------------------------
# Folder where downloaded maps are saved (created automatically if missing).
# In Docker this is a mounted volume, see docker-compose.yml.
DATA_DIR = Path(os.environ.get("DATA_DIR", WORK_DIR / "data"))
# Downloaded maps older than this (by the date in the filename) are deleted.
MAP_RETENTION_DAYS = int(os.environ.get("MAP_RETENTION_DAYS", "30"))

# --- Logging ------------------------------------------------------------------
# Folder for the JSONL action log (actions.jsonl, rotated daily).
LOG_DIR = Path(os.environ.get("LOG_DIR", WORK_DIR / "logs"))
# Days of JSONL history to keep; older files are deleted on rotation.
LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "7"))

# --- Telegram (secrets — environment only) -----------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# One or more recipient chat ids, comma-separated: "123456789,987654321"
TELEGRAM_CHAT_IDS = [
    chat_id.strip()
    for chat_id in os.environ.get("TELEGRAM_CHAT_ID", "").split(",")
    if chat_id.strip()
]

# --- Scheduling -------------------------------------------------------------
# Local time (HH:MM) at which main.py fetches and sends tomorrow's map.
DAILY_RUN_AT = os.environ.get("DAILY_RUN_AT", "12:05")
# If the map is not published yet, retry this many times, this far apart.
RETRY_ATTEMPTS = int(os.environ.get("RETRY_ATTEMPTS", "15"))
RETRY_DELAY_MINUTES = int(os.environ.get("RETRY_DELAY_MINUTES", "10"))


def validate() -> None:
    """Fail fast with a clear message if secrets are missing."""
    missing = [
        name
        for name, value in {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_IDS,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )
