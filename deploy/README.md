# Deploy

Deployment targets `eventerini@192.168.1.138` and installs into
`/home/eventerini/Documents`. These values are embedded in `deploy.py`, the
systemd units, cron entry, and Wayland session files. Update them consistently
before deploying to another host.

## Prerequisites

On the machine running deployment, install Python 3, OpenSSH's client, and
`rsync`. The target must be reachable over SSH as `eventerini`; deployment uses
an interactive SSH terminal so `sudo` can prompt for a password.

The target needs:

- A Linux installation using systemd, an active systemd user manager, and LightDM.
- Python 3, Bash, `curl`, `rsync`, `sudo`, and `crontab`.
- `/usr/bin/chromium`, `/usr/bin/labwc`, and `wlr-randr` for the Wayland kiosk.
- Permission for `eventerini` to use `sudo` to install services and update LightDM.
- Internet access for uv/Python/dependency installation and Meetup/Discord collection.
- A display reported by `wlr-randr` as `HDMI-A-1`. The autostart script rotates it
  by 270 degrees; adjust `deploy/labwc/autostart` for a different display or orientation.
- An existing `/etc/lightdm/lightdm.conf` with exactly one uncommented
  `user-session=` setting and one `autologin-session=` setting. The installer
  replaces their values with `freeside-kiosk`; configure LightDM to autologin
  as `eventerini` before deployment.

uv is installed into `/home/eventerini/.local/bin` if absent. The installer then
installs Python 3.13 and the locked production dependencies.

Create the bot configuration on the target before the first deploy:

```sh
ssh -t eventerini@192.168.1.138 'mkdir -p /home/eventerini/Documents && umask 077 && touch /home/eventerini/Documents/.env && chmod 600 /home/eventerini/Documents/.env && nano /home/eventerini/Documents/.env'
```

Set `TOKEN` in that file to the Discord bot token. The bot must belong to the
intended server and have permission to read its scheduled events. Collection
uses the bot's first server. Deployment leaves the target's `.env` in place.

## Run deployment

From the repository:

```sh
python3 deploy/deploy.py
```

The script copies the application, collects and validates the first JSON file,
installs the web server and hourly fetch job, and installs the Wayland kiosk
session. If it changes the LightDM session, it restarts LightDM, ending the
current graphical session. Otherwise it restarts the kiosk. It backs up changed
LightDM configuration to `/etc/lightdm/lightdm.conf.before-freeside-kiosk`.

The web server listens on port 8080 on all interfaces; allow access from the
intended LAN. View the sign at
<http://192.168.1.138:8080/freeside-sign.html>. Data collection runs at the top of
each hour; the browser refreshes hourly from the time it starts.

## Check operation

On the target:

```sh
systemctl status events-server.service
journalctl -u events-server.service
systemctl --user status freeside-kiosk.service
journalctl --user -u freeside-kiosk.service
crontab -l
tail /home/eventerini/Documents/cron.log
```

To collect immediately, run `bash /home/eventerini/Documents/start-fetch.sh`.
Reload the sign to display the result immediately. Failed collection leaves the
previous JSON file intact and exits with an error in the fetch log.
