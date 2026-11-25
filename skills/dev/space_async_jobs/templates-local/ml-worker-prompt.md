# ML training worker prompt (template)

Replace __PRODUCER__, __HOST_NAME__ (e.g. gpu-01), __HOST_IP__,
__REMOTE_RUN_DIR__ and __CHAT__ before registering the hook.

You were woken because the watcher for ML training job __PRODUCER__ saw a
relevant change. The wake reason and payload are hints only. Verify
everything from the record itself before reporting:

1. Before connecting, note in your report setup that you are connecting to
   __HOST_NAME__ (__HOST_IP__) by SSH (the user's standing rule: name the
   server when connecting).
2. Read __REMOTE_RUN_DIR__/status.json, the tail of train.log, the process
   list and nvidia-smi in one SSH session. Check the promised artifacts
   (checkpoint / best.pt / metrics file): existence, size, mtime.
3. Judge by state:
   - running + log advancing: report epoch, step, latest loss / val CER,
     start time and a rough remaining estimate only if the log supports it.
   - running + log stalled: apply the autonomous_work_checkpoints skill.
     A background torchrun job can look idle; check CPU and artifact
     mtimes. If the herdr session is merely waiting for a completion
     notice, nudge it. If the cause is unknown, do not restart; report
     the stall with its evidence.
   - finished: verify the final artifact and the test/val figures from
     the run's own records, then report the numbers. Do not trust a
     session's completion claim without the artifact.
   - failed: report the last error lines (OOM, traceback) verbatim in
     summary, and do not auto-retry. Requeue is a human decision, except
     where the run's plan pre-approved a specific restart condition.
4. Never start a second heavy job on the same host while one is running.
5. Report to __CHAT__ only when something changed or needs a decision;
   a routine epoch advance is not a report.
