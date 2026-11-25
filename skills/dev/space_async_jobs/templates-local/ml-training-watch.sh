#!/usr/bin/env bash
# Template: ML training watcher hook (async-jobs pattern, remote host variant).
# Replace __PLACEHOLDER__ values, save as ~/hooks/scripts/ml-__RUN__-watch.sh,
# register as a hook with templates-local/ml-worker-prompt.md as the prompt.
#
# How it works:
# - One SSH call per poll reads the run's status.json, log mtime and process
#   presence on the training host. That data is a hint only.
# - Wake on: status transition (running/finished/failed), or a stall
#   (status=running but the log has not advanced for __STALL_SECS__).
# - Epoch progress alone does NOT wake; the reconciler / checkpoint cron
#   reports progress. This keeps wakes meaningful.
# - State snapshot lives in ~/hooks/state/ml-__PRODUCER__-last.json and is
#   not written on dry runs.
set -euo pipefail
source "$HATCH_HOOK_RUNTIME"

PRODUCER="__PRODUCER__"            # ^[a-z0-9-]+$  e.g. ml-indra-ocr-ft
HOST_IP="__HOST_IP__"              # Tailscale IP, e.g. gpu-01 100.105.219.77
REMOTE_RUN_DIR="__REMOTE_RUN_DIR__" # /home/ryo/agentic-project/<proj>/runs/<run>
STALL_SECS="__STALL_SECS__"        # e.g. 1800

case "$PRODUCER$HOST_IP$REMOTE_RUN_DIR$STALL_SECS" in
  *__*) silent "template placeholders not replaced" '{}' ;;
esac
command -v jq >/dev/null 2>&1 || silent "jq missing" '{}'

STATE_DIR="$HOME/hooks/state"
mkdir -p "$STATE_DIR"
LAST="$STATE_DIR/ml-$PRODUCER-last.json"
HEARTBEAT="$STATE_DIR/ml-$PRODUCER-hook.heartbeat"
if [ "${HATCH_HOOK_DRY_RUN:-0}" != "1" ]; then
  date +%s > "$HEARTBEAT" || silent "heartbeat write failed" '{}'
fi

SSH=(ssh -F /dev/null -i /home/hatch/.ssh/id_ed25519 -o IdentitiesOnly=yes
  -o UserKnownHostsFile=/home/hatch/.ssh/known_hosts
  -o ProxyCommand="python3 $HOME/.local/bin/tsproxy.py %h %p"
  -o BatchMode=yes -o ConnectTimeout=15)

# Single bounded probe: status.json content, log mtime (epoch secs), proc flag.
probe="$("${SSH[@]}" "ryo@$HOST_IP" \
  "cat '$REMOTE_RUN_DIR/status.json' 2>/dev/null; echo __SEP__; stat -c %Y '$REMOTE_RUN_DIR/train.log' 2>/dev/null || echo 0; pgrep -fc '[t]orchrun|[t]rain' || true" \
  2>/dev/null || true)"
if [ -z "$probe" ]; then
  log "probe failed (host unreachable or no status yet)" '{}'
  silent "probe failed" '{}'
fi

status_json="$(printf '%s' "$probe" | sed -n '1,/__SEP__/p' | sed '$d')"
rest="$(printf '%s' "$probe" | sed -n '/__SEP__/,$p' | tail -n +2)"
log_mtime="$(printf '%s' "$rest" | sed -n '1p')"
case "$log_mtime" in (*[!0-9]*|"") log_mtime=0 ;; esac

cur_status="$(printf '%s' "$status_json" | jq -r '.status // "unknown"' 2>/dev/null || echo unknown)"
cur_epoch="$(printf '%s' "$status_json" | jq -r '.epoch // -1' 2>/dev/null || echo -1)"

prev_status="none"; prev_epoch=-1
if [ -f "$LAST" ]; then
  prev_status="$(jq -r '.status // "none"' "$LAST" 2>/dev/null || echo none)"
  prev_epoch="$(jq -r '.epoch // -1' "$LAST" 2>/dev/null || echo -1)"
fi

now="$(date +%s)"
reason=""
if [ "$cur_status" != "$prev_status" ] && [ "$prev_status" != "none" ]; then
  reason="status $prev_status -> $cur_status"
elif [ "$prev_status" = "none" ] && [ "$cur_status" != "unknown" ]; then
  reason="first observation: $cur_status"
fi
if [ -z "$reason" ] && [ "$cur_status" = "running" ] && [ "$log_mtime" -gt 0 ] \
   && [ $(( now - log_mtime )) -gt "$STALL_SECS" ]; then
  reason="stall suspected: log unchanged for $(( now - log_mtime ))s while running"
fi

if [ "${HATCH_HOOK_DRY_RUN:-0}" != "1" ]; then
  printf '{"status":"%s","epoch":%s,"log_mtime":%s,"seen_at":%s}\n' \
    "$cur_status" "$cur_epoch" "$log_mtime" "$now" > "$LAST"
fi

if [ -n "$reason" ]; then
  log "ml watch: $reason" "{\"epoch\":$cur_epoch}"
  wake "ML training $PRODUCER: $reason" "{\"status\":\"$cur_status\",\"epoch\":$cur_epoch}"
fi
silent "no relevant change (status=$cur_status epoch=$cur_epoch)" '{}'
