"""Send a fetched fire-risk map as a private Telegram message.

Setup (one time):
1. Talk to @BotFather on Telegram, send /newbot and copy the token
   into TELEGRAM_BOT_TOKEN in your .env file.
2. Send any message to your new bot, open
   https://api.telegram.org/bot<TOKEN>/getUpdates
   and copy the chat id into TELEGRAM_CHAT_ID in .env.
"""

from __future__ import annotations

from pathlib import Path

import requests

import config


class TelegramNotifier:
    """Sends images to one or more private Telegram chats via the Bot API."""

    def __init__(
        self,
        bot_token: str = config.TELEGRAM_BOT_TOKEN,
        chat_ids: list[str] = config.TELEGRAM_CHAT_IDS,
    ) -> None:
        if not bot_token or not chat_ids:
            raise RuntimeError(
                "Telegram credentials missing: set TELEGRAM_BOT_TOKEN and "
                "TELEGRAM_CHAT_ID in the environment (see .env.example)."
            )
        self.chat_ids = chat_ids
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str) -> None:
        """Send a plain text message to every configured chat."""
        for chat_id in self.chat_ids:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                data={"chat_id": chat_id, "text": text},
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()

    def send_map(self, image_path: str | Path, caption: str | None = None) -> None:
        """Send the image at image_path as a photo to every configured chat."""
        image_path = Path(image_path)
        if caption is None:
            caption = f"Fire risk map for {image_path.stem}"

        for chat_id in self.chat_ids:
            with image_path.open("rb") as photo:
                response = requests.post(
                    f"{self.api_url}/sendPhoto",
                    data={"chat_id": chat_id, "caption": caption},
                    files={"photo": photo},
                    timeout=config.REQUEST_TIMEOUT,
                )
            response.raise_for_status()


if __name__ == "__main__":
    from fetch import fetch_daily_image

    path = fetch_daily_image()
    TelegramNotifier().send_map(path)
    print(f"Sent {path} to Telegram")
