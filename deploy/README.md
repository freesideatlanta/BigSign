# Deploy

```sh
python3 deploy/deploy.py
```

Requires Python 3 and rsync locally, SSH access to `eventerini@192.168.1.138`,
and sudo on the host. Set the Discord bot `TOKEN` in
`/home/eventerini/Documents/.env` on the host before the first deploy.

To create or edit that file with restricted permissions:

```sh
ssh -t eventerini@192.168.1.138 'mkdir -p /home/eventerini/Documents && umask 077 && touch /home/eventerini/Documents/.env && chmod 600 /home/eventerini/Documents/.env && nano /home/eventerini/Documents/.env'
```

In the editor, add `TOKEN=your_discord_bot_token`, save, and exit. Then run the
deploy command again. A missing or empty remote `.env` stops deployment before
any files are copied.

Rerun the same command for updates. It preserves `.env` and unrelated cron jobs.
Events refresh hourly. Reload Chromium to apply HTML changes immediately;
kiosk launcher changes take effect at the next desktop login.

For failures, check `journalctl -u events-server.service` and
`/home/eventerini/Documents/cron.log` on the host.
