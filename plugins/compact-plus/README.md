# compact-plus

[Japanese README](./README.ja.md) | [Architecture](./docs/architecture.md)

A transparent Claude Code plugin that strengthens `/compact` continuity without replacing Claude Code's compaction algorithm. It captures a structured checkpoint before compaction, hardens and redacts it, then restores it into the same session through documented hooks.

## Strategy

- **Primary path: same-session checkpoint.** `PreCompact` saves state and `SessionStart` with `compact|resume` injects it through `additionalContext`.
- **Fallback path: next-prompt guidance.** If direct restore did not run, `PostCompact` leaves a marker that `UserPromptSubmit` consumes once.
- **Emergency path: explicit handoff.** Export a sanitized handoff only when repeated compaction or contradictory context makes same-session recovery unreliable. The plugin does not start a successor session or re-register `/loop`.
- Project documents, rules, plans, Git, issues, pull requests, CI, and artifacts remain authoritative. A checkpoint is recovery evidence, not expanded permission.

## What It Preserves

The 18-section state records:

1. goal and definition of done
2. authoritative documents
3. active plan
4. current phase and tasks
5. task-list state
6. decisions
7. rejected hypotheses
8. constraints and blockers
9. Git state
10. pull-request state
11. `/loop` state and approval scope
12. worker topology
13. invoked skills and slash commands
14. edited files
15. failed attempts
16. next deterministic action
17. unverified items
18. recovery metadata

Large reproducible logs, full diffs, and generated output are omitted. Credentials, authorization/cookie values, passwords, private keys, URL credentials, known token forms, and personal email addresses are redacted before the final checkpoint is stored or restored.

## Usage

After installation, use `/compact` normally. Manual and automatic compaction use the same checkpoint path.

Optional controls:

- `/compact keep the security decisions` forwards priority guidance to the state-generation LLM.
- `/compact-plus` manually enriches and verifies the checkpoint before compaction.
- `/compact-plus handoff` exports emergency recovery material after checkpoint verification. A supervisor or user must start the new session, load the handoff, revalidate live state, and re-register `/loop` or monitors.

## Runtime Flow

1. `PreCompact`
   - `precompact-transcript-backup.sh` saves a transcript backup.
   - `precompact-state-summary.sh` selects and squashes transcript evidence, invokes the configured LLM backend, and writes rich state.
   - `scripts/checkpoint.py precompact` validates the session id and file ownership, migrates legacy headings, enforces the 18-section order, adds Git/recovery metadata, redacts sensitive data, limits the checkpoint to 64 KiB, and atomically writes mode `0600` in an owner-only directory.
2. `SessionStart` (`compact|resume`)
   - `scripts/checkpoint.py restore` validates and injects the checkpoint through `additionalContext` once per restore event window.
3. `PostCompact` and `UserPromptSubmit`
   - A short-lived restore receipt suppresses duplicate recovery guidance regardless of hook order.
   - If direct restore did not occur, the legacy marker causes one next-prompt recovery reference to be injected.
4. Threshold reminder
   - The existing warning marker can inject a short recitation of Active Plan, Current Phase and Tasks, and the latest Session Decision.

All hooks fail open: checkpoint failure does not block compaction.

## Requirements

- Claude Code v2.x or later
- Python 3
- `jq`
- An optional LLM backend through `claude -p` or `codex exec` for rich state generation

The default primary backend is `claude -p --model claude-sonnet-5 --effort medium`; the default fallback is `codex exec --model gpt-5.3-codex-spark`. If both fail, the deterministic checkpoint hardener still creates a minimal state file.

## Installation

Add this repository as a Claude Code marketplace, then install the plugin.

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install compact-plus@kotomiya07-skills --scope user
```

Restart Claude Code after installation. To update later:

```bash
claude plugin marketplace update kotomiya07-skills
claude plugin update compact-plus@kotomiya07-skills --scope user
```

Restart Claude Code again after updating. `npx skills add` installs only the skill files and does not install this plugin's hooks, so use the marketplace path for full functionality.

## Configuration

Set overrides under `env` in `~/.claude/settings.json` or export them for one session.

| Environment variable | Default | Purpose |
|---|---:|---|
| `COMPACT_PLUS_PRIMARY_BACKEND` | bundled `claude -p` command | Complete primary backend command; empty disables it |
| `COMPACT_PLUS_FALLBACK_BACKEND` | bundled `codex exec` command | Complete fallback backend command; empty disables it |
| `COMPACT_PLUS_TRANSCRIPT_MODE` | `incremental` | `incremental`, `head-tail`, or `tail` |
| `COMPACT_PLUS_TRANSCRIPT_HEAD_TURNS` | `5` | Head-side turn limit |
| `COMPACT_PLUS_TRANSCRIPT_TAIL_TURNS` | `25` | Tail-side turn limit |
| `COMPACT_PLUS_TRANSCRIPT_HEAD_KB` | `10` | Head-side byte cap in KiB |
| `COMPACT_PLUS_TRANSCRIPT_TAIL_KB` | `40` | Tail-side byte cap in KiB |
| `COMPACT_PLUS_INCREMENTAL_REFRESH` | `10` | Full rebuild cadence; `0` disables refresh |
| `COMPACT_PLUS_MAX_OUTPUT_TOKENS` | `4096` | Backend output cap when supported |
| `COMPACT_PLUS_SQUASH_ENABLED` | `1` | Tool-output squash toggle |
| `COMPACT_PLUS_SQUASH_READ_LINES` | `100` | Read/Grep/Glob squash threshold |
| `COMPACT_PLUS_SQUASH_BASH_CHARS` | `500` | Bash-output squash threshold |
| `COMPACT_PLUS_TWO_PASS` | `1` | LLM self-critique hint |

Backend commands receive `$SYSTEM_PROMPT`, `$SESSION_ID`, `$TRANSCRIPT_PATH`, and `$MAX_OUTPUT_TOKENS`.

`COMPACT_WARN_THRESHOLD` belongs to the external statusline producer, not this plugin.

## State and Marker Files

| Path | Purpose |
|---|---|
| `${TMPDIR}/claude-compact-state/<session_id>.md` | Hardened same-session checkpoint |
| `${TMPDIR}/claude-compact-handoff/<session_id>.md` | Explicit emergency handoff |
| `${TMPDIR}/claude-compact-restore-claims/*.claim` | Duplicate-injection guard |
| `${TMPDIR}/claude-compact-restored/<session_id>.md` | Short-lived direct-restore receipt |
| `${TMPDIR}/claude-compacted/<session_id>` | Legacy next-prompt fallback marker |
| `${TMPDIR}/claude-compact-state-offset/<session_id>` | Incremental transcript offset |
| `${TMPDIR}/claude-compact-state-counter/<session_id>` | Refresh counter |

## Development Checks

Run from the repository root:

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool plugins/compact-plus/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/compact-plus/hooks/hooks.json >/dev/null
python3 -m py_compile plugins/compact-plus/scripts/checkpoint.py
bash -n plugins/compact-plus/hooks/*.sh plugins/compact-plus/tests/*.sh
bash plugins/compact-plus/tests/checkpoint-hooks.sh
```
