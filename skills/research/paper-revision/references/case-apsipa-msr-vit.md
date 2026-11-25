# 適用例: APSIPA / MSR-ViT 論文（査読コメント分析の具体例）

> 本節は、APSIPA 論文「MSR-ViT (Cross-Scale Conditioning for Full-Page Historical Japanese Character Recognition)」の v2→v3→v4 にわたる査読コメント（共著者 Fujita 氏による校閲、計78件）から得られた案件固有の具体例・語彙・参照情報をまとめたものである。他論文へ適用する際は本体ルールを優先し、本節は具体例の参考として扱う。

## 案件固有の英語表現例

- **長い名詞句の分解例**:
  - NG: `dense full-page historical Japanese character recognition`
  - OK: `full-page character recognition in historical Japanese documents`
- **査読者コメント付きの語彙置換例**:
  - `protocol` → `procedure`, `method`, `rule`（「protocolは通信手順のように、相手がある規約だと感じる」）
  - `report` (動詞) → `describe`, `present`（「論文でreportという単語をあまり見ない」）
  - `diagnostics` / `diagnostic` → `examinations`, `examines`, `results`（「健康・医療のように感じる」「意味がわからない」）
  - `canvas` → `image`
  - `used` (encoder の共有) → `shared`
- **接続詞・数値表現・動詞の例**:
  - `unless` に関する指摘: 「unlessは『もし〜がなかったら』という条件付け。理由付けには because not では？」
  - `a +3.03 point gain` の回避例（OK例）: `..., corresponding to improving recognition for six characters in a 200-character page.`
  - `is handled` → `pixels are identified`
- **査読者が提示した言い換え例**:
  - `separates recognition quality from tile-boundary artifacts` → `reduces tile-boundary artifacts and makes recognition quality higher`
  - `reported BCA results` → `results in BCA metric`
  - `letterbox` という語は使うか再検討する（一般的でない可能性）。本文では `pad to a square canvas` 系の表現に統一済み。

## 案件固有の論理・説明・数式例

- **用語定義**:
  - `grid cell` は v2 で4回「わからない」と指摘された最大の地雷。v4 では `token cell` に統一されたが、定義の明示は必須（対象用語例: `grid cell`, `token cell`, `valid cell`, `retained cell`）。
  - `repetition mark` への指摘: 「語や単語が2度繰り返す時の省略記号であると書いてください」。
- **未定義記号の例**:
  - `\hat{m}_{ij}`, `m_bar_u`, `Ω_valid`, `κ_u` など（指摘: 「`\hat{m}_{ij}` が未定義」）。
- **操作の動機説明例**:
  - foreground を 32×32 class grid へ average-pool する理由 → 「foreground estimation は pixel 単位、class identification は grid 単位なので、その大きさを調整するため」と書く。
  - `deterministic reconstruction rule` と書くなら「deterministic だと何が良いのか」を説明する。
- **主題先行の指摘（C19）と模範例**:
  - 指摘（C19）: 「述べたいことの対象を明確に伝えてから、その性能や理由を述べるべき。そうでないと、読む人は何を言っているのかわからない。」
  - 模範例（査読者提示）:
    > At lower resolutions, the injection from the downward resolution has a negative impact to the recognition accuracy. This is because the lower resolution images are too noisy to support the recognition at the upward resolution. In contrast, the final 2048 resolution holds rich details of the local image, then the global information could help the recognition from a contextual viewpoint.
- **数式の直感的説明と一致確認例**:
  - 指摘: 「このあたりが理解できません。もっと簡単に説明しないと reviewer が評価できない。」
  - box-level voting (式8-10) のような複雑な部分は、式の前に1〜2文で直感的説明を置く。
  - KL divergence が何の確率間の計算かなど、式の意味と本文説明の一致を確認する。

## 案件固有の冗長性・構成例

- **v4 での重複文削除（v4 で「削除」指摘が急増した重複文除去フェーズ）**:
  - v4 C11/C12: 「先頭行と同じなので削除」「削除」。
- **表の定義先行（C20）**:
  - 各行・各列ラベルの定義例: Non-overlap / Overlap-average / Center-crop が何か、BCA 列・Boundary BCA 列が何かを結果の解釈より前に述べる。
- **不要文の再評価例**:
  - CER の読み順正規化の話を実験節で繰り返す等、Related Work か Method で既に述べていれば実験節では削る。

## 案件固有の用語統一・座標系例

- **用語統一**:
  - `head` か `branch` か → どちらかに統一（査読者「統一」）。v4 では `branch` 系に寄せている。
  - `tile` / `pixel` / `cell` の混同回避: v2 で `tiles` → `pixels`、`cells` → `pixels` の修正が複数入った。
  - `conditioning` と `injection` の使い分け（査読者「Conditioning ですか? Injection とか」）。機構名と動作を区別する。
- **座標系・添字の整合**:
  - 局所座標 `a` を全体 `M` で合計する混同への指摘: 「a という座標系はlocalでは？それをMで合計するのはおかしい」。
  - 添字の役割を Method 冒頭で定義する例: `s` 解像度, `a` タイル位置, `u` token/cell, `(i,j)` pixel。

## 案件固有の実験・データ記述例

- **データ分割**:
  - CODH が提供したのか著者が分けたのかを明示する。
  - 査読者の模範文:
    > We divide the pages in the dataset into train, validation and test data groups according to the book unit to avoid leakage from the page style, cramped hand writing, printing conditions within the same book.
- **test set の記述**:
  - 指摘: 「こう書くと test group だけが特別な特徴を持っているように読める」。
- **設計判断の補足例**:
  - 「one training run selected by validation top-5 class accuracy」のような記述では、なぜ top-5 か、なぜ 1 run かが伝わるよう補足する。
