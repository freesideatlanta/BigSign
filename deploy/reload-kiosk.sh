#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

if [[ "$DISPLAY" == :0 && ! -S /tmp/.X11-unix/X0 ]]; then
    echo "No desktop session running; kiosk will open at the next login."
    exit 0
fi

# Check access first so a display authentication error cannot look like no kiosk.
xdotool getdisplaygeometry >/dev/null
if windows=$(xdotool search --onlyvisible --all --class chromium \
    --name '^Freeside Atlanta — Upcoming Events'); then
    for window in $windows; do
        xdotool windowactivate --sync "$window"
        xdotool key --clearmodifiers ctrl+F5
    done
    echo "Chromium kiosk reloaded."
else
    status=$?
    if [[ "$status" != 1 ]]; then
        exit "$status"
    fi
    echo "No visible sign window; kiosk will open at the next login."
fi
