# skills

Kotomiya07 が管理する Claude Code plugin の配布リポジトリです。現時点では `compact-plus` のみを収録しています。

## Plugins

| Plugin | Version | 概要 |
|---|---:|---|
| [`compact-plus`](./plugins/compact-plus/) | 1.1.0 | `/compact` 前後で構造化 checkpoint を保存・再注入し、同一 session の継続性を強化します。 |

## compact-plus の導入

### Claude Code marketplaceから導入

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install compact-plus@kotomiya07-skills --scope user
```

導入後に Claude Code を再起動してください。以降は通常どおり `/compact` を使えます。manual compact と auto-compaction の両方で同じ checkpoint 経路が動作します。

### 更新

```bash
claude plugin marketplace update kotomiya07-skills
claude plugin update compact-plus@kotomiya07-skills --scope user
```

更新後も Claude Code の再起動が必要です。

### ローカルcloneから導入

```bash
git clone https://github.com/Kotomiya07/skills.git
claude plugin marketplace add /absolute/path/to/skills --scope user
claude plugin install compact-plus@kotomiya07-skills --scope user
```

既に同名marketplaceを登録している場合は、先に `claude plugin marketplace remove kotomiya07-skills` で削除してから登録し直してください。

## skills installerについて

`compact-plus`は`PreCompact`、`SessionStart`、`PostCompact`、`UserPromptSubmit` hookを含むClaude Code pluginです。`npx skills add`でskill部分だけを配置してもhookは導入されないため、完全な機能には上記marketplace手順を使用してください。

`gh skill`はGitHub CLIの標準コマンドではないため、このリポジトリの導入手順には使用しません。

## 詳細

- [compact-plus README](./plugins/compact-plus/README.md)
- [compact-plus 日本語README](./plugins/compact-plus/README.ja.md)
- [Architecture](./plugins/compact-plus/docs/architecture.md)
- [アーキテクチャ](./plugins/compact-plus/docs/architecture.ja.md)
- [Security policy](./plugins/compact-plus/SECURITY.md)

## 由来とライセンス

`compact-plus`は[`u-ichi/compact-plus`](https://github.com/u-ichi/compact-plus)を元に、checkpoint保存・再注入・redaction・handoff復旧を強化した派生版です。

リポジトリ全体の新規部分は[`LICENSE`](./LICENSE)のMIT License（Copyright (c) 2026 Kotomiya07）で配布します。`compact-plus`の原著作者のcopyright noticeは[`plugins/compact-plus/LICENSE`](./plugins/compact-plus/LICENSE)に保持しています。
