"""Fetch the daily fire-risk map from civilprotection.gov.gr.

URL pattern: https://civilprotection.gov.gr/sites/default/files/<YYYY-MM>/<YYMMDD>.jpg
e.g. for 2026-07-15 -> .../2026-07/260715.jpg

The map for a given day is published the evening before, so the default
target date is tomorrow.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import requests

from firemap import config

log = logging.getLogger("firemap.fetch")


def tomorrow() -> date:
    return date.today() + timedelta(days=1)


def build_url(day: date) -> str:
    """Build the image URL for the given date."""
    return f"{config.BASE_URL}/{day:%Y-%m}/{day:%y%m%d}.jpg"


def fetch_daily_image(day: date | None = None) -> Path:
    """Download the map for the given date (defaults to tomorrow).

    The file is saved in config.DATA_DIR as YYYY-MM-DD.jpg and its path is
    returned. Raises requests.HTTPError if the image is not (yet) published.
    """
    day = day or tomorrow()
    url = build_url(day)

    log.info(
        "Fetching fire-risk map for %s",
        day,
        extra={"action": "fetch.start", "target_date": str(day), "url": url},
    )
    response = requests.get(
        url,
        headers={"User-Agent": config.USER_AGENT},
        timeout=config.REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.DATA_DIR / f"{day:%Y-%m-%d}.jpg"
    dest.write_bytes(response.content)
    log.info(
        "Saved map to %s",
        dest,
        extra={
            "action": "fetch.saved",
            "target_date": str(day),
            "url": url,
            "file": str(dest),
            "bytes": len(response.content),
            "status_code": response.status_code,
        },
    )
    return dest


def cleanup_old_maps() -> None:
    """Delete maps whose date (the YYYY-MM-DD filename) is older than
    config.MAP_RETENTION_DAYS days."""
    cutoff = date.today() - timedelta(days=config.MAP_RETENTION_DAYS)
    for path in sorted(config.DATA_DIR.glob("*.jpg")):
        try:
            day = date.fromisoformat(path.stem)
        except ValueError:
            continue  # not one of our maps, leave it alone
        if day < cutoff:
            path.unlink()
            log.info(
                "Deleted old map %s",
                path.name,
                extra={
                    "action": "cleanup.deleted",
                    "file": str(path),
                    "map_date": str(day),
                    "retention_days": config.MAP_RETENTION_DAYS,
                },
            )


if __name__ == "__main__":  # run with: python -m firemap.fetch
    try:
        path = fetch_daily_image()
        print(f"Saved {path}")
    except requests.HTTPError as exc:
        print(f"Image not available yet: {exc}")
