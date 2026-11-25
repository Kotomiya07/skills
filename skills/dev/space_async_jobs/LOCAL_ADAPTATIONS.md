# Local adaptations (this user's Muse)

Upstream: nakamo326/muse-space-async-jobs (MIT), cloned 2026-11-14 at the
user's request. Upstream files (SKILL.md, skill.yaml, templates/) are kept
verbatim; local additions live here and in templates-local/.

Avoid the upstream word "正本" in user-facing Japanese; say 「元の記録」
or name the concrete file/DB instead (user preference, 2026-11-13).

## 1. Xポスト置き場 (space: xposutozhi-kichang)

Mapping: the space DB is the record; marks (diagnose/draft/want/adopt) are
the jobs; setmark/setadoptmark emit one signal line to
~/hooks/state/xpost-signal.jsonl; a polling hook (60s) wakes a worker whose
prompt is the same sweep as the existing cron "x-post-place-pickup"
(listmarked oldest-first, process, write results back, report to the
"X投稿を再現する" chat 0cffa18c-c252-43b5-8f84-31078973622c only when at
least one card was processed).
Tier: B-plus. The 6h cron stays unchanged as the safety net (reconciler):
if a signal is lost, the cron still picks the mark up within 6 hours.
Status: see the dated log line at the bottom of this file.

## 2. ML training monitoring (gpu-01 / gpu-02 / gpu-03)

The same pattern with a different producer:

| Pattern role | Space version | ML version |
|---|---|---|
| Producer | Space action | Training script / wrapper on the GPU host |
| Record | Space DB | Run dir: status.json + train.log + artifacts |
| Signal | JSONL file append | signal.jsonl in the run dir; the VM hook polls it and status.json over SSH (Tailscale/tsproxy, see TOOLS.md) |
| Dispatcher | Polling hook (60s) | Polling hook (120-300s is enough; SSH per poll) |
| Worker | Agent sweeping listmarked | Agent verifying process, log pace, GPU, artifacts (templates-local/ml-worker-prompt.md) |
| Claim/lock | CAS + token | Never start a second heavy job; verify process before any restart |
| Retry | Manual requeue only | Manual only, except restart conditions pre-approved in the run plan |
| Reconciler | Low-frequency cron | Checkpoint cron per autonomous_work_checkpoints |

Templates: templates-local/ml_status.py (training-side status/signal
helper), templates-local/ml-training-watch.sh (hook),
templates-local/ml-worker-prompt.md (worker prompt).
Wake conditions are deliberately narrow: status transitions and stalls.
Epoch progress is reported by the checkpoint cron, not by wakes.

## Log

- 2026-11-14: Skill installed verbatim. ML templates added. Xポスト置き場
  signal-write probe requested (artifact edit in progress at time of writing).
