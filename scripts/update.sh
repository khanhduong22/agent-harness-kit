#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

git -C "$kit_root" pull --ff-only
exec "$kit_root/scripts/install.sh" "$@"
