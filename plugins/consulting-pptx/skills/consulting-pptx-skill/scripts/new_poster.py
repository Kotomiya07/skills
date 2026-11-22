#!/usr/bin/env python3
"""
new_poster.py — templates/poster_parts.html から必要なパーツだけを取り出し、A0/A1 縦ポスター（HTML 1 枚もの）を組み立てる。

  python3 scripts/new_poster.py --size a0 --parts 01,02,03,04,06,09 --title "題名" -o myposter.html

  パーツ番号 = poster_parts.html の「═══ パーツNN: 名前（」コメントの NN（--list で一覧）
  並べた順に section.poster の中へ縦に積む。省略時は全パーツ
  --size  a0（841×1189mm、既定） / a1（594×841mm、--k:0.7064）
  --title <title> とタイトル帯（パーツ01）の h1 に差し込む。省略時は <title> が「ポスター」、h1 はサンプル文のまま
  --list  パーツ番号と名前の一覧を表示して終了

判型は :root の --poster-w / --poster-h / --k と、@page の size（直前コメントが書き換え位置）の 2 か所を同じ値に揃える。
"""
import argparse, html, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "templates" / "poster_parts.html"

# (幅mm, 高さmm, --k)。A1 の --k は 594 ÷ 841
SIZES = {"a0": ("841mm", "1189mm", "1"), "a1": ("594mm", "841mm", "0.7064")}

MARKER = re.compile(r"<!--\s*═══ パーツ(\d+): ([^（═\n]+).*?-->", re.S)


def split_css(src):
    """先頭コメントの閉じ（最初の -->）より後ろの style 要素の中身。"""
    i = src.index("<style>", src.index("-->")) + len("<style>")
    return src[i : src.index("</style>", i)]


def split_parts(src):
    """[(番号, 名前, 断片)]。断片は区切りコメント直後から次の区切り直前（最後は section の閉じタグ直前）まで。"""
    start = src.index('<section class="poster">') + len('<section class="poster">')
    end = src.rindex("</section>")
    marks = list(MARKER.finditer(src, start, end))
    parts = []
    for k, m in enumerate(marks):
        stop = marks[k + 1].start() if k + 1 < len(marks) else end
        parts.append((m.group(1), m.group(2).strip(), src[m.end() : stop].strip()))
    return parts


def sub_once(pattern, repl, text, what):
    text, n = re.subn(pattern, repl, text, count=1)
    if n == 0:
        sys.exit(f"{SRC.name} に {what} が見つからない（テンプレートの形が変わっている）")
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", choices=sorted(SIZES), default="a0")
    ap.add_argument("--parts", help="例: 01,02,03,06,09（省略時は全パーツ）")
    ap.add_argument("--title")
    ap.add_argument("-o", "--out", default="myposter.html")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    src = SRC.read_text(encoding="utf-8")
    parts = split_parts(src)
    by_no = {no: (name, frag) for no, name, frag in parts}

    if a.list:
        for no, name, _ in parts:
            print(f"{no}  {name}")
        return

    if a.parts:
        order = []
        for tok in a.parts.split(","):
            tok = tok.strip()
            if not re.fullmatch(r"\d{1,2}", tok):
                sys.exit(f"パーツ指定が不正: {tok!r}（01〜{parts[-1][0]} の 2 桁番号をカンマ区切りで）")
            no = f"{int(tok):02d}"
            if no not in by_no:
                sys.exit(f"範囲外: {tok}（01〜{parts[-1][0]}）")
            order.append(no)
    else:
        order = [no for no, _, _ in parts]

    frags = [by_no[no][1] for no in order]
    if a.title:
        t = html.escape(a.title)
        frags = [re.sub(r"(<h1[^>]*>).*?(</h1>)", lambda m: f"{m.group(1)}{t}{m.group(2)}", f, count=1, flags=re.S) for f in frags]

    w, h, k = SIZES[a.size]
    css = split_css(src)
    css = sub_once(r"--poster-w:[^;]+;\s*--poster-h:[^;]+;\s*--k:[^;}]+", f"--poster-w:{w}; --poster-h:{h}; --k:{k}", css, ":root の判型 3 値")
    css = sub_once(r"@page\{size:[^;}]+", f"@page{{size:{w} {h}", css, "@page の size")

    title = html.escape(a.title) if a.title else "ポスター"
    body = "\n\n".join(frags)
    out = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>{title}</title>
<!-- scripts/new_poster.py で生成（{a.size.upper()} 縦 {w}×{h}、パーツ {','.join(order)}）。
     規約: references/slide-rules.md ／ 納品前: python3 scripts/check_deck.py {a.out} → FAIL 0 -->
<style>{css}</style>
</head><body>
<section class="poster">

{body}

</section>
</body></html>
"""
    pathlib.Path(a.out).write_text(out, encoding="utf-8")
    print(f"wrote {a.out}: {a.size.upper()} / パーツ {len(order)} 個（{','.join(order)}）")


if __name__ == "__main__":
    main()
