"""Long-running entrypoint for Docker.

Once a day (at config.DAILY_RUN_AT local time) it fetches tomorrow's
fire-risk map and sends it to Telegram. If the map is not published yet,
it retries a few times before giving up until the next day.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

import requests

import config
from fetch import fetch_daily_image
from notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("firemap")


def fetch_and_send() -> None:
    notifier = TelegramNotifier()
    for attempt in range(1, config.RETRY_ATTEMPTS + 1):
        try:
            path = fetch_daily_image()
            notifier.send_map(path)
            log.info("Sent %s to Telegram, sleeping until tomorrow", path.name)
            return
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as exc:
            log.warning(
                "Attempt %d/%d failed (%s)", attempt, config.RETRY_ATTEMPTS, exc
            )
            if attempt < config.RETRY_ATTEMPTS:
                time.sleep(config.RETRY_DELAY_MINUTES * 60)

    log.error("Giving up until tomorrow: map never became available")
    try:
        notifier.send_message(
            f"⚠️ Failed to fetch the fire-risk map after "
            f"{config.RETRY_ATTEMPTS} attempts. Please try manually: "
            f"https://civilprotection.gov.gr"
        )
    except requests.RequestException as exc:
        log.error("Could not send failure alert either: %s", exc)


def seconds_until_next_run() -> float:
    hour, minute = (int(part) for part in config.DAILY_RUN_AT.split(":"))
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def main() -> None:
    config.validate()
    log.info("Started; will run daily at %s", config.DAILY_RUN_AT)
    while True:
        wait = seconds_until_next_run()
        log.info("Next run in %.1f hours", wait / 3600)
        time.sleep(wait)
        fetch_and_send()


if __name__ == "__main__":
    main()
