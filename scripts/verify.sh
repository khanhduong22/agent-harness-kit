#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$kit_root/scripts/install.sh"
bash -n "$kit_root/scripts/update.sh"
bash -n "$kit_root/scripts/sync-upstream.sh"
bash -n "$kit_root/scripts/assert.sh"
bash -n "$kit_root/scripts/check-skill-ownership.sh"
/usr/bin/env python3 -m py_compile "$kit_root/scripts/sync_rules.py" "$kit_root/scripts/rollback.py" "$kit_root/scripts/sync_upstream.py" "$kit_root/scripts/verify.py"
/usr/bin/env python3 "$kit_root/scripts/verify.py"

# Skips silently unless AGENT_HARNESS_WORKSPACE is set, so a machine without the
# workspace checked out still verifies clean.
bash "$kit_root/scripts/check-skill-ownership.sh"
