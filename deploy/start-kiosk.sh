#!/usr/bin/env bash
set -euo pipefail
curl -fsS --retry 30 --retry-connrefused --retry-delay 1 --max-time 5 \
    http://localhost:8080/ >/dev/null
exec /usr/bin/chromium --ozone-platform=wayland \
    --user-data-dir="$HOME/.local/share/freeside-kiosk" \
    --kiosk --noerrdialogs --disable-infobars --no-first-run --incognito \
    --force-device-scale-factor=3 'http://localhost:8080/?portrait'
