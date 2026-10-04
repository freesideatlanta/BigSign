# Deploy

```sh
python3 deploy/deploy.py
```

Requires Python 3 and rsync locally, SSH access to `eventerini@192.168.1.138`,
and sudo on the host. Set the Discord bot `TOKEN` in
`/home/eventerini/Documents/.env` on the host before the first deploy.

Rerun the same command for updates. It preserves `.env` and unrelated cron jobs.
Events refresh hourly. Reload Chromium to apply HTML changes immediately;
kiosk launcher changes take effect at the next desktop login.

For failures, check `journalctl -u events-server.service` and
`/home/eventerini/Documents/cron.log` on the host.
