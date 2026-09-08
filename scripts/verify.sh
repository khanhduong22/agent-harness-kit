#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$kit_root/scripts/install.sh"
bash -n "$kit_root/scripts/update.sh"
bash -n "$kit_root/scripts/sync-upstream.sh"
/usr/bin/env python3 -m py_compile "$kit_root/scripts/sync_rules.py" "$kit_root/scripts/rollback.py" "$kit_root/scripts/sync_upstream.py" "$kit_root/scripts/verify.py"
/usr/bin/env python3 "$kit_root/scripts/verify.py"
