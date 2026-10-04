#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p public
ln -sfn ../freeside-sign.html public/freeside-sign.html
ln -sfn ../eventsdata.json public/eventsdata.json
exec uv run --locked --no-dev python -m http.server 8080 --bind 0.0.0.0 --directory public
