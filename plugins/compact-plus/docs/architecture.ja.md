# compact-plus アーキテクチャ

[English architecture](./architecture.md) | [README](../README.md) | [日本語 README](../README.ja.md)

compact-plus は Claude Code の公式 hook で context compaction を補強する。内部 compaction algorithm や prompt は置き換えない。主方式は構造化 checkpoint を同じ session へ戻すことであり、新規 session への handoff は明示的な非常用経路に限定する。

## 1. 目的と境界

### 目的

- goal、判断、破棄仮説、残作業、実行状態を compacted conversation の外へ保存する。
- `compact` / `resume` 直後に、次の user prompt を待たず復旧証拠を再注入する。
- 自律開発に必要な Git、PR、`/loop`、worker、validation、承認範囲を保持する。
- project documents と live external state を正典として維持する。
- 秘密情報を redactionし、bounded fileを強制し、失敗時も compaction を止めない。

### 対象外

- Claude Code の compaction algorithm や built-in summary の置換。
- checkpoint を commit、push、PR作成、merge、deployなど共有状態変更の承認として扱うこと。
- 後継 session の自動起動、handoff読込、`/loop`・monitor・background processの自動再登録。
- full transcript、巨大 log、full diff、再生成可能な出力の checkpoint 保存。

## 2. 継続レイヤー

### 2.1 同一 session checkpoint（主方式）

`PreCompact` が rich state を生成し、deterministic checkpoint hardener が最終化する。source が `compact` または `resume` の `SessionStart` で検証し、`additionalContext` へ注入する。

復元 state は recovery evidence である。agent は記録された正典を再読し、未検証項目と live state を確認してから行動する。

### 2.2 次 prompt recovery（fallback）

`PostCompact` が one-shot marker を書く。直接 `SessionStart` restore が動かなかった場合だけ、`UserPromptSubmit` が marker をconsumeし、checkpoint、active plan、original instruction sourceへの参照を注入する。

短命 restore receipt が direct restore 成功時の重複注入を抑止する。receipt方式は `SessionStart` と `PostCompact` の実行順に依存しない。

### 2.3 Emergency handoff（明示操作）

`checkpoint.py prepare-handoff --session-id <id>` が `${TMPDIR}/claude-compact-handoff/` に sanitized handoff を出力する。compaction反復、summary矛盾、重大な context drift により同一 session 復旧が不十分な場合だけ使う。

handoff は新規 session を起動せず、承認範囲も拡張しない。supervisorまたはユーザーが後継を起動し、handoff読込、Git/Issue/PR/CI再検証、`/loop`と非永続monitorの再登録を行う。

## 3. Runtime Flow

1. `PreCompact` が transcript をbackupする。
2. `precompact-state-summary.sh` が incremental / head-tail / tail evidenceを選び、巨大tool outputをsquashする。
3. 設定済み LLM backend が18見出し rich stateを生成する。backend失敗は許容する。
4. `checkpoint.py precompact` が最終 checkpointを検証または作成する。
   - strict session ID validation
   - owner-only directory、regular-file ownership、symlink拒否
   - 旧10見出しmigration
   - 18見出しexact order
   - Git / recovery metadata fallback
   - sensitive-data redaction
   - 64 KiB cap
   - mode `0600` atomic writeとreadback
5. `SessionStart` (`compact|resume`) が `checkpoint.py restore` を実行する。
6. malformed、oversized、incomplete、unowned、symlink stateを拒否し、valid stateをevent windowごとに1回注入する。
7. restore成功を記録し、legacy next-prompt経路の重複contextを抑止する。
8. direct restoreがなければ、`PostCompact` / `UserPromptSubmit` が1回だけfallback recoveryを注入する。

すべてのhookはfail openする。

## 4. State Contract

正確な順序:

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

旧 `## Current Phase` と `## Recovery Notes` の内容は対応する新見出しへmigrationする。欠落情報は発明せず `Not verified` とする。

`## Loop State and Approval Scope` はrecurrence、wake signal、現在の明示承認境界を記録する。過去の無関係な操作から権限を推論してはならない。

## 5. Security Model

hook JSON、transcript excerpt、LLM output、既存 checkpoint、Git output、環境由来pathはすべてuntrusted inputとして扱う。

制御:

- hook input: 最大1 MiB
- checkpoint / handoff: 最大64 KiB
- Git status capture: 最大8 KiB
- session ID: `[A-Za-z0-9][A-Za-z0-9_-]{0,127}`
- directory: current-user ownership、mode `0700`、directory symlink拒否
- file: current-user regular file、symlink拒否、mode `0600`
- write: same-directory temporary file、`fsync`、atomic replace、readback
- redaction: secret assignment、Authorization/Cookie header、Bearer/known token、private-key block、URL credential、email address

rich stateがmalformedまたはoversizedなら、危険な内容を保持せず最小deterministic checkpointへ置換する。

## 6. 正典の優先順位

復旧判断では次を優先する。

1. 現在の明示 user instruction と durable approval policy
2. project rules、spec、plan、ADR、tests
3. live Git、Issue、PR、CI、artifact、process state
4. checkpoint または emergency handoff
5. compacted conversation summary

checkpoint は正典を指し示せるが、正典を上書きしない。

## 7. Files と Ownership

| Path | Writer | Reader | 用途 |
|---|---|---|---|
| `${TMPDIR}/claude-compact-state/<session_id>.md` | rich generator / hardener | restore / fallback | hardened checkpoint |
| `${TMPDIR}/claude-compact-handoff/<session_id>.md` | explicit handoff command | successor / supervisor | emergency recovery material |
| `${TMPDIR}/claude-compact-restore-claims/*.claim` | restore | restore | duplicate injection guard |
| `${TMPDIR}/claude-compact-restored/<session_id>.md` | restore | PostCompact/UserPromptSubmit | short-lived success receipt |
| `${TMPDIR}/claude-compacted/<session_id>` | PostCompact | UserPromptSubmit | fallback trigger |
| `${TMPDIR}/claude-compact-state-offset/<session_id>` | rich generator | rich generator | incremental offset |
| `${TMPDIR}/claude-compact-state-counter/<session_id>` | rich generator | rich generator | refresh cadence |
| `${TMPDIR}/claude-active-plan/<session_id>` | external plan hook | generator / fallback | active-plan pointer |

## 8. Configuration Boundary

compact-plus は `COMPACT_PLUS_PRIMARY_BACKEND`、`COMPACT_PLUS_FALLBACK_BACKEND`、transcript selection limits、output squash、refresh cadence、output token cap、two-pass guidanceを所有する。外部statusline producerが `COMPACT_WARN_THRESHOLD` を所有する。

pluginは `PreCompact`、`PostCompact`、`SessionStart`、`UserPromptSubmit` を使う。plugin有効時、global settingsへcheckpoint hookを重複登録する必要はない。
