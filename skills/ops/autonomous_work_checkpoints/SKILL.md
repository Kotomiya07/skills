---
name: autonomous_work_checkpoints
description: 停滞した自律作業や長時間ジョブをチェックポイントで点検し、安全に再開・報告するための手順を定義する。稼働すべきジョブやホスト再起動の確認、ログと約束成果物に基づく進捗・完了検証、無反応な委任タスクの引き取り、原因診断を経た安全な再起動と3分後の生存確認、および状況報告の方法を含む。長時間ジョブや委任作業の停滞を確認するとき、チェックポイント報告を行うとき、または異常終了したジョブを再開してよいか判断するときに使用する。
---

# Check stalled autonomous work

## Confirm what should be running

- List the jobs that should be active, the next step, and the signal that proves each job is alive.

- Read the program plan and name the step that should have finished since the last checkpoint.

- Treat a silent job as unproven and look for its process, log, and latest output before you judge it.

- Check whether the host rebooted by reading its uptime and the gap in the logs, and treat a short uptime with a log gap as a reboot that stopped every runner on that host.

## Check progress and records

- Compare the latest log timestamp and output against the expected pace and flag a job whose log has not advanced.

- Verify that each completed step left the record it promised before you call that step done.

- Treat a step with no promised record as incomplete even when its process exited cleanly.

## Reclaim an idle delegation

- Check a delegated worker directly when its lead session reports idle or waiting for a completion notice.

- Treat a completion notice as unproven until the promised artefact exists and read that artefact yourself.

- Take the unfinished step over in the lead session when the worker is idle with no fresh output and no promised record.

## Resume only when safe

- Diagnose an abnormal exit from its log and last output before you restart anything and record the cause.

- Restart only a job that is safe to restart, start it detached, and verify the detachment before you end the session.

- Restart with the exact launch command that last worked and is recorded in the program log, and do not invent a new launch command for a restart.

- Verify a restart after at least three minutes by checking that the process is still alive and its log has advanced, and do not call a restart done from an immediate start alone.

- When a restart dies within minutes, read its startup error before you try again and fix that error or return to the proven launch method, instead of repeating the same failing launch.

- Skip a restart when a job is already running, when its cause is unknown, or when a restart could duplicate work, and report the block instead.

## Report the checkpoint

- Report the job state, the progress since the last checkpoint, any restart you made, and any block you could not clear, with numbers and timestamps from the logs.

- Name the next step and the next checkpoint time so the user can see whether the program is moving without asking.

## Available connectors

- Use muse.connector_search to find other connectors and muse.skill_search to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with the custom connector setup skill, or build a custom connector.

## Alternatives for better results

- Add an explicit stop rule to the program plan, such as a maximum idle time or a missing record threshold, so a checkpoint has a clear trigger for action.

- Keep a short program log that lists each step, its start time, its output location, and its promised record.

- Set an explicit reclaim time when you delegate a step, so the lead takes the step over at that time instead of waiting for a notice.
