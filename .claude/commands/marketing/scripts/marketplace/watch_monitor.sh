#!/bin/bash
# Parameterised monitor loop: runs the buyer-message watcher repeatedly, but only inside an
# ACTIVE window (the hours the seller actually answers buyers). Outside it, it sleeps.
#
# Required env vars: whatever watch_buyer_messages.py itself needs (MKT_GMAIL_TOKEN_PATH,
# MKT_GMAIL_CREDENTIALS_PATH, MKT_STATE_FILE). Export them before starting this loop. Use ABSOLUTE
# paths for them: this script does not cd, so a relative path resolves against wherever you
# started it from.
#
# Optional env vars:
#   MKT_WATCH_SCRIPT    path to the watcher to run (default: watch_buyer_messages.py beside this
#                       script, resolved from this script's own absolute location)
#   MKT_POLL_SECONDS    seconds between ticks (default 180)
#   MKT_ACTIVE_START    HHMM, start of the window in which it polls (default 0730)
#   MKT_ACTIVE_END      HHMM, end of that window (default 2300)
#   MKT_TICK_TIMEOUT    seconds before a stuck tick is killed (default 90)
#
# Run exactly ONE of these per sale. A second instance racing the same MKT_STATE_FILE can
# double-print and double-archive buyer messages.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"

WATCH_SCRIPT="${MKT_WATCH_SCRIPT:-$HERE/watch_buyer_messages.py}"
POLL_SECONDS="${MKT_POLL_SECONDS:-180}"
ACTIVE_START="${MKT_ACTIVE_START:-0730}"
ACTIVE_END="${MKT_ACTIVE_END:-2300}"
TICK_TIMEOUT="${MKT_TICK_TIMEOUT:-90}"

if [ ! -f "$WATCH_SCRIPT" ]; then
  echo "WATCH ERROR: watcher not found at $WATCH_SCRIPT" >&2
  exit 1
fi

while true; do
  hm=$(date +%H%M)
  if [ "$((10#$hm))" -ge "$((10#$ACTIVE_START))" ] && [ "$((10#$hm))" -lt "$((10#$ACTIVE_END))" ]; then
    out=$(timeout "$TICK_TIMEOUT" python3 "$WATCH_SCRIPT" 2>&1); rc=$?
    echo "$out" | grep -E '^==|^archived|more not shown'
    [ $rc -ne 0 ] && echo "WATCH ERROR rc=$rc: $(echo "$out" | tail -2 | tr '\n' ' ' | cut -c1-200)"
  fi
  sleep "$POLL_SECONDS"
done
