# Fire-risk map bot

Fetches the next day's fire-risk map from civilprotection.gov.gr every
evening and sends it to you as a private Telegram message.

## Setup

1. Create a bot: talk to [@BotFather](https://t.me/BotFather) on Telegram,
   send `/newbot`, copy the token.
2. Send any message to your new bot, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the chat id.
3. `cp .env.example .env` and fill in both values. **Never commit `.env`.**

## Run the published image (no clone needed)

Every push to `main` publishes the image to GitHub Container Registry.
All you need is a `.env` file (step 3 above):

```bash
docker pull ghcr.io/stavros-stathopoulos/fire-risk-notification-telegram-bot:latest
mkdir -p data logs
sudo chown -R 1000:1000 data logs   # the container writes as uid 1000 (appuser)
docker run -d --name firemap \
  --env-file .env \
  -e TZ=Europe/Athens \
  -v "$PWD/data:/app/data" \
  -v "$PWD/logs:/app/logs" \
  --restart unless-stopped \
  ghcr.io/stavros-stathopoulos/fire-risk-notification-telegram-bot:latest
docker logs -f firemap   # watch the startup check run
```

## Run with Docker Compose (from a clone)

```bash
docker compose -f docker/docker-compose.yml up -d          # pulls the published image
docker compose -f docker/docker-compose.yml up -d --build  # or build locally
docker compose -f docker/docker-compose.yml logs -f        # watch it work
```

On startup the bot immediately runs a self-check: it sends a status
message and delivers the current map, so in a new environment you see it
working right away instead of waiting for the next cycle. It then sleeps
until `DAILY_RUN_AT` (default 20:00 Europe/Athens), fetches tomorrow's
map into `./data/` and sends it to Telegram, retrying every 30 minutes
if it isn't published yet. Maps older than 30 days
(`MAP_RETENTION_DAYS`) are deleted automatically.

## Run locally

```bash
pip install -e .
python main.py               # or just: firemap
python -m firemap.fetch      # one-off: just download tomorrow's map
python -m firemap.notifier   # one-off: download and send it
```

## Logs

Besides the console, every action (fetch, save, send, retry, failure) is
appended as one JSON object per line to `logs/actions.jsonl` with a UTC
timestamp and structured fields (`action`, `url`, `chat_id`, …). The file
rotates at midnight and only the last 7 days are kept, so storage use
stays bounded.

## Configuration

Everything is overridable via environment variables — see
[src/firemap/config.py](src/firemap/config.py) and [.env.example](.env.example).

## Project structure

```text
main.py                # thin entrypoint (the app lives in the package)
pyproject.toml         # packaging + dependencies
src/firemap/           # application package
  main.py              # daily scheduling loop
  config.py            # env-driven configuration
  fetch.py             # downloads the map from civilprotection.gov.gr
  notifier.py          # sends messages/photos via the Telegram Bot API
  logging_setup.py     # console + rotating JSONL action log
docker/                # Dockerfile and docker-compose.yml
data/                  # downloaded maps (volume-mounted in Docker)
logs/                  # actions.jsonl, 7-day rotating history
```
