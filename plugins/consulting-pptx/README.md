# consulting-pptx

スライド設計規約 `slide-rules.md` を核に、経営会議品質のスライド（HTML 16:9 → PDF／PPTX）と A0／A1 縦ポスターを作る Claude Code plugin です。規約違反の機械チェック（`check_deck.py`、`check_layout.mjs`）と、工程ごとに規約を引く仕組み（`scripts/rules.py`）を含みます。

## Skill

- `consulting-pptx-skill`：規約を読んで組み、機械チェック FAIL 0 で仕上げる手順を提供します。
- ポスター対応：`scripts/new_poster.py` と `templates/poster_parts.html`（パーツ9点）で A0／A1 縦ポスターを組み、判型と文字サイズ下限も機械チェックします（規約 §10）。
- 学会発表対応：`references/academic-presentation.md` に、学会発表デッキ専用の構成・タイトル・情報量の作法をまとめています。

## 導入

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install consulting-pptx@kotomiya07-skills --scope user
```

導入後に Claude Code を再起動してください。PDF 化とレイアウト検査には Node.js と Chromium headless shell が要ります（スキル内の `npm run setup`）。

## 由来

[`carnot-tech/jinba-consulting-pptx-skill`](https://github.com/carnot-tech/jinba-consulting-pptx-skill)（Jinba のメンバーによる公開スキル）の 2026-11-19 時点の HEAD（`3411e47`）を土台に、Kotomiya07 が次の2点を加えた派生版です。

1. **ポスター対応の移植**：利用者の Mac 上で独自に追加していたポスター対応（`new_poster.py`、`poster_parts.html`、規約 §10、判型・文字サイズの機械チェック、テスト13件）を、上流の新しい版へ移植しました。上流で削除された資産（SuperTemplate、型カタログ、型カタログ PDF）は戻していません。ポスターのパーツ一覧は §10 が兼ねます。未移植は `check_layout.mjs` の px 閾値の倍率換算のみで、ポスターでは px の絶対値で測る細かい指摘が 16:9 基準のまま出る場合があります（§10.6 に明記）。
2. **学会発表の作法の追加**：大西真駿「学会発表で役立つ発表スライド作成のヒント」（株式会社リバネス・中高生研究者向け資料、Speaker Deck 公開 2021-12-22）の内容を要約・再構成し、`references/academic-presentation.md` として追加しました。転載ではありません。

検証：スキル内のテスト 305 件が全て合格しています（上流 HEAD 単体の 292 件＋ポスター 13 件。Chrome 本体との PDF 比較テスト1件は、検証環境に Chrome 本体が無いため skip）。

## ライセンス

このプラグインのスキル本体は、上流のライセンス **PolyForm Noncommercial 1.0.0** の対象です。`skills/consulting-pptx-skill/` 内の `LICENSE`、`LICENSING.md`、`LICENSES/MIT.txt`（変更前の版の MIT 表示）をそのまま保持しています。無償の範囲・評価利用・商用ライセンスが必要な使い方は `LICENSING.md` を確認してください。このリポジトリ全体の MIT License（Kotomiya07 の新規部分向け）は、このプラグインのスキル本体には適用されません。
