#!/usr/bin/env bash
# Assertion helpers shared by scripts/test.sh and tests/test_harness.sh.
#
# macOS ships bash 3.2, where `set -e` does NOT abort on a failing `[[ ... ]]`
# test or on a `! cmd` negation — POSIX exempts both. Assertions written that
# way are silent no-ops. Both suites did exactly that and reported "passed"
# while asserting symlinks for skills that had been purged from the kit.
#
# Route every assertion through these helpers. They exit explicitly, so they
# behave the same on bash 3.2 and bash 5.
#
# Usage:
#   assert "description" test -L "$path"
#   assert "description" grep -q 'pattern' "$file"
#   refute "description" grep -q 'pattern' "$file"
#
# Note the command must be a real command or builtin (`test`, `grep`, ...),
# not the `[[ ]]` keyword, which cannot be passed as arguments.

assert() {
  local description="$1"
  shift
  if ! "$@"; then
    printf 'FAIL: %s\n' "$description" >&2
    exit 1
  fi
}

refute() {
  local description="$1"
  shift
  if "$@"; then
    printf 'FAIL: %s (expected to fail, but succeeded)\n' "$description" >&2
    exit 1
  fi
}

# Echo the names of real skills shipped by the kit, one per line. Suites sample
# from this instead of hardcoding names, which rot every time a skill is
# renamed or purged.
kit_skill_names() {
  local kit_root="$1" skill_dir
  for skill_dir in "$kit_root"/skills/*/; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    basename "$skill_dir"
  done
}
