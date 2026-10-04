# Freeside Big Sign

A digital sign showing upcoming Freeside Atlanta events from Meetup and Discord.

## Local setup

From the project directory, with Python 3.13 and Bash installed:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Set `TOKEN` in `.env` to a Discord bot token. The bot must belong to Freeside's
Discord server; the collector currently reads scheduled events from the bot's
first server.

```sh
bash start-fetch.sh
bash start-server.sh
```

Open <http://127.0.0.1:8080/freeside-sign.html> in the display's browser.

## Refreshing events

Run `bash start-fetch.sh` to update `eventsdata.json`. For unattended operation,
schedule it with cron using the script's absolute path. Fetching requires
internet access to Meetup and Discord; the server script only serves the display
and does not collect new events.

The display reloads the JSON once an hour. Reload the browser to show a fresh
fetch immediately.

## Known limitations

- Discord event times use a fixed UTC−4 offset, which is incorrect during
  Atlanta's standard time.
- The fallback image `static/Members-Only-Event.png` is missing.
- The alternative Flask app (`app.py`) is missing its templates. Use the static
  display described above.
- The included server binds to localhost and serves the project directory.
  For remote displays, host the HTML, event JSON, and image assets separately
  from the source and `.env`.
