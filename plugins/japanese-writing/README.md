# japanese-writing

自然な日本語、技術文書の論証、長文の認知リズムを改善する Claude Code plugin です。

## Skills

- `natural-japanese-writing`：簡潔性、明確性、具体性、一貫性を整え、AIらしい定型表現を抑えます。
- `japanese-tech-writing`：段落構成、論証の厳密さ、読み手の負荷、表記、冗長性を点検します。
- `cognitive-rhythm-writing`：認知モード、未回収の問い、文章の拍、段落の密度を調整します。使用時には `japanese-tech-writing` も参照します。

## 導入

```bash
claude plugin marketplace add https://github.com/Kotomiya07/skills --scope user
claude plugin install japanese-writing@kotomiya07-skills --scope user
```

導入後に Claude Code を再起動してください。

## 原文

このプラグインは、次の Gist を収録または Claude Code skill 向けに整形しています。

- k16shikano 氏の [`japanese-tech-writing`](https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d)
- k16shikano 氏の [`cognitive-rhythm-writing`](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432)
- YSRKEN 氏の [`自然な日本語文章を生成するためのライティングガイドライン`](https://gist.github.com/YSRKEN/66eefabf975b3e0ec8e947f8765bea0c)

スキル本文の著作権は原著作者に帰属します。原文の更新は自動では反映されないため、必要に応じて上記 Gist と収録内容を比較してください。
