# compact-plus Architecture

[Japanese architecture](./architecture.ja.md) | [README](../README.md) | [Japanese README](../README.ja.md)

compact-plus augments Claude Code context compaction through documented hooks. It does not replace the internal compaction algorithm or prompt. Its primary continuity mechanism is a structured checkpoint restored into the same session; a new-session handoff is explicit and exceptional.

## 1. Goals and Boundaries

### Goals

- Preserve goal, decisions, rejected hypotheses, remaining work, and execution state outside the compacted conversation.
- Restore that evidence immediately after `compact` or `resume` without waiting for another user prompt.
- Preserve Git, pull-request, `/loop`, worker, validation, and approval state needed for autonomous development.
- Keep project documents and live external state authoritative.
- Redact secrets and personal data, enforce bounded files, and fail open without blocking compaction.

### Non-goals

- Replacing Claude Code's compaction algorithm or built-in compact summary.
- Treating a checkpoint as authorization for commit, push, PR creation, merge, deployment, or other shared-state changes.
- Automatically starting a successor session, loading a handoff, or re-registering `/loop`, monitors, or background processes.
- Storing complete transcripts, large logs, full diffs, or other reproducible output in the checkpoint.

## 2. Continuity Layers

### 2.1 Same-session checkpoint (primary)

`PreCompact` creates rich state and then runs the deterministic checkpoint hardener. `SessionStart` with source `compact` or `resume` validates and injects that checkpoint through `additionalContext`.

The restored state is recovery evidence. The resumed agent must re-read listed authoritative documents and re-check unverified or live state before acting.

### 2.2 Next-prompt recovery (fallback)

`PostCompact` writes a one-shot marker. If direct `SessionStart` restore did not run, `UserPromptSubmit` consumes the marker and injects references to the checkpoint, active plan, and original instruction sources.

A short-lived restore receipt suppresses this fallback when direct restore succeeded. The receipt design works whether `SessionStart` runs before or after `PostCompact`.

### 2.3 Emergency handoff (explicit)

`checkpoint.py prepare-handoff --session-id <id>` exports a sanitized handoff under `${TMPDIR}/claude-compact-handoff/`. Use it only when repeated compaction, contradictory summaries, or severe context drift makes same-session recovery unreliable.

The handoff does not start a new session and does not broaden approval. A supervisor or user must start the successor, load the handoff, revalidate Git/Issue/PR/CI state, and re-register `/loop` and non-persistent monitors.

## 3. Runtime Flow

1. `PreCompact` backs up the transcript.
2. `precompact-state-summary.sh` selects incremental, head-tail, or tail evidence and squashes large tool output.
3. The configured LLM backend emits the 18-section rich state. Backend failure is allowed.
4. `checkpoint.py precompact` validates or creates the final checkpoint:
   - strict session ID validation;
   - owner-only state directory and regular-file ownership checks;
   - symlink rejection;
   - legacy 10-section migration;
   - exact 18-section ordering;
   - Git and recovery metadata fallback;
   - sensitive-data redaction;
   - 64 KiB cap;
   - atomic mode-`0600` write and readback.
5. `SessionStart` (`compact|resume`) runs `checkpoint.py restore`.
6. Restore rejects malformed, oversized, incomplete, unowned, or symlinked state and injects valid state once per event window.
7. Restore records success so the legacy next-prompt path does not duplicate context.
8. If direct restore did not happen, `PostCompact` and `UserPromptSubmit` provide one fallback recovery injection.

All hook paths fail open.

## 4. State Contract

The exact order is:

1. `## Goal and Definition of Done`
2. `## Authoritative Documents`
3. `## Active Plan`
4. `## Current Phase and Tasks`
5. `## TaskList Summary`
6. `## Session Decisions`
7. `## Rejected Hypotheses`
8. `## Constraints and Blockers`
9. `## Git State`
10. `## Pull Request State`
11. `## Loop State and Approval Scope`
12. `## Worker Topology`
13. `## Skills Invoked`
14. `## Editing Files`
15. `## Failed Attempts`
16. `## Next Deterministic Action`
17. `## Unverified Items`
18. `## Recovery Metadata`

Legacy `## Current Phase` and `## Recovery Notes` content migrates to the corresponding new sections. Missing content is marked `Not verified`; it is not invented.

`## Loop State and Approval Scope` records recurrence, wake signals, and the currently explicit authorization boundary. It must never infer permission from prior unrelated operations.

## 5. Security Model

Untrusted inputs include hook JSON, transcript excerpts, LLM output, existing checkpoint files, Git output, and environment-derived paths.

Controls:

- hook input: 1 MiB maximum;
- checkpoint and handoff: 64 KiB maximum;
- Git status capture: 8 KiB maximum;
- session IDs: `[A-Za-z0-9][A-Za-z0-9_-]{0,127}`;
- directories: current-user ownership, mode `0700`, no directory symlink;
- files: current-user regular files, no symlink, mode `0600`;
- writes: same-directory temporary file, `fsync`, atomic replace, readback;
- redaction: secret assignments, authorization and cookie headers, bearer and known token forms, private-key blocks, URL credentials, and email addresses.

When rich state is malformed or too large, the hardener replaces it with a minimal deterministic checkpoint rather than preserving unsafe content.

## 6. Source-of-Truth Hierarchy

For recovery decisions, use this order:

1. explicit current user instruction and durable approval policy;
2. project rules, specifications, plans, ADRs, and tests;
3. live Git, Issue, PR, CI, artifact, and process state;
4. checkpoint or emergency handoff;
5. compacted conversation summary.

A checkpoint may point to authoritative material but cannot supersede it.

## 7. Files and Ownership

| Path | Writer | Reader | Purpose |
|---|---|---|---|
| `${TMPDIR}/claude-compact-state/<session_id>.md` | rich generator and hardener | restore and fallback hooks | Hardened checkpoint |
| `${TMPDIR}/claude-compact-handoff/<session_id>.md` | explicit handoff command | successor session or supervisor | Emergency recovery material |
| `${TMPDIR}/claude-compact-restore-claims/*.claim` | restore | restore | Duplicate injection guard |
| `${TMPDIR}/claude-compact-restored/<session_id>.md` | restore | PostCompact/UserPromptSubmit | Short-lived success receipt |
| `${TMPDIR}/claude-compacted/<session_id>` | PostCompact | UserPromptSubmit | Fallback trigger |
| `${TMPDIR}/claude-compact-state-offset/<session_id>` | rich generator | rich generator | Incremental offset |
| `${TMPDIR}/claude-compact-state-counter/<session_id>` | rich generator | rich generator | Refresh cadence |
| `${TMPDIR}/claude-active-plan/<session_id>` | external plan hook | state generator and fallback | Active-plan pointer |

## 8. Configuration Boundary

compact-plus owns `COMPACT_PLUS_PRIMARY_BACKEND`, `COMPACT_PLUS_FALLBACK_BACKEND`, transcript selection limits, output squash settings, refresh cadence, output token cap, and two-pass guidance. The external statusline producer owns `COMPACT_WARN_THRESHOLD`.

The plugin uses `PreCompact`, `PostCompact`, `SessionStart`, and `UserPromptSubmit`. Global settings do not need duplicate checkpoint hooks when the plugin is enabled.
