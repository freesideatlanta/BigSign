#!/usr/bin/env python3
"""Deploy to the Freeside sign: python3 deploy/deploy.py."""

import inspect
import shlex
import subprocess
from pathlib import Path


def install() -> None:
    """Runs on BigSign over SSH."""
    import os
    import re
    import shutil
    import subprocess
    import time
    from pathlib import Path

    def run(
        command: list[str],
        *,
        input: bytes | str | None = None,
        text: bool = False,
        stdout: int | None = None,
    ) -> None:
        subprocess.run(command, check=True, input=input, text=text, stdout=stdout)

    root = Path("/home/eventerini/Documents")
    os.chdir(root)
    os.environ["PATH"] = f"/home/eventerini/.local/bin:{os.environ['PATH']}"
    run(["sudo", "-v"])
    uv = Path("/home/eventerini/.local/bin/uv")
    if not uv.exists():
        installer = subprocess.run(
            ["curl", "-fsSL", "https://astral.sh/uv/install.sh"],
            check=True,
            capture_output=True,
        ).stdout
        run(["sh"], input=installer)
    run([str(uv), "python", "install", "3.13"])
    run([str(uv), "sync", "--locked", "--no-dev"])
    (root / ".env").chmod(0o600)
    run(
        [
            str(uv),
            "run",
            "--locked",
            "--no-dev",
            "python",
            "-c",
            "from dotenv import dotenv_values; assert dotenv_values('.env').get('TOKEN'), 'Set TOKEN in .env'",
        ]
    )
    run(["bash", "start-fetch.sh"])
    run(
        [
            str(uv),
            "run",
            "--locked",
            "--no-dev",
            "python",
            "-m",
            "json.tool",
            "eventsdata.json",
        ],
        stdout=subprocess.DEVNULL,
    )

    run(
        [
            "sudo",
            "install",
            "-m",
            "644",
            "deploy/events-server.service",
            "/etc/systemd/system/events-server.service",
        ]
    )
    run(["sudo", "systemctl", "daemon-reload"])
    run(["sudo", "systemctl", "enable", "events-server.service"])

    cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if cron.returncode and "no crontab for" not in cron.stderr.lower():
        raise RuntimeError(cron.stderr.strip())
    lines = [
        line
        for line in cron.stdout.splitlines()
        if line.lstrip().startswith("#")
        or not any(
            str(root / script) in line for script in ("jsonolater.py", "start-fetch.sh")
        )
    ]
    entry = (root / "deploy/events-fetch.cron").read_text().strip()
    run(["crontab", "-"], input="\n".join([*lines, entry]) + "\n", text=True)

    user_units = Path("/home/eventerini/.config/systemd/user")
    user_units.mkdir(parents=True, exist_ok=True)
    run(
        [
            "install",
            "-m",
            "644",
            "deploy/freeside-kiosk.service",
            str(user_units / "freeside-kiosk.service"),
        ]
    )
    run(["systemctl", "--user", "daemon-reload"])
    run(
        [
            "sudo",
            "install",
            "-m",
            "644",
            "deploy/freeside-kiosk.desktop",
            "/usr/share/wayland-sessions/freeside-kiosk.desktop",
        ]
    )
    # LightDM's main configuration overrides conf.d, so update its seat settings.
    lightdm = Path("/etc/lightdm/lightdm.conf")
    config = lightdm.read_text()
    updated = config
    for key in ("user-session", "autologin-session"):
        updated, count = re.subn(
            rf"^{key}=.*$", f"{key}=freeside-kiosk", updated, flags=re.MULTILINE
        )
        if count != 1:
            raise RuntimeError(f"Expected one {key} setting in {lightdm}")
    session_changed = updated != config
    if session_changed:
        backup = Path("/etc/lightdm/lightdm.conf.before-freeside-kiosk")
        if not backup.exists():
            run(["sudo", "cp", "-p", str(lightdm), str(backup)])
        run(
            ["sudo", "tee", str(lightdm)],
            input=updated,
            text=True,
            stdout=subprocess.DEVNULL,
        )
    Path("/home/eventerini/.config/autostart/kiosk.desktop").unlink(missing_ok=True)
    run(["sudo", "systemctl", "restart", "events-server.service"])
    run(
        [
            "curl",
            "-fsS",
            "--retry",
            "5",
            "--retry-connrefused",
            "--retry-delay",
            "1",
            "--max-time",
            "5",
            "http://localhost:8080/eventsdata.json",
        ],
        stdout=subprocess.DEVNULL,
    )
    if session_changed:
        run(["sudo", "systemctl", "restart", "lightdm"])
    else:
        session_env = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            check=True,
            capture_output=True,
            text=True,
        )
        wayland_env = os.environ.copy()
        for line in session_env.stdout.splitlines():
            key, _, value = line.partition("=")
            if key in ("WAYLAND_DISPLAY", "XDG_RUNTIME_DIR"):
                wayland_env[key] = value
        subprocess.run(
            ["sh", "deploy/labwc/autostart"],
            check=True,
            env=wayland_env,
        )
        run(["systemctl", "--user", "restart", "freeside-kiosk.service"])
    for _ in range(30):
        kiosk = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", "freeside-kiosk.service"]
        )
        if kiosk.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError(
            "Wayland kiosk did not start; check journalctl --user -u freeside-kiosk"
        )
    time.sleep(2)
    run(["systemctl", "--user", "is-active", "--quiet", "freeside-kiosk.service"])
    # Retire the old environment only after the new service passes its health check.
    for name in ("myenv", "__pycache__"):
        path = root / name
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
    for name in (
        "requirements.txt",
        "deploy.py",
        "events-fetch.cron",
        "events-server.service",
        "kiosk.desktop",
    ):
        (root / name).unlink(missing_ok=True)
    for name in ("kiosk.desktop", "reload-kiosk.sh"):
        (root / "deploy" / name).unlink(missing_ok=True)
    print("Deployed. Wayland kiosk restarted with the updated sign.")


def deploy() -> None:
    root = Path(__file__).resolve().parents[1]
    host = "eventerini@192.168.1.138"
    target = "/home/eventerini/Documents"

    env_check = subprocess.run(["ssh", host, f"test -s {target}/.env"])
    if env_check.returncode == 1:
        raise SystemExit(
            f"Missing or empty {target}/.env on {host}.\n"
            "Create it on the host and set TOKEN to the Discord bot token:\n"
            f"  ssh -t {host} "
            + shlex.quote(
                f"mkdir -p {target} && umask 077 && touch {target}/.env "
                f"&& chmod 600 {target}/.env && nano {target}/.env"
            )
            + "\nThen rerun this deploy command."
        )
    if env_check.returncode:
        raise SystemExit(
            f"Could not check {target}/.env on {host} "
            f"(SSH exited with status {env_check.returncode}). "
            "Resolve the SSH error above and retry."
        )
    files = [
        *[path.name for path in root.glob("*.py")],
        "freeside-sign.html",
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        ".env.example",
        "start-fetch.sh",
        "start-server.sh",
        "deploy",
    ]
    subprocess.run(
        ["rsync", "-av", "--", *files, f"{host}:{target}/"], cwd=root, check=True
    )
    remote = inspect.getsource(install) + "\ninstall()\n"
    subprocess.run(
        ["ssh", "-t", host, shlex.join(["python3", "-c", remote])], check=True
    )


if __name__ == "__main__":
    deploy()
