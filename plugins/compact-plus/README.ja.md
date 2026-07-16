# compact-plus

[English README](./README.md) | [アーキテクチャ](./docs/architecture.ja.md)

Claude Code の圧縮アルゴリズムを置き換えず、`/compact` 前後の継続性を強化する透過型 plugin。圧縮前に構造化 checkpoint を保存・機密化し、公式 hook 経由で同じ session へ再注入する。

## 継続戦略

- **主経路: 同一 session checkpoint。** `PreCompact` で state を保存し、`SessionStart` の `compact|resume` で `additionalContext` へ再注入する。
- **fallback: 次 prompt の復旧案内。** 直接 restore が動かなかった場合だけ、`PostCompact` marker を `UserPromptSubmit` が1回 consumeする。
- **非常用: 明示 handoff。** compaction の反復や矛盾した context により同一 session の復旧が不十分な場合だけ、sanitized handoff を出力する。後継 session の起動や `/loop` 再登録は行わない。
- project documents、rules、plans、Git、Issue、PR、CI、artifact が正典。checkpoint は復旧証拠であり、権限を拡大しない。

## 保存内容

18見出しの state に以下を保存する。

1. 目的と完了条件
2. 正典文書
3. active plan
4. 現在 phase と tasks
5. task list
6. session decisions
7. 破棄した仮説
8. 制約と blocker
9. Git state
10. PR state
11. `/loop` state と承認範囲
12. worker topology
13. 呼び出し済み skill / slash command
14. 編集中 files
15. 失敗した試行
16. 次の決定的な操作
17. 未検証項目
18. recovery metadata

再取得可能な巨大 log、full diff、生成物は省略する。credential、Authorization/Cookie値、password、private key、URL credential、既知 token 形式、個人 email address は最終保存・再注入前に redaction する。

## 使い方

install 後は通常どおり `/compact` を実行する。manual compact と auto-compaction は同じ checkpoint 経路を使う。

任意操作:

- `/compact セキュリティ判断を残して` のような引数は state生成 LLM の priority guidance になる。
- `/compact-plus` は compact 前に checkpoint を手動で充実・検証する。
- `/compact-plus handoff` は checkpoint 検証後に非常用復旧 material を出力する。新規 session の起動、handoff読込、Git/Issue/PR/CI再検証、`/loop`やmonitor再登録は外部 supervisor またはユーザーの責務。

## 動作フロー

1. `PreCompact`
   - `precompact-transcript-backup.sh` が transcript backup を保存する。
   - `precompact-state-summary.sh` が transcript evidence を選択・squashし、設定済み LLM backend で rich state を作る。
   - `scripts/checkpoint.py precompact` が session ID、所有権、symlinkを検査し、旧見出しをmigration、18見出し順序を強制、Git/recovery metadataを補完、機密情報をredaction、64 KiBへ制限し、owner-only directoryへmode `0600`でatomic writeする。
2. `SessionStart` (`compact|resume`)
   - `scripts/checkpoint.py restore` が checkpoint を再検証し、restore event windowごとに1回 `additionalContext`へ注入する。
3. `PostCompact` / `UserPromptSubmit`
   - 短命な restore receipt により、hook順序に依存せず重複 recovery guidance を抑止する。
   - direct restore がなければ legacy marker により次 prompt で1回だけ復旧参照を注入する。
4. threshold reminder
   - 既存 warning marker が Active Plan、Current Phase and Tasks、最新 Session Decision の短い recitation を注入できる。

すべて fail open であり、checkpoint失敗は compaction を止めない。

## 前提

- Claude Code v2.x 以降
- Python 3
- `jq`
- rich state生成用の任意 LLM backend (`claude -p` または `codex exec`)

既定 primary は `claude -p --model claude-sonnet-5 --effort medium`、fallback は `codex exec --model gpt-5.3-codex-spark`。両方失敗しても deterministic hardener が最小 checkpoint を作る。

## Installation

このrepositoryをClaude Code marketplaceとして追加し、pluginをinstallする。

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install compact-plus@kotomiya07-skills --scope user
```

install後にClaude Codeを再起動する。後から更新する場合:

```bash
claude plugin marketplace update kotomiya07-skills
claude plugin update compact-plus@kotomiya07-skills --scope user
```

更新後もClaude Codeを再起動する。`npx skills add`ではskill filesだけが配置され、このpluginのhooksは導入されないため、完全な機能にはmarketplace経路を使う。

## 設定

`~/.claude/settings.json` の `env`、または session単位の shell export で上書きする。

| 環境変数 | default | 用途 |
|---|---:|---|
| `COMPACT_PLUS_PRIMARY_BACKEND` | bundled `claude -p` | primary command全体。空で無効化 |
| `COMPACT_PLUS_FALLBACK_BACKEND` | bundled `codex exec` | fallback command全体。空で無効化 |
| `COMPACT_PLUS_TRANSCRIPT_MODE` | `incremental` | `incremental` / `head-tail` / `tail` |
| `COMPACT_PLUS_TRANSCRIPT_HEAD_TURNS` | `5` | head turn上限 |
| `COMPACT_PLUS_TRANSCRIPT_TAIL_TURNS` | `25` | tail turn上限 |
| `COMPACT_PLUS_TRANSCRIPT_HEAD_KB` | `10` | head byte cap (KiB) |
| `COMPACT_PLUS_TRANSCRIPT_TAIL_KB` | `40` | tail byte cap (KiB) |
| `COMPACT_PLUS_INCREMENTAL_REFRESH` | `10` | full rebuild周期。`0`で無効 |
| `COMPACT_PLUS_MAX_OUTPUT_TOKENS` | `4096` | backend対応時の出力上限 |
| `COMPACT_PLUS_SQUASH_ENABLED` | `1` | tool output squash |
| `COMPACT_PLUS_SQUASH_READ_LINES` | `100` | Read/Grep/Glob threshold |
| `COMPACT_PLUS_SQUASH_BASH_CHARS` | `500` | Bash output threshold |
| `COMPACT_PLUS_TWO_PASS` | `1` | LLM self-critique hint |

backend command 内では `$SYSTEM_PROMPT`、`$SESSION_ID`、`$TRANSCRIPT_PATH`、`$MAX_OUTPUT_TOKENS` を参照できる。

`COMPACT_WARN_THRESHOLD` は外部 statusline producer の設定であり、この plugin の所有ではない。

## state / marker files

| path | 用途 |
|---|---|
| `${TMPDIR}/claude-compact-state/<session_id>.md` | hardened same-session checkpoint |
| `${TMPDIR}/claude-compact-handoff/<session_id>.md` | 明示 emergency handoff |
| `${TMPDIR}/claude-compact-restore-claims/*.claim` | 重複注入 guard |
| `${TMPDIR}/claude-compact-restored/<session_id>.md` | 短命 direct-restore receipt |
| `${TMPDIR}/claude-compacted/<session_id>` | legacy next-prompt fallback marker |
| `${TMPDIR}/claude-compact-state-offset/<session_id>` | incremental offset |
| `${TMPDIR}/claude-compact-state-counter/<session_id>` | refresh counter |

## Development Checks

repository rootから実行する。

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool plugins/compact-plus/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/compact-plus/hooks/hooks.json >/dev/null
python3 -m py_compile plugins/compact-plus/scripts/checkpoint.py
bash -n plugins/compact-plus/hooks/*.sh plugins/compact-plus/tests/*.sh
bash plugins/compact-plus/tests/checkpoint-hooks.sh
```
