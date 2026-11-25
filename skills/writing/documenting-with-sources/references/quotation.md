# 引用書式リファレンス

本リファレンスは、`documenting-with-sources` における引用ブロックの詳細な書式規約を定める。

参照形式（`[label (YYYY/MM), location]`、裸番号 `[1]` 禁止）、引用と地の文の分離、外部情報源の引用に常にフェンス付きコードブロックを使うこと（`>` 禁止）、および異言語引用時に原文と訳を同じコードブロック内に配置する原則については、本体 [SKILL.md](../SKILL.md) を参照する。

## 1. 引用ブロックの構造

引用ブロックは次の形をとる。

- 開始コードフェンス
- 原文
- 空行1行
- 執筆者の作業言語への訳（情報源が異なる言語のときのみ）
- 終了コードフェンス
- 終了フェンス直後の行に出典参照 `[label (YYYY/MM), location]`

詳細ルール:

- 原文と訳の間は空行1行で区切る。
- 原文と訳の間に水平線（`---`）を入れてはならない。
- 訳をコードブロックの外に出してはならない。原文の横に括弧書きで入れてはならない。
- 出典参照は終了フェンスの次の行に独立した1行として置く。決してコードブロック内に入れてはならない。

## 2. 具体例

### 2.1 同一言語の引用

情報源と執筆者の作業言語が同じ場合、訳は不要である。

```
Composability is the property by which a system's behaviour is determined by the behaviour of its parts and the rules under which they are combined.
```

[example-handbook (2026/04), Section 2.1]

### 2.2 異言語の引用

情報源が執筆者の作業言語と異なる言語の場合、同じコードブロック内に別段落として訳を置く。

```
Le sens d'une expression complexe est déterminé par le sens de ses constituants et par les règles qui les combinent.

The meaning of a complex expression is determined by the meaning of its constituents and the rules that combine them.
```

[example-handbook (2026/04), Section 2.1]

### 2.3 プロンプトテンプレートの引用

プロンプトテンプレートにも同じルールを適用する。コードブロックで囲み、終了フェンスの後に出典参照を置く。

```
Human: You are an assistant who summarises research papers. The paper is enclosed in <paper> tags. Produce a summary enclosed in <summary> tags. <paper>P</paper> Assistant:
```

[example-prompt-library (2026/04), template 03]

### 2.4 訳側でのロール表記の短縮

プロンプトテンプレート（Human/Assistant 形式）を翻訳するとき、認知負荷を下げ、原文と訳を一目で見分けやすくするため、訳側ではロール表記を短縮してもよい。

- `Human:` → `H:`
- `Assistant:` → `A:`

原文側は短縮せずにそのまま保つ（`Human:` / `Assistant:` をフル表記）。チャットテンプレートの末尾の `Assistant:`（応答が始まる位置を示す箇所）は構造的な意味を持つため、訳側でも `Assistant:` のまま残してよい。

## 3. アンチパターン

### アンチパターン1 — 引用記法（`>`）の使用

`>` で始まる行は外部引用として不可。必ずコードブロックで囲む（本体 [SKILL.md](../SKILL.md) 参照）。

### アンチパターン2 — コードブロック外の訳

```
Composability is the property by which ...
```

訳がコードブロックの外に地の文として書かれている。[example-handbook (2026/04), Section 2.1]

修正: 原文と訳を同じコードブロック内に入れ、空行1行で区切る。

### アンチパターン3 — 原文の横に括弧書きの訳

```
Composability is the property by which ... (括弧内のインライン訳 ...)
```

[example-handbook (2026/04), Section 2.1]

修正: 原文と訳は同じコードブロック内の独立した段落とし、空行1行で区切る。

### アンチパターン4 — コードブロック内の出典参照

```
Composability is the property by which ...

ここに訳 ...
[example-handbook (2026/04), Section 2.1]
```

修正: 出典参照は終了フェンスの次の行に独立した1行として置く。

### アンチパターン5 — 裸の番号による出典参照

```
Composability is the property by which ...

ここに訳 ...
```

[1]

修正: 情報源を直接識別できるラベル（著者略称または媒体名）を使う。

### アンチパターン6 — 原文と訳の間の水平線

```
Composability is the property by which ...
---
ここに訳 ...
```

[example-handbook (2026/04), Section 2.1]

修正: 原文と訳は空行1行で区切る。水平線は使わない。

## 4. 適用範囲

本リファレンスは引用の書式のみを定義する。*いつ*引用するか（Assertion-Evidence の順序、どのラベルを使うかなど）は呼び出し元スキルが決める。

- `survey`: Assertion-Evidence 順序——まず地の文で主張を述べ、その後で引用によって裏付ける。`label` 欄には媒体名または情報源名を入れる。
- `paper-details`: 対象論文への参照は著者を省略し、位置情報のみを使う（`[p.X, Section Y.Z]`）。他文献への参照は `[author-short (YYYY/MM)]` を使う。
