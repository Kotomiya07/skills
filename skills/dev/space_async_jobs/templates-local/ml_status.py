#!/usr/bin/env python3
"""Template helper for ML training jobs monitored with the async-jobs pattern.

Usage from the training side (on the training host, e.g. gpu-01):

    from ml_status import update_status, emit_signal
    update_status(run_dir, status="running", epoch=1, step=1200,
                  metrics={"loss": 0.42, "val_cer": 0.1101})
    emit_signal(run_dir)  # appends one line to <run_dir>/signal.jsonl

The run directory is the record that matters:
  - status.json is rewritten atomically (tmp file + rename) on every update.
  - signal.jsonl is an append-only hint for the watcher on the Muse VM.
    Losing signal lines must never lose work: the watcher always re-reads
    status.json, the log and the artifacts themselves.

Fields follow templates-local/ml-worker-prompt.md. Keep secrets, personal
data and long instructions out of both files.
"""
import json
import os
import time
import uuid


def update_status(run_dir, status, epoch=None, step=None, metrics=None,
                  artifact=None, note=None):
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "status.json")
    prev = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                prev = json.load(f)
        except Exception:
            prev = {}
    now = time.time()
    data = {
        "v": 1,
        "status": status,  # queued|running|finished|failed
        "epoch": epoch if epoch is not None else prev.get("epoch"),
        "step": step if step is not None else prev.get("step"),
        "metrics": metrics if metrics is not None else prev.get("metrics", {}),
        "artifact": artifact if artifact is not None else prev.get("artifact"),
        "note": note if note is not None else prev.get("note"),
        "started_at": prev.get("started_at") or now,
        "updated_at": now,
    }
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
    return data


def emit_signal(run_dir, event="changed"):
    line = {
        "v": 1,
        "event_id": str(uuid.uuid4()),
        "event": event,
        "ts": time.time(),
    }
    with open(os.path.join(run_dir, "signal.jsonl"), "a") as f:
        f.write(json.dumps(line) + "\n")
    return line
