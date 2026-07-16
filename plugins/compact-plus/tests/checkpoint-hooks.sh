#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/compact-plus-test.XXXXXX")
trap 'rm -rf "$TMP_ROOT"' EXIT
export TMPDIR="$TMP_ROOT"
export HOME="$TMP_ROOT/home"
mkdir -p "$HOME"

SESSION_ID="123e4567-e89b-12d3-a456-426614174000"
STATE_FILE="$TMPDIR/claude-compact-state/$SESSION_ID.md"
PRECOMPACT=$(printf '{"session_id":"%s","trigger":"manual","cwd":"%s"}' "$SESSION_ID" "$ROOT")

printf '%s' "$PRECOMPACT" | python3 "$ROOT/scripts/checkpoint.py" precompact
[[ -f "$STATE_FILE" ]]
grep -q '^## Goal and Definition of Done$' "$STATE_FILE"
grep -q '^## Next Deterministic Action$' "$STATE_FILE"
grep -q 'trigger: manual' "$STATE_FILE"

python3 - "$STATE_FILE" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(
    "# Compact Prep State\n"
    "## Active Plan\n- Keep the current plan\n"
    "## Current Phase\n- Preserve the legacy phase\n"
    "## TaskList Summary\n- One task remains\n"
    "## Session Decisions\n- Preserve this rich decision\n"
    "## Constraints and Blockers\nNot verified\n"
    "## Worker Topology\nNot verified\n"
    "## Skills Invoked\nNot verified\n"
    "## Editing Files\nNot verified\n"
    "## Failed Attempts\nNot verified\n"
    "## Recovery Notes\n- Preserve the legacy recovery note\n",
    encoding="utf-8",
)
PY
printf '%s' "$PRECOMPACT" | python3 "$ROOT/scripts/checkpoint.py" precompact
grep -q 'Preserve the legacy phase' "$STATE_FILE"
grep -q 'Preserve the legacy recovery note' "$STATE_FILE"

python3 - "$STATE_FILE" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace(
    "## Constraints and Blockers\nNot verified",
    "## Constraints and Blockers\n"
    "password: super-secret\n"
    "api_token: sk-1234567890abcdefghijklmnop\n"
    "Authorization: Bearer dummy-authorization-value\n"
    "Found ghp_0123456789ABCDEF in command output\n"
    "owner@example.com\n"
    "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----",
)
path.write_text(text, encoding="utf-8")
PY
printf '%s' "$PRECOMPACT" | python3 "$ROOT/scripts/checkpoint.py" precompact
grep -q 'Preserve this rich decision' "$STATE_FILE"
! grep -q 'super-secret' "$STATE_FILE"
! grep -q 'sk-1234567890abcdefghijklmnop' "$STATE_FILE"
! grep -q 'dummy-authorization-value' "$STATE_FILE"
! grep -q 'ghp_0123456789ABCDEF' "$STATE_FILE"
! grep -q 'owner@example.com' "$STATE_FILE"
! grep -q 'BEGIN PRIVATE KEY' "$STATE_FILE"
grep -q '\[REDACTED SECRET\]' "$STATE_FILE"

python3 - "$STATE_FILE" <<'PY'
from pathlib import Path
import sys

expected = [
    "## Goal and Definition of Done",
    "## Authoritative Documents",
    "## Active Plan",
    "## Current Phase and Tasks",
    "## TaskList Summary",
    "## Session Decisions",
    "## Rejected Hypotheses",
    "## Constraints and Blockers",
    "## Git State",
    "## Pull Request State",
    "## Loop State and Approval Scope",
    "## Worker Topology",
    "## Skills Invoked",
    "## Editing Files",
    "## Failed Attempts",
    "## Next Deterministic Action",
    "## Unverified Items",
    "## Recovery Metadata",
]
actual = [line for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if line.startswith("## ")]
assert actual == expected
PY

got=$(printf '{"session_id":"%s","source":"resume"}' "$SESSION_ID" | python3 "$ROOT/scripts/checkpoint.py" restore)
printf '%s' "$got" | python3 -c 'import json,sys; data=json.load(sys.stdin); ctx=data["hookSpecificOutput"]["additionalContext"]; assert "Preserve this rich decision" in ctx; assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"'

compact_got=$(printf '{"session_id":"%s","source":"compact"}' "$SESSION_ID" | python3 "$ROOT/scripts/checkpoint.py" restore)
[[ -n "$compact_got" ]]
RESTORED_FILE="$TMPDIR/claude-compact-restored/$SESSION_ID.md"
MARKER_FILE="$TMPDIR/claude-compacted/$SESSION_ID"
[[ -f "$RESTORED_FILE" ]]
printf '{"session_id":"%s"}' "$SESSION_ID" | bash "$ROOT/hooks/compaction-recovery.sh"
[[ ! -e "$RESTORED_FILE" ]]
[[ ! -e "$MARKER_FILE" ]]
printf '{"session_id":"%s"}' "$SESSION_ID" | bash "$ROOT/hooks/compaction-recovery.sh"
[[ -f "$MARKER_FILE" ]]
fallback=$(printf '{"session_id":"%s"}' "$SESSION_ID" | bash "$ROOT/hooks/userpromptsubmit-compaction-recovery.sh")
printf '%s' "$fallback" | python3 -c 'import json,sys; data=json.load(sys.stdin); assert "[COMPACTION RECOVERY]" in data["hookSpecificOutput"]["additionalContext"]'
[[ ! -e "$MARKER_FILE" ]]

missing=$(printf '{"session_id":"223e4567-e89b-12d3-a456-426614174000","source":"resume"}' | python3 "$ROOT/scripts/checkpoint.py" restore)
[[ -z "$missing" ]]

invalid=$(printf '{"session_id":"../escape","trigger":"auto","cwd":"%s"}' "$ROOT" | python3 "$ROOT/scripts/checkpoint.py" precompact)
[[ -z "$invalid" ]]
[[ ! -e "$TMPDIR/escape.md" ]]

TRANSCRIPT_TARGET="$TMPDIR/transcript.jsonl"
TRANSCRIPT_LINK="$TMPDIR/transcript-link.jsonl"
printf '%s\n' '{"type":"user","message":{"content":"test"}}' > "$TRANSCRIPT_TARGET"
printf '{"session_id":"../shell-escape","transcript_path":"%s"}' "$TRANSCRIPT_TARGET" |
  bash "$ROOT/hooks/precompact-state-summary.sh"
[[ ! -e "$TMPDIR/shell-escape.md" ]]

ln -s "$TRANSCRIPT_TARGET" "$TRANSCRIPT_LINK"
printf '{"session_id":"323e4567-e89b-12d3-a456-426614174000","transcript_path":"%s"}' "$TRANSCRIPT_LINK" |
  bash "$ROOT/hooks/precompact-state-summary.sh"
[[ ! -e "$TMPDIR/claude-compact-state/323e4567-e89b-12d3-a456-426614174000.md" ]]

SYMLINK_TMP="$TMPDIR/symlink-boundary"
SYMLINK_TARGET="$SYMLINK_TMP/target"
mkdir -p "$SYMLINK_TARGET"
ln -s "$SYMLINK_TARGET" "$SYMLINK_TMP/claude-compact-state"
printf '{"session_id":"423e4567-e89b-12d3-a456-426614174000","transcript_path":"%s"}' "$TRANSCRIPT_TARGET" |
  TMPDIR="$SYMLINK_TMP" bash "$ROOT/hooks/precompact-state-summary.sh"
[[ ! -e "$SYMLINK_TARGET/423e4567-e89b-12d3-a456-426614174000.md" ]]

MARKER_SYMLINK_TMP="$TMPDIR/marker-symlink-boundary"
MARKER_SYMLINK_TARGET="$MARKER_SYMLINK_TMP/target"
mkdir -p "$MARKER_SYMLINK_TARGET"
ln -s "$MARKER_SYMLINK_TARGET" "$MARKER_SYMLINK_TMP/claude-compacted"
printf '{"session_id":"523e4567-e89b-12d3-a456-426614174000"}' |
  TMPDIR="$MARKER_SYMLINK_TMP" bash "$ROOT/hooks/compaction-recovery.sh"
[[ ! -e "$MARKER_SYMLINK_TARGET/523e4567-e89b-12d3-a456-426614174000" ]]

cp "$STATE_FILE" "$TMPDIR/good-state"
python3 - "$STATE_FILE" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).write_text("x" * 70000, encoding="utf-8")
PY
oversized=$(printf '{"session_id":"%s","source":"compact"}' "$SESSION_ID" | python3 "$ROOT/scripts/checkpoint.py" restore)
[[ -z "$oversized" ]]
printf '%s' "$PRECOMPACT" | python3 "$ROOT/scripts/checkpoint.py" precompact
[[ "$(wc -c < "$STATE_FILE")" -le 65536 ]]
grep -q '^## Recovery Metadata$' "$STATE_FILE"
cp "$TMPDIR/good-state" "$STATE_FILE"

handoff=$(python3 "$ROOT/scripts/checkpoint.py" prepare-handoff --session-id "$SESSION_ID")
[[ -f "$handoff" ]]
[[ "$(python3 "$ROOT/scripts/checkpoint.py" latest-handoff)" == "$handoff" ]]

python3 -m json.tool "$ROOT/hooks/hooks.json" >/dev/null
python3 - "$ROOT/hooks/hooks.json" <<'PY'
import json
from pathlib import Path
import sys
hooks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["hooks"]
assert any(
    item["matcher"] == "manual|auto"
    and any("checkpoint.py" in hook["command"] and "precompact" in hook["command"] for hook in item["hooks"])
    for item in hooks["PreCompact"]
)
assert any(
    item["matcher"] == "compact|resume"
    and any("checkpoint.py" in hook["command"] and "restore" in hook["command"] for hook in item["hooks"])
    for item in hooks["SessionStart"]
)
PY

printf 'checkpoint hook tests passed\n'
