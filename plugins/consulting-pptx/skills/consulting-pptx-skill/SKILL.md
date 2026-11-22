---
name: consulting-pptx-skill
description: スライド設計規約 slide-rules.md を核に、経営会議品質のスライドを作るスキル。規約は工程ごとに必要な節だけを scripts/rules.py で引き、規約を満たすことを確かめた部品（new_deck.py --list の20種類）で組み、check_deck.py・check_layout.mjs の機械チェック FAIL 0 で仕上げる。A0/A1 縦のポスターも同じ規約・機械チェックで作れる（slide-rules §10）。既存の PowerPoint 資料を渡され、そこへ差し込むページを PPTX で求められたときだけ、その資料のマスターの上に直接組む（slide-rules §8.7）。トリガー例:「コンサル品質のスライドを作って」「A0 のポスターを作って」「学会発表のスライドを作って」「規約に沿ったデッキで」「この pptx に足すページを同じ書式で」。
---

# コンサル型スライド作成スキル

規約の正典は `references/slide-rules.md`。全文は読まず、**工程ごとに `scripts/rules.py --phase <工程>` の要点を切らずに読み、根拠が要る項だけ `--sec 4.12` で引く。** 成果物は HTML（スライドは 16:9・1 section = 1スライド、ポスターは A0/A1 縦・1 section = 1枚）と `snapshot.py` で印刷した PDF。

| 工程 | 読む・使う |
| --- | --- |
| 1. 定義 | `--phase plan`、`references/working-practices.md` |
| 2. 調べる | 一次情報。確かめた数字は `sources.md` に控える |
| 3. ストーリーライン | `new_deck.py --list` |
| 4. 骨組み | `new_deck.py --parts ...`（作りを見るときだけ `--show b09`） |
| 5. 中身を書く | `--phase build`、形に応じて `chart` / `table` / `process` |
| 6. 文章を仕上げる | `--phase text`、`references/ai-smell-lexicon.md` |
| 7. 検査と直し | `check_all.py`、指摘に出た節だけ `--sec` |
| 8. 最後の確認 | `--phase check`、`snapshot.py` の PDF と画像 |
| 9. フレッシュアイ・レビュー | `references/content-review-prompt.md` |

- 工程1で足して読むもの：`local/`（git 管理外）の `slide-rules.local.md`・`forbid.txt`・`old-colors.txt`（local が優先。他社の書式で組むときは check_deck に `--brand none`）／テーマが AI・業務の自動化なら `references/jinba-context.md`／PPTX にするなら `--phase pptx`／登壇用ピッチなら `--phase pitch`／ポスター（A0/A1 縦）なら `--phase poster`（§10）と `templates/poster_parts.html`・`scripts/new_poster.py`／学会発表のデッキなら `references/academic-presentation.md`（構成・タイトル・情報量の作法。規約とぶつかる点は学会発表ではそちらを優先）。

## 手順

1. **定義する**: 目的・成果物の定義・スコープ IN/OUT を3〜5行で決める。誰に・どの会議で・何を判断してもらうかが分からなければ聞く。聞けなければ前提を置いて報告に書き、デッキにせず1枚の論点整理で出す。
2. **調べる（必須）**: 載せる数字・事例・固有名詞は一次情報で確かめ、`sources.md` に1行ずつ控える（数字・何の数字か・出典名・URL・時点）。試算は `python3 -c` で計算し、式・入力・結果を貼る。見つからない数字は作らず「要確認」と書く。`sources.md` と `qa.md` はデッキと同じフォルダに置く。
3. **ストーリーラインを書く**: 1枚1行の主張の列を書き、材料の関係から形を決め（§5.12）、最後に部品を選ぶ。型どおりの並びにせず（§4.103）、薄いページは隣とまとめる（§5.13）。各ページの「タイトル／結論／載せる内容／見せ方」を文章で出し、合意してから組む。
4. **骨組みを作る**: `python3 scripts/new_deck.py --parts b01,m01,b09:axb,m05,b10 --title "資料名" -o mydeck.html`。合う部品が無ければ `--list --all` を見るか、規約の範囲で自由に組む。
5. **中身をまとめて書く**: 伏せ字（`Text N`・`ラベル N`・`パーツNN｜…`）を全部実物に置き換えた完成版を1回の Write で書く。数字は `sources.md` の値だけを使う。
6. **文章を仕上げる**: タイトルを上から通し読みし、要るページだけ Edit する。
7. **検査して直す**: `python3 scripts/check_all.py mydeck.html --sources sources.md`（`PLAYWRIGHT_MODULE_DIR` が無いときだけ `npm run setup`）。指摘の節を `--sec` で引き、ページごとにまとめて形で直す（直し方は `working-practices.md`）。FAIL 0 まで回す。WARN も直すのが既定で、規約の例外に当たるものだけ § を qa.md に書いて残す。
8. **PDF で全ページを見る**: `python3 scripts/snapshot.py mydeck.html` の PDF と画像を全部見て（pdftoppm は別途入れる）、§8 の目視の基準で確かめた結果を `qa.md` にページごとに書く。直したら `check_all.py` を回し直す。
9. **フレッシュアイ・レビュー**（速度優先と言われたとき以外）: `content-review-prompt.md` を作り方を伏せて別エージェントに渡し、採用した指摘を直して検査を回し直す。1ラリーで止めて、続けるかを聞く。

## ポスター（A0/A1 縦）を作るとき

スライドの手順に追加する形で使う。既定は 16:9 のまま。規約は `--phase poster`（§10: 判型・文字サイズ下限・読み順・1ポスター=1メッセージ）を読み、部品は `templates/poster_parts.html` の01〜09（タイトル帯・結論ボックス・本文セクション・2段/3段グリッド・図とキャプション・軸つき表・数字カード・フッター）。1ポスター = `section.poster` 1つ。

```bash
python3 scripts/new_poster.py --list                                     # パーツ01〜09
python3 scripts/new_poster.py --size a0 --parts 01,02,03,04,06,09 --title "題名" -o myposter.html   # a0（既定）/ a1
python3 scripts/check_deck.py myposter.html          # FAIL 0（判型・文字サイズ下限も検査）
node scripts/check_layout.mjs myposter.html          # はみ出し・重なり・版面の空き（大きさの揃いの検査はポスター対象外）
python3 scripts/snapshot.py myposter.html            # PDF 化。pdfinfo で1ページ・A0/A1 の寸法を確かめる
```

- 判型は HTML の `@page` が決める。`pdfinfo` が無ければ PDF の /MediaBox から mm 寸法を読む（A0 は 841×1189、A1 は 594×841）
- 目視は低解像度の画像で足りる（A0 をそのまま画像にすると巨大になる。長辺は 1200px 程度まで縮める）
- PPTX は「PPTX で」と言われたときだけ: `python3 scripts/html_to_pptx.py myposter.html`（スライド寸法が A0/A1 になる。§10.7）

## 学会発表のデッキでは

学会・研究会の発表デッキは、手順に加えて `references/academic-presentation.md` を工程1で読む。要点は、背景 → 課題 → 目的 → 着目点・仮説 → 手法 → 結果 → 結論 を「つなぐ言葉」でつなぐこと、スライドタイトルを項目名でなく要約の一文にすること、1スライド1データと図の近くに結論を置くこと、「ご清聴ありがとうございました」だけで終わらせずまとめで終えること。文字サイズの目安（タイトル 32–36 pt 等）もそちらにあり、規約の数値とぶつかる場合は学会発表ではそちらを優先する。

## PowerPoint（.pptx）が要るとき

HTML で仕上げ、「PPTX で」と言われたときだけ最後に1回 `html_to_pptx.py` で変換する。ポスターの PPTX も手順は同じで、スライドサイズは最初の `section.poster` の実寸から決まる（§10.7）。既存の資料へ差し込むページは、その資料のマスターの上で組む（`measure_deck.py` → `deck_pptx.py`）。詳しくは `--phase pptx`。

## 本スキル使用の注釈

裏表紙（b10）の出典行に「本資料は consulting-pptx-skill（github.com/carnot-tech/consulting-pptx-skill）で作成」が既定で入っている。ツール名を置けるのは最終ページの出典行だけで、他のページに出ると check_deck が FAIL にする。

## スキルを育てる

自分の組織の規約は本体を書き換えず `local/` に足す。どの組織でも効く指摘・誤検知は、納品後に一度だけ PR を提案する。手順は `working-practices.md` の「スキルを育てる」、PR に入れないものは `CONTRIBUTING.md`。
