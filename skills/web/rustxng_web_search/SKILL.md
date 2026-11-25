---
name: rustxng_web_search
description: API キー不要の多エンジン検索ツール RustXNG を用いて、VM ローカルでの Web 検索および `gpu-01` インスタンス経由のページ本文取得・MCP 操作を実行・保守する手順を定義する。導入確認、ラッパーや HTTP API による検索、VM のプロキシ・DNS 制約下での運用、`gpu-01` 接続時の事前通知と更新検証、およびスニペットを根拠にせず一次ページを読む原則を含む。ユーザーが RustXNG での検索を求めたとき、複数プロバイダを横断した情報源探索や `gpu-01` 経由の本文取得が必要なとき、または RustXNG の導入状態を点検・更新するときに使用する。
---

# RustXNG web search

## Choose RustXNG for a search

- Use this skill when the user asks to search with RustXNG or names RustXNG directly.

- Use RustXNG as an additional independent search route alongside `browser.search` when a question benefits from results aggregated across many providers without any API key.

- Treat every RustXNG result as a snippet for source discovery and never as evidence for a claim.

- Fetch the source page with `browser.open` or `browser.browse` and read its body before judging, quoting or acting on it.

- Keep private information out of search queries because RustXNG sends the query text to the upstream providers selected for the request.

## Check the installation

- Run `/home/hatch/.local/bin/rustxng --version` and expect a line starting with RustXNG followed by the installed version.

- Check for an already running service with `curl --fail --max-time 3 http://127.0.0.1:29483/healthz` and reuse it when it answers.

- Confirm a reused service is really RustXNG by reading `/config` and checking that its version starts with RustXNG, that it lists an engines array and that its brand URL is the RustXNG GitHub repository.

- Reinstall from the release binary when the binary is missing, following the agent setup guide in the RustXNG repository at https://github.com/sahenjp/RustXNG/blob/main/docs/AGENT-SETUP.md.

- Verify the SHA-256 sidecar before installing any downloaded binary and stop the install on a checksum mismatch.

- Install only into user owned locations, with the binary at `/home/hatch/.local/bin/rustxng` and the license files and settings under `/home/hatch/.local/share/rustxng/`.

## Run a search

- Search through the wrapper with `muse.exec` by running `/home/hatch/.local/bin/rustxng-search "<query>" 5`, which starts the service on loopback when needed and prints JSON with title, url and content for each result.

- Keep the first search small at five results and widen max_results only when the first set is too thin.

- Call the HTTP API directly with `curl --get http://127.0.0.1:29483/search` and the format and max_results data fields when extra parameters are needed.

- Narrow a direct API search with the engines parameter for a known source, with include_domains or exclude_domains for domain control and with time_range for recency where providers support it.

- Project the JSON response down to title, url and content with `jq` before passing results into the conversation, as the wrapper already does.

- Read `unresponsive_engines` when a search returns few or no results and report upstream availability instead of treating a healthy `/healthz` as proof that search works.

- Avoid repeated high volume searches against the upstream providers and respect each provider's terms and rate limits.

## Work within the limits of this VM

- Keep the user settings in `/home/hatch/.local/share/rustxng/settings.toml`, which select the staged search strategy with longer timeouts for this VM's congested outbound proxy, and restore those values if a reinstall replaces the file.

- Expect the default parallel strategy with a three second limit to time out on most engines through this proxy, and check the settings file first when searches suddenly return nothing.

- Do not rely on page text from the VM local RustXNG, because its page fetcher rejects this VM's synthetic 198.18 DNS answers as non-public by design and direct egress from this VM is blocked, which was verified with a proxy free test instance as well.

- Fetch page text through the gpu-01 instance described in the next section whenever a task needs RustXNG page text, and keep the browser tools as the other route for reading sources.

- Run `/home/hatch/.local/bin/rustxng mcp` only when a caller needs the MCP search tool over stdio, knowing that its read_page tool cannot work on this VM.

- Let the service exit on its own after 300 seconds without requests and start it again through the wrapper on the next search instead of keeping a permanent process.

- Find the service log and past verification output under `/home/hatch/workspace/rustxng-run/` when a search fails and the cause is unclear.

## Fetch page text through the gpu-01 instance

- Tell the user that the work connects to gpu-01 before or when using this route, as with any server connection.

- Search with page text by running `/home/hatch/.local/bin/rustxng-search-full "<query>" 5` with `muse.exec`, which calls the same RustXNG 0.27.1 on gpu-01 over SSH and returns raw_content of up to about 8000 characters per result.

- Use the gpu-01 instance installed under `/home/ryo/agentic-project/rustxng/` on that machine, where its service binds only to loopback on port 29483 and starts on demand through the remote script of the same name pattern.

- Drive the gpu-01 MCP server over SSH stdio when a caller needs read_page, using the Tailscale SSH invocation from TOOLS.md with the remote command `/home/ryo/agentic-project/rustxng/rustxng mcp`.

- Pass the result count to the MCP search tool as limit rather than max_results and parse its results from the JSON text in the response content.

- Call read_page only with a URL that the same MCP session's search returned and page through long texts with offset and the query argument for matching passages.

- Reinstall the gpu-01 copy from the verified release binary into `/home/ryo/agentic-project/rustxng/` when it is missing and confirm `--version`, a plain search and one raw_content search before relying on it again.

## Maintain the installation

- Check for a newer release with `/home/hatch/.local/bin/rustxng --check-update` when the user asks about updates or a version problem appears.

- Update with `/home/hatch/.local/bin/rustxng --update` only after telling the user, then verify the new version with `--version`, `/healthz` and one small JSON search before reporting success.

- Remember that `--update` covers only the VM local copy and reinstall the gpu-01 copy separately from the matching release when versions need to stay in step.

- Report the binary version, the endpoint http://127.0.0.1:29483 and one working search command when the user asks how RustXNG is set up.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Prefer the matching `browser.search` vertical for news, sports, weather, finance and datetime questions, where RustXNG results carry no live guarantee.

- Reformulate the query in the other language, Japanese or English, and search again when the first results miss the sources the user cares about.

- Combine one RustXNG search with one `browser.search` query and compare the top results when a topic is contested or fast moving, then read the strongest primary sources from either set.
