#!/usr/bin/env bash
# heavy-lock.sh - N-slot machine-wide lock for heavy jobs (headless Chrome, a vite build,
# Blender, a balance sweep). Generalised from the one-slot `mkdir` lock we used on a 16 GB laptop;
# a 32 GB machine got two slots.
#
# Usage:
#   heavy-lock.sh [-n SLOTS] [-d LOCK_DIR_PREFIX] [-s POLL_SECONDS] -- <command> [args...]
#
#   -n  number of slots (default 1; use 2 on a 32 GB machine)
#   -d  lock path prefix (default /tmp/game-heavy); slot k is "<prefix>-<k>.lock"
#   -s  seconds between retries (default 20)
#
# Examples:
#   heavy-lock.sh -- npx vite build
#   heavy-lock.sh -n 2 -- npx tsx tools/shots.ts
#
# Rules it encodes (each one cost us something):
#   * mkdir is the atomic test-and-set; no PID files, no flock needed (works on macOS and Linux).
#   * The slot is released on EVERY exit path (success, failure, Ctrl-C) via trap.
#   * It never kills anything. A stale lock from a dead run is reported, not deleted: check the
#     holder with `ls -ld <lock>` and remove it yourself, because killing/removing blindly once
#     destroyed another agent's work.
#   * Exit status is the wrapped command's status.
set -u
slots=1; prefix=/tmp/game-heavy; poll=20
while getopts "n:d:s:" o; do
  case $o in n) slots=$OPTARG;; d) prefix=$OPTARG;; s) poll=$OPTARG;; *) exit 2;; esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift
[ $# -ge 1 ] || { echo "usage: heavy-lock.sh [-n SLOTS] [-d PREFIX] [-s SECS] -- cmd..." >&2; exit 2; }
case $slots in ''|*[!0-9]*) echo "SLOTS must be a positive integer" >&2; exit 2;; esac
[ "$slots" -ge 1 ] || { echo "SLOTS must be >= 1" >&2; exit 2; }

held=""
release() { [ -n "$held" ] && rmdir "$held" 2>/dev/null; held=""; }
trap release EXIT
trap 'exit 130' INT TERM

waited=0
while [ -z "$held" ]; do
  k=1
  while [ "$k" -le "$slots" ]; do
    if mkdir "${prefix}-${k}.lock" 2>/dev/null; then held="${prefix}-${k}.lock"; break; fi
    k=$((k+1))
  done
  [ -n "$held" ] && break
  if [ $((waited % 300)) -eq 0 ] && [ "$waited" -gt 0 ]; then
    echo "heavy-lock: still waiting after ${waited}s; holders: $(ls -ld ${prefix}-*.lock 2>/dev/null | awk '{print $6,$7,$8,$9}' | tr '\n' ';')" >&2
  fi
  sleep "$poll"; waited=$((waited+poll))
done
echo "heavy-lock: acquired $held" >&2
"$@"; rc=$?
exit $rc
