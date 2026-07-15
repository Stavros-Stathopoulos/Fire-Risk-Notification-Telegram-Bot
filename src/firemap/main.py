"""Long-running entrypoint for Docker.

Once a day (at config.DAILY_RUN_AT local time) it fetches tomorrow's
fire-risk map and sends it to Telegram. If the map is not published yet,
it retries a few times before giving up until the next day.

Every action is also appended to LOG_DIR/actions.jsonl, see logging_setup.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta

import requests

from firemap import config
from firemap.fetch import cleanup_old_maps, fetch_daily_image, tomorrow
from firemap.logging_setup import setup_logging
from firemap.notifier import TelegramNotifier

log = logging.getLogger("firemap")


def startup_check() -> None:
    """Exercise the whole pipeline immediately on startup.

    In a fresh environment this proves credentials, network access and the
    Telegram chat work without waiting for the next scheduled cycle: it sends
    a status message and tries to fetch and deliver the current map (today's,
    falling back to tomorrow's if it is already published). Failures are
    reported but never crash the app — the scheduled cycle will retry.
    """
    log.info("Running startup check", extra={"action": "startup.begin"})
    try:
        notifier = TelegramNotifier()
        notifier.send_message(
            "✅ Fire-map bot started — verifying with a test fetch…"
        )
        for day in (date.today(), tomorrow()):
            try:
                path = fetch_daily_image(day)
                notifier.send_map(
                    path, caption=f"Startup check OK — fire risk map for {day}"
                )
                log.info(
                    "Startup check succeeded with map for %s",
                    day,
                    extra={"action": "startup.success", "map_date": str(day)},
                )
                return
            except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as exc:
                log.warning(
                    "Startup fetch for %s failed (%s)",
                    day,
                    exc,
                    extra={
                        "action": "startup.fetch_failed",
                        "map_date": str(day),
                        "error": str(exc),
                    },
                )
        notifier.send_message(
            "⚠️ Startup check: Telegram works, but no map is available right "
            "now. Will fetch at the scheduled time."
        )
        log.info(
            "Startup check: Telegram OK, no map available yet",
            extra={"action": "startup.partial"},
        )
    except requests.RequestException as exc:
        log.error(
            "Startup check failed: %s",
            exc,
            extra={"action": "startup.failed", "error": str(exc)},
        )


def fetch_and_send() -> None:
    notifier = TelegramNotifier()
    for attempt in range(1, config.RETRY_ATTEMPTS + 1):
        try:
            path = fetch_daily_image()
            notifier.send_map(path)
            log.info(
                "Sent %s to Telegram, sleeping until tomorrow",
                path.name,
                extra={"action": "run.success", "attempt": attempt, "file": path.name},
            )
            return
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as exc:
            log.warning(
                "Attempt %d/%d failed (%s)",
                attempt,
                config.RETRY_ATTEMPTS,
                exc,
                extra={
                    "action": "run.retry",
                    "attempt": attempt,
                    "max_attempts": config.RETRY_ATTEMPTS,
                    "error": str(exc),
                },
            )
            if attempt < config.RETRY_ATTEMPTS:
                time.sleep(config.RETRY_DELAY_MINUTES * 60)

    log.error(
        "Giving up until tomorrow: map never became available",
        extra={"action": "run.gave_up", "attempts": config.RETRY_ATTEMPTS},
    )
    try:
        notifier.send_message(
            f"⚠️ Failed to fetch the fire-risk map after "
            f"{config.RETRY_ATTEMPTS} attempts. Please try manually: "
            f"https://civilprotection.gov.gr"
        )
    except requests.RequestException as exc:
        log.error(
            "Could not send failure alert either: %s",
            exc,
            extra={"action": "run.alert_failed", "error": str(exc)},
        )


def seconds_until_next_run() -> float:
    hour, minute = (int(part) for part in config.DAILY_RUN_AT.split(":"))
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def main() -> None:
    setup_logging()
    config.validate()
    log.info(
        "Started; will run daily at %s",
        config.DAILY_RUN_AT,
        extra={"action": "app.start", "daily_run_at": config.DAILY_RUN_AT},
    )
    startup_check()
    cleanup_old_maps()
    while True:
        wait = seconds_until_next_run()
        log.info(
            "Next run in %.1f hours",
            wait / 3600,
            extra={"action": "app.sleep", "seconds": round(wait)},
        )
        time.sleep(wait)
        fetch_and_send()
        cleanup_old_maps()


if __name__ == "__main__":
    main()
