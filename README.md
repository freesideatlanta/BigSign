# Freeside Big Sign

Displays Freeside Atlanta events from Meetup and Discord.

## Run locally

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```sh
uv python install 3.13
uv sync --locked
cp .env.example .env
```

Set `TOKEN` in `.env` to the Freeside Discord bot token. The collector uses the
bot's first server.

```sh
bash start-fetch.sh
bash start-server.sh
```

Open <http://localhost:8080/freeside-sign.html>. Rerun the fetch script to update
events; reload the browser to show them immediately.

## Deploy

```sh
python3 deploy/deploy.py
```

See [deployment prerequisites](deploy/README.md).

## Before committing Python changes

```sh
uv run ruff format .
uv run ruff check .
```
