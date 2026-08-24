# sanitize-artifacts

生成物に残ったプロンプト、会話履歴、制作上の制約、修正過程などの不要な痕跡を取り除き、対象読者向けの独立した成果物へ整える Claude Code plugin です。

## Skill

- `sanitize-artifacts`：生成物の目的と技術的な正しさを保ちながら、制作過程に関するメタ記述や会話由来の不自然な表現を検査・修正します。

## 導入

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install sanitize-artifacts@kotomiya07-skills --scope user
```

導入後に Claude Code を再起動してください。
