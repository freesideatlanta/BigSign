#!/usr/bin/env python3
"""Deploy to the Freeside sign: python3 deploy/deploy.py."""

import inspect
import shlex
import subprocess
from pathlib import Path


def install() -> None:
    """Runs on BigSign over SSH."""
    import os
    import subprocess
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

    autostart = Path("/home/eventerini/.config/autostart")
    autostart.mkdir(parents=True, exist_ok=True)
    run(
        [
            "install",
            "-m",
            "644",
            "deploy/kiosk.desktop",
            str(autostart / "kiosk.desktop"),
        ]
    )
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
    print("Deployed. Reload Chromium for HTML changes; log in again for kiosk changes.")


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
        "deploy/",
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
