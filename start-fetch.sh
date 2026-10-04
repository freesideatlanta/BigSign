#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec flock -n .events-fetch.lock uv run --locked --no-dev python jsonolater.py
