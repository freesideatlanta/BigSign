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
uv run ty check
uv run python -m unittest discover -s tests
```

Python uses fully annotated functions and strict Pydantic models for Meetup,
Discord, configuration, normalized events, and sign JSON. Wrong field types are
rejected rather than coerced; model assignments are also validated. Upstream
models ignore provider fields the sign does not use, while internal models reject
unexpected fields. Ruff enforces annotations and ty checks the whole project.
