---
name: parallel_web_search
description: Parallel MCP のカスタムコネクタ（匿名モード）を用いて、`web_search`・`web_fetch`・`web_decisions` による独立した Web 検索と情報取得を実行・保守する手順を定義する。個人情報を含めない検索、抜粋に頼らない公式一次情報の確認、クライアントの疎通確認・ツール呼び出し方法、レート制限対応および代替検索手段との使い分けを含む。ユーザーが Parallel での検索や検証を求めたとき、価格・無料枠・規約・リリース変更などを公式情報で裏取りしたいとき、または Parallel コネクタを点検・保守するときに使用する。
---

# Parallel web search

## Choose Parallel for a search

- Use this skill when the user asks to search or verify with Parallel, names Parallel MCP, or says "Parallelで調べて".

- Use Parallel as an extra independent search route alongside `browser.search` and RustXNG when a factual claim needs verification against official sources, especially prices, free tiers, terms and release changes.

- Use `web_decisions` only when the user asks for it by name, or asks for a probability, a pick among options they gave, or a score on a scale they gave, and suggest it instead of calling it when it merely seems like a better fit.

- Keep private information out of queries and fetched URLs, because every query is sent to Parallel, a US company, and the user approved this route for public information only.

- Read the primary source itself before a judgement that matters, because Parallel excerpts are evidence pointers and the user's rule is that snippets alone never settle a question, and pricing table excerpts in particular can come back broken.

## Check the installation

- Confirm the connector files exist at `~/workspace/custom-connectors/custom.parallel/` with `bin/client.py`, `CONNECTOR.md` and `connector.yaml`.

- Run `python3 ~/workspace/custom-connectors/custom.parallel/bin/client.py list-tools` and expect 7 tools in anonymous mode, with no `web_research`.

- Rebuild the client from the notes in the connector doc when `list-tools` fails, keeping curl as the transport because urllib fails on chunked SSE through this VM proxy.

## Run the tools

- Write arguments as one JSON object in a workspace file, then call `python3 ~/workspace/custom-connectors/custom.parallel/bin/client.py call-tool --name <tool> --arguments-file <path-to-json>`.

- For `web_search`, set `objective` and 2 to 3 concise `search_queries`, and answer from the returned excerpts when they carry enough evidence instead of fetching every result.

- For `web_fetch`, pass up to 20 URLs with an `objective`, and leave `full_content` off unless the whole page is needed.

- Pass a returned `session_id` back on follow-up calls in the same conversation, and never invent one.

- Stop on a rate limit error and cool down, because anonymous free use is rate limited and repeated retries make it worse.

## Maintain the installation

- Keep the connector in anonymous mode unless the user asks to sign in, because sign-in adds `web_research` and higher limits but needs an OAuth or API key flow this client does not implement.

- Add a newly offered server tool to `ALLOWED_TOOLS` in `client.py` only after reading its schema from `list-tools` and noting it in the connector doc.

- Keep `send_feedback` blocked until the user agrees to a specific feedback note and has seen its text.

## Available connectors

- [Parallel](~/workspace/custom-connectors/custom.parallel/CONNECTOR.md) for the exact commands, inputs and limits.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

## Alternatives for better results

- Prefer the matching `browser.search` vertical for news, sports, weather, finance and datetime questions.

- Combine one Parallel search with one RustXNG or `browser.search` query and compare the strongest primary sources when a topic is contested or fast moving.

- Reformulate the query in the other language, Japanese or English, when the first results miss the sources the user cares about.
