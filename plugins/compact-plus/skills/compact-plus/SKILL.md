---
name: compact-plus
description: |
  Save and harden Claude Code recovery state before /compact, or export an explicit emergency handoff when same-session recovery is no longer reliable.
  MANDATORY TRIGGERS: /compact-plus, compact-plus, compact plus, compaction checkpoint, emergency compact handoff, pre-compact state save.
  DO NOT TRIGGER: ordinary progress updates, plan creation, or casual context-usage discussion.
codex_description: |
  Save compact-plus recovery state before /compact, or explicitly export an emergency handoff. Prefer same-session checkpoints.
strict_procedure: true
argument-hint: "[recovery notes | handoff]"
allowed-tools: Bash, Read, Write, Edit, Grep
---

# compact-plus

Prefer Claude Code's automatic `PreCompact` checkpoint and `SessionStart` restore path. Use this skill to enrich state manually before `/compact`, or to export a handoff only when repeated compaction has made the current session unreliable.

A checkpoint is recovery evidence. Project documents, rules, plans, Git, issues, pull requests, CI, and artifacts remain authoritative and must be revalidated after recovery.

## Hard gates

- Detect the session id with `${CLAUDE_PLUGIN_ROOT}/scripts/get-session-id.sh`. Never guess it.
- Write only `${TMPDIR:-/tmp}/claude-compact-state/${SESSION_ID}.md`.
- Redact secrets and personal data before writing. Never store tokens, authorization/cookie values, passwords, private keys, URL credentials, or personal email addresses.
- Keep the file under 64 KiB. Omit reproducible logs, full diffs, and generated output; record concise results and source paths instead.
- Do not broaden approval scope. A checkpoint or handoff never authorizes commit, push, PR, merge, destructive actions, or external messages.

## Checkpoint procedure

1. Detect the session id. Stop if unavailable.
2. Re-read relevant authoritative project documents and the active plan when visible.
3. Inspect current task, Git, PR/CI, `/loop` or monitor state, workers, and edited files. Mark unavailable or stale-prone facts `Not verified`.
4. Write the exact format below, with every heading once and in order.

```markdown
# Compact Prep State
## Goal and Definition of Done
## Authoritative Documents
## Active Plan
## Current Phase and Tasks
## TaskList Summary
## Session Decisions
## Rejected Hypotheses
## Constraints and Blockers
## Git State
## Pull Request State
## Loop State and Approval Scope
## Worker Topology
## Skills Invoked
## Editing Files
## Failed Attempts
## Next Deterministic Action
## Unverified Items
## Recovery Metadata
```

5. Run the hardener with the same session id and current working directory:

```bash
printf '%s' "{\"session_id\":\"${SESSION_ID}\",\"trigger\":\"manual\",\"cwd\":\"${PWD}\"}" |
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint.py" precompact
```

6. Read the file back. Verify exact heading order, redaction, the 64 KiB limit, and the deterministic next action.
7. Report the path, saved essentials, and unverified items. Tell the user that preparation is complete and `/compact` can run.

## Content rules

- Record the goal and observable definition of done.
- Record authoritative paths and which facts require rereading.
- Preserve decisions separately from rejected hypotheses and failed attempts.
- Record repository, branch, HEAD, worktree, issue/PR/check state, and which remote facts require refresh.
- Record the original `/loop` prompt, cadence, monitor/wakeup facts, and current approval boundary. Do not claim session-scoped monitors or background commands survive resume.
- Record active worker roles and cleanup facts.
- List only skills and slash commands actually invoked; invocation history does not reactivate them.
- Make `Next Deterministic Action` one evidence-backed first action.

## Emergency handoff

Use handoff only after same-session checkpoint recovery is inadequate because of repeated compaction, contradictory state, or clear context drift. It does not start a new session or re-register `/loop`.

1. Complete and verify the checkpoint procedure first.
2. Export a sanitized handoff:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint.py" prepare-handoff --session-id "${SESSION_ID}"
```

3. Read back the returned path. Confirm that the handoff is explicit recovery material, not expanded authorization.
4. Report that an external supervisor or the user must start the successor session, load the handoff, revalidate Git/issue/PR/CI state, and re-register `/loop` or monitors as needed.

Use `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint.py" latest-handoff` only to locate the newest previously exported handoff; never treat newest-by-time as sufficient proof that it belongs to the current task.
