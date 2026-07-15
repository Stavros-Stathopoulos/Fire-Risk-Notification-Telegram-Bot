# Fire-risk map bot

Fetches the next day's fire-risk map from civilprotection.gov.gr every
evening and sends it to you as a private Telegram message.

## Setup

1. Create a bot: talk to [@BotFather](https://t.me/BotFather) on Telegram,
   send `/newbot`, copy the token.
2. Send any message to your new bot, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the chat id.
3. `cp .env.example .env` and fill in both values. **Never commit `.env`.**

## Run with Docker

```bash
docker compose up -d --build
docker compose logs -f   # watch it work
```

The container runs `main.py`, which sleeps until `DAILY_RUN_AT` (default
20:00 Europe/Athens), then fetches tomorrow's map into `./data/` and sends
it to Telegram, retrying every 30 minutes if it isn't published yet.

## Run locally (one-off)

```bash
pip install -r requirements.txt
set -a; source .env; set +a
python fetch.py      # just download tomorrow's map
python notifier.py   # download and send it
```

## Configuration

Everything is overridable via environment variables — see
[config.py](config.py) and [.env.example](.env.example).
