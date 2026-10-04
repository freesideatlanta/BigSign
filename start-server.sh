#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec uv run --locked --no-dev python -m http.server 8080 --bind 127.0.0.1
