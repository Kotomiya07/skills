#!/bin/bash
# PostCompact hook (matcher: ""): record compaction with a marker file.
# PostCompact does not support additionalContext output, so context injection
# is handled by the UserPromptSubmit hook (userpromptsubmit-compaction-recovery.sh).
#
# fail-open (always exit 0)

set -uo pipefail

INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[[ "$SESSION_ID" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$ ]] || exit 0

# SessionStart restore may run before or after PostCompact. A fresh receipt means the
# checkpoint was already injected, so suppress the legacy next-prompt fallback once.
RESTORED_DIR="${TMPDIR:-/tmp}/claude-compact-restored" # lint:allow-os-tmp
RESTORED_FILE="$RESTORED_DIR/$SESSION_ID.md"
if [[ -f "$RESTORED_FILE" && ! -L "$RESTORED_FILE" ]]; then
  RESTORED_AT=$(cat "$RESTORED_FILE" 2>/dev/null || true)
  NOW=$(date +%s)
  rm -f "$RESTORED_FILE" 2>/dev/null || true
  if [[ "$RESTORED_AT" =~ ^[0-9]+$ ]] && (( NOW >= RESTORED_AT && NOW - RESTORED_AT <= 30 )); then
    rm -f "${TMPDIR:-/tmp}/claude-compacted/$SESSION_ID" 2>/dev/null || true
    WARN_DIR="${TMPDIR:-/tmp}/claude-compact-warned" # lint:allow-os-tmp
    rm -f "$WARN_DIR/$SESSION_ID" 2>/dev/null || true
    exit 0
  fi
fi

# Write the marker file. UserPromptSubmit detects it, injects context, then removes it.
umask 077
MARKER_DIR="${TMPDIR:-/tmp}/claude-compacted" # lint:allow-os-tmp
[[ ! -L "$MARKER_DIR" ]] || exit 0
mkdir -p "$MARKER_DIR" 2>/dev/null || exit 0
[[ -d "$MARKER_DIR" && -O "$MARKER_DIR" ]] || exit 0
chmod 700 "$MARKER_DIR" 2>/dev/null || exit 0
MARKER_FILE="$MARKER_DIR/$SESSION_ID"
[[ ! -L "$MARKER_FILE" ]] || exit 0
if [[ -e "$MARKER_FILE" ]]; then
  [[ -f "$MARKER_FILE" && -O "$MARKER_FILE" ]] || exit 0
fi
printf '%s\n' "$(date +%s)" > "$MARKER_FILE" 2>/dev/null || exit 0
chmod 600 "$MARKER_FILE" 2>/dev/null || exit 0

# Reset the compact reminder cooldown after compact runs.
WARN_DIR="${TMPDIR:-/tmp}/claude-compact-warned" # lint:allow-os-tmp
rm -f "$WARN_DIR/$SESSION_ID" 2>/dev/null || true

exit 0
