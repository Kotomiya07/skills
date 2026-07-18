# semantic-generation

語を決める前に指示対象と役割を対応表へ固定し、曖昧な造語が設計、調査報告、命名、コード識別子へ波及するのを防ぐ Claude Code plugin です。

## Skill

- `semantic-generation`：本文より先に referent table を独立ファイルとして作成し、その表に基づいて本文と識別子を書く手順を提供します。
- `references/referent-before-label.md`：対象文書で常時守る禁則と問題時の処理を定義します。

## 導入

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install semantic-generation@kotomiya07-skills --scope user
```

導入後に Claude Code を再起動してください。

## 原文

Yuichi Uemura（[@u1](https://x.com/u1)）氏の X Article「[codexの独自用語乱立･曖昧問題への対策](https://x.com/u1/status/2078414824917156228)」で公開された `semantic-generation` skill と `referent-before-label` rule を、Claude Code の skill 形式へ整形しています。

Claude Code 向けの主な調整は、frontmatter の修正、Codex 固有の wiki link と runtime summary 名のClaude Code向け変更、Markdown表の区切り行追加、SHA-256コマンドの環境別表記、記事に同梱されていない `terminology` rule の注記です。手順、禁則、例、問題時の処理は原文を保持しています。
