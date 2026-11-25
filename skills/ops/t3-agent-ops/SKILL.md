---
name: t3-agent-ops
description: Muse（司令塔）から各マシンの T3 Code にスレッドを立て、Antigravity / Claude / Devin / Grok のエージェントへ研究開発の作業を委任し、agmsg と完了通知ブリッジで管理するための実測手順と運用ルールを定義する。対象マシン構成、スレッド起動・完了判定、プロバイダとモデル、テレメトリ無効化、CLI パス設定、利用上の線引きおよびマシン固有の対処法を含む。T3 Code 経由で実装・修正・調査・文書起草・レビュー等の作業を委任するとき、または各マシンの T3 環境・プロバイダ・agmsg を運用・保守するときに使用する。
---

# t3-agent-ops — T3 Code を使ったエージェント駆動の運用

**強制ルール (2026-11-23 08:40 ユーザー指示)**: これ以降のすべての作業委任は T3 Code 経由で行う。実装・修正・調査・実験の指示・文書起草・レビュー・相談のいずれも対象。herdr 直起動、Devin CLI 直接実行、素の `agy -p` 直接実行、CPA 直接チャット、汎用 subagent への直接委任は新規作業では使わない。T3 が使えないときは別経路で代替せずユーザーに報告する。例外はユーザーがその場で明示した場合のみ。Muse 自身の対話・検証・T3 スレッド管理・ツール操作は直接行う。詳細は AGENTS.md の「T3 Code エージェント運用」節。

Muse (司令塔) が各マシンの T3 Code にスレッドを立て、Antigravity (Gemini) / Claude (CPA) / Devin / Grok のエージェントに研究開発の作業 (実装・調査・文書起草・レビュー) を委任し、agmsg で名簿と戻り通知を管理する運用の手順。2026-11-22 に gpu-01 でパイロットし、5 台へ展開した。ここには実測済みの内容だけを書く。背景と設計判断は ~/workspace/t3code-agmsg-study/ (REPORT.md、SEAT_DESIGN.md) を参照。

構成は3層: 層1 agmsg (名簿・受け箱)、層2 T3 Messaging (輸送)、層3 完了通知ブリッジ + inbox 確認 (戻り経路)。

## 対象マシン (すべて T3 v0.1.11 常駐、待受は tailnet IP の 3773 のみ)

| マシン | tailnet IP | 状態 |
|---|---|---|
| gpu-01 | 100.105.219.77 | 全プロバイダ実証済み。実作業の主戦場 |
| gpu-02 | 100.68.55.57 | 全プロバイダ実証済み。Node は ~/.local/node24 |
| gpu-03 | 100.84.90.84 | 全プロバイダ実証済み。sqlite3 は deb 展開ラッパー (~/.local/bin/sqlite3) |
| M4 Mac mini | 100.84.99.52 | 全プロバイダ実証済み。node は /opt/homebrew/bin のみ。CPA (CLIProxyAPI :8317) のホスト |
| MacBook (mac-portable) | 100.90.214.14 | 全プロバイダ実証済み。grok は旧版から 1.0.92 に更新済み |

- 2026-11-23 の一斉スモークで、全5台 × 4プロバイダ (claudeAgent、antigravity、grok、acpRegistry_devin) はすべてスレッド完走 (completed) を確認済み。
- **Muse VM (6台目・試行、2026-11-24 導入)**: T3 v0.1.11 を localhost 限定 (127.0.0.1:3773) で常駐。構成が他5台と異なる (下記「マシン固有の癖」の Muse VM 項)。実証済みは全4プロバイダ: claudeAgent (GPT 6.0 Luna)、antigravity (gemini-4-neon、サインインは shirokumarose008@gmail.com)、grok (grok-4.7、アカウントは shirokumalop+001@gmail.com、2026-11-24 に device-auth で再ログイン済み)、acpRegistry_devin (swe-2-flash-medium、認証はこの VM の Devin CLI ログインを共用)。agmsg と完了通知ブリッジは未導入 (Muse 自身が同居するため試行では省略)。プロジェクトは ~/agentic-project/t3-pilot (他機と同名)。
- 接続は SSH (鍵 /home/hatch/.ssh/id_ed25519 + ProxyCommand ~/.local/bin/tsproxy.py、ユーザー ryo)。接続先は事前または接続時にユーザーへ伝える。Mac では対話 zsh の癖を避けるため `ssh ... 'bash -s'` に heredoc で渡し、PATH は `/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin` を明示する。
- T3 の画面は http://<tailnet-ip>:3773。端末の追加は各マシンで `t3 pair` (コード/QR、有効期限約5分)。T3 Connect (アカウントログイン) は使わない。
- サーバー上の新規作業は ~/agentic-project 配下 (Mac も同じ)。

## 作業の流し方 (層2: 輸送)

プロジェクトのディレクトリで:

```bash
t3 thread start . "<指示文>" --provider <provider> --model <model> --title "<短い題>" --json
```

- 戻り値の threadId を控える。`--wait` は付けない (SSH が約90秒で切れるため)。進捗は短い SSH で `t3 thread show <threadId>` を繰り返して確認する。スレッドはサーバ側で継続する。
- 完了判定はスレッドの自己申告ではなく、成果物そのもの (ファイルの中身、テスト結果、数値) で確認する。
- 新規プロジェクトは対象マシンの ~/agentic-project 配下に作り、git init して `t3 project add .` で登録する。**Antigravity はプロジェクトごとに T3 の画面で有効化が必要** (CLI には切り替え手段がない)。新しいプロジェクトで "disabled for project" と出たら、ユーザーに画面での有効化を頼む。
- 画像や PDF を渡すときは、呼び出しごとの作業フォルダに prompt.md と materials/ (入力ファイルのコピー) を置き、「答えは out/answer.md に書け。他のファイルは触るな」と指示して、完了は answer.md の有無と中身で判定する (PaperOrchestra 改造で実証済みの受け渡し形式)。スレッドの表示テキストを答えとして解析しない。
- 標準の分担は TEAM.md §3 の役割表に従う (2026-11-23 改訂: 計画・指揮は Neon / Argon / Opus 5.5 / Fable 5.2、実装は Sol / Opus / Sonnet / Grok / SWE-2 / DeepSeek、実装レビューは Sol / Astra、軽作業は Grok / SWE-2 / Luna / DeepSeek。Opus・Sonnet は antigravity 優先で、クォータ切れ時は devin 側。2026-11-24 追補で、計画・指揮の中では設計・アーキテクチャは Neon 先行、改善・最適化は Opus 先行とし、Neon の停滞判定は確認間隔を長めに取ることにした。根拠と限界は TEAM.md §3.1)。Muse はブリーフ作成、成果物の検証、数値の照合を担う。ブリーフや相談は日本語で書く。
- チーム憲章は同じフォルダの `TEAM.md` (役割表、ルーティング規則、承認・検証・失敗時の規則)。役割の割り当てや失敗時の扱いに迷ったら SKILL.md の実測事項と合わせて TEAM.md を見る。
- ブリーフは同じフォルダの `BRIEF_TEMPLATE.md` の全欄を埋めてから出す (2026-11-23 採用)。対象ファイル / 対象外 / 完了条件 / レビュアー (別モデル) / 検証方法 / 失敗時の停止条件が欠けたブリーフは発行しない。停滞の目安 (進捗確認2回連続で変化なし → 止めて小さいブリーフで出し直す) も TEAM.md §9.1 にある。
- 長時間の学習やジョブ監視そのものは T3 スレッドではなく、従来の herdr / cron の領分のまま。

### provider とモデル (実測済み)

- `antigravity` (インスタンス ID は全サーバー共通でこの名前。認証は oauth-personal): gemini-4-neon (既定、速い)、gemini-4-argon、gemini-4-hydrogen、gemini-pro-orchestrator-neon (段取り型)、gemini-pro-orchestrator-g1-pro、gemini-3.8-flash、claude-opus-5-5、claude-sonnet-5-5、gpt-oss-120b-medium。使うモデルは TEAM.md §2.2 の割り当てに従う (gemini-3.8-flash と gpt-oss-120b-medium は割り当て外)。文書の起草・構成は Gemini が第一候補 (ユーザー指定)。
- `claudeAgent` (裏側は各マシンの Claude Code + Mac mini の CPA): 使うモデルは TEAM.md §2.2 の割り当て (gpt-6-luna、gpt-6.1-terra、preview/DeepSeek-V4.1-Flash-1017)。Luna (slug `claude-fable-5-dd-anul-6-tpg`) は全台で completed 実測済み (途中で waiting 表示になることがあるが最終的に完了する)。DeepSeek はさくらの AI Engine で月3,000リクエストまで無料、超過はレート制限のみ (CPA 経由の実呼び出し検証済み)。Terra はユーザー指定の割り当てで、slug は使用時にモデル一覧で確認する。
- `acpRegistry_devin` (T3 管理ランタイムの Devin。単体の Devin CLI 本体はサーバーに無くても動く): 使うモデルは TEAM.md §2.2 の割り当て (SWE-2、claude fable 5.2、claude opus 5.5、gpt-6.2 astra、claude sonnet 5.5、gpt-6.2 sol)。実測済みの slug は gpt-6-sol-medium、gpt-6-2-sol-medium。表示名と slug が異なる場合は一覧で対応を確認する。
- `grok` (Grok Build CLI): grok-4.7。Grok の呼び出しはこの CLI を既定とする (ユーザー決定)。CLI の検出には symlink が要る (下記 PATH の節)。
- `codex` はユーザーが使わない方針 (2026-11-23)。新規の委任では選ばない。

## テレメトリ無効化 (2026-11-24、全5台適用済み)

- T3 Code は既定で製品テレメトリ (モデル名・Token 数・権限モード等) を ingest.t3.codes へ送り、Identify.ts が ~/.codex/auth.json と ~/.claude.json のアカウント ID を無塩 SHA-256 で送る (一次資料で検証済み。経緯は MEMORY.md の 2026-11-24 の記録)。
- 全5台の常駐サービスは無効化済み: 各機 ~/.t3/service.env に `T3CODE_TELEMETRY_ENABLED=false`、`T3CODE_OTEL_SDK_DISABLED=true`、`OTEL_SDK_DISABLED=true` の3行を入れ、再起動後に serve プロセスの環境変数で確認済み。バックアップは service.env.bak-20261124-telemetry。
- T3 の更新・再導入・service install のやり直しをしたときは、service.env の3行が残っているかを必ず確認し、消えていたら入れ直して再起動する。
- サーバー側設定では止まらない経路: ブラウザ版 Web アプリとモバイルアプリの Axiom 中継トレース (スイッチなし)。
- 「Publish agent activity」(モバイル通知用にプロジェクト名・スレッド名等を Connect 中継へ送る機能) は 2026-11-24 に全5台でオフ確定: 有効条件は secret `cloud-publish-agent-activity` が "true" かつ `cloud-relay-url` と `cloud-relay-environment-credential` の両方が存在すること (v0.1.11 バンドルの readAgentActivityPublishingActive) だが、全5台の ~/.t3/userdata/secrets/ に3つとも無く、`t3 status` でも全台 T3 Connect off。将来 Connect を連携したら Settings > Sharing & access でこのトグルがオフのままか確認する。

## agmsg (層1: 名簿・受け箱 / 層3: 戻り通知)

- 各マシンに agmsg v1.8.2、team `t3-pilot` (ローカル SQLite、マシン間で共有されない) があり、席は muse (Muse)、claude、codex、gemini、t3bridge。対象プロジェクトは各機の ~/agentic-project/t3-pilot。スクリプトは ~/.agents/skills/agmsg/scripts/ の join.sh / send.sh / inbox.sh / history.sh / team.sh。
- Muse から: `bash $S/send.sh t3-pilot muse <席> "<文>"`、`bash $S/inbox.sh t3-pilot muse`。結果待ちのスレッドがある場合は、ターン開始時に inbox を確認する。
- 完了通知ブリッジが全台で稼働中: スレッドの「実行中 → 完了/失敗」遷移を検知し、t3bridge 席から muse 席へ通知が届く (Linux は systemd ユーザーサービス t3-agmsg-bridge.service、Mac は LaunchAgent com.nao.t3-agmsg-bridge)。スクリプトの正本は ~/workspace/t3code-agmsg-study/bridge/t3_agmsg_bridge.py。
- 実プロジェクトへ広げるときは、プロジェクトごとに team を分けるか席名に接頭辞を付けるかをその時点で決める。現状、実案件の連絡はスレッドと成果物ファイル経由が主で、agmsg は t3-pilot の通知に使っている。
- 実セッション側の delivery 設定 (agmsgd 等) は未実施。CPA の Claude 系が復旧してから、各席のセッションで /agmsg を実行して設定する。

## CLI ツールの検出 (PATH)

- T3 は provider の CLI をサービスプロセスの PATH で探す。grok は導入先が ~/.grok/bin で PATH に入らないため、**~/.local/bin へ symlink が要る** (grok 本体と agent の両方。gpu-01 の既存構成が手本)。symlink 後に `t3 service restart` すると認識される (2026-11-23 gpu-02 で実証)。他の CLI を新規導入するときも同じ確認をする。
- grok CLI 本体は公式インストーラ `curl -fsSL https://x.ai/cli/install.sh | bash` で入れ、版は 1.0.92 (gpu 系と Mac mini)。ログイン状態は対象マシンの `grok models` で確認できる。

## 守る線引き (ユーザーの承認した枠)

- T3 経由で Antigravity を触る範囲の自動化はユーザーが承認済み (2026-11-22)。この枠の外 (素の `agy -p` をエージェントループに包む、OAuth トークンの抽出・プロキシ、アカウントローテーション) はしない。Antigravity の利用は公式 antigravity-acp + oauth-personal のみ。
- Google のクォータは 1 アカウントを全マシンで共有する (5時間枠と週間枠)。台数を増やしても枠は増えないので、並列にスレッドをばらまいて枠を早く食い潰さない。クォータ切れのとき ACP はクレジットにフォールバックせず停止する。
- Antigravity のプラグイン／スキルを T3 セッションで使わせるには、本体の ~/.gemini/config/plugins/ への導入だけでは足りず、各 ACP プロファイル (~/.t3/userdata/providers/antigravity/<hash>/config/plugins/) へ symlink を張る必要がある (2026-11-25 実測: gemini-frontend-design (demolab プラグイン) で、リンク前は Neon が「利用不可」、リンク後はスキル本文を読んで正答)。~/.gemini/antigravity/skills へのコピーも ACP セッションからは読まれない。新しいプラグインを入れたら、プロファイル全件へのリンクと、新規スレッドでの利用可否スモークまで行う。
- agy-fast v0.2.8 は全サーバーに標準導入済み (2026-11-23 ユーザー決定)。導入先はグローバル領域 ~/.gemini/config/plugins/agy-fast で、インストーラが T3 の ACP ランタイムにもリンクする。版は各機の ~/agentic-project/agy-fast の clone (commit 552367f) に固定し、自動更新は mcp_config.json の AGY_FAST_AUTO_UPDATE=off で切ってある。再導入や更新は clone から `node scripts/install.mjs install` を実行し、自動更新オフを再設定する。小規模タスクの A/B では差は誤差範囲だった (2026-11-22 実測) が、標準装備として使う方針。
- 認証情報 (ペアリングコード、OAuth トークン) はチャットやファイルに書かない。

## マシン固有の癖

- Muse VM: systemd ユーザーマネージャが無いため `t3 service install` は使えない (user-manager-unavailable で失敗する)。常駐は systemd システムユニット `t3code-muse.service` (ユニット正本と復旧スクリプトは ~/workspace/t3-muse-vm/、VM 入れ替え後は install-service.sh の再実行で復旧)。`__service-launcher` は ~/.t3/runtime/service-state.json ({"protocol":4,"activeVersion":"0.1.11"}) が無いと起動しないため、同スクリプトが無ければ作る。インストーラの tar 展開は所有権変更が許可されず失敗するので `TAR_OPTIONS=--no-same-owner` を付けて実行する。service.env には他機の3行に加えて `T3CODE_HOST=127.0.0.1` と `IS_SANDBOX=1` (root 実行で Claude Code が --dangerously-skip-permissions を拒否するため) が要る。通信は宛先で経路が分かれる: CPA (tailnet) は tunnel proxy (ポート 3130) でしか届かず、Google 等の公開側は egress proxy (3128) でしか届かない (どちらも実測済み)。このため振り分けプロキシ (~/workspace/t3-muse-vm/route-proxy.py、systemd ユニット t3-route-proxy.service、127.0.0.1:18131、*.ts.net と 100.64/10 は 3130、それ以外は 3128 へ中継) を常駐させ、T3 のプロキシ変数は全て 127.0.0.1:18131 に向ける (drop-in proxy.conf)。上流 URL は /etc/t3-route-proxy.env (600) にのみ置き、install-service.sh が HTTPS_PROXY から生成する。プロバイダの有効化は画面なしでも可能: ~/.t3/userdata/settings.json の providerInstances に {"antigravity": {"driver": "antigravity", "displayName": "Antigravity", "enabled": true}} を書いて再起動すると有効化され、サーバが不足キーを補って書き戻す (2026-11-24 実証)。Antigravity のサインインは、プロファイルの app data dir を指定して `agy acp --login --app-data-dir ~/.t3/userdata/providers/antigravity/<hash>/antigravity-acp` を実行し、表示される Google の URL をユーザーが開いて認可コードを貼る方式 (ACP の認証エラー文がこの手順を指定する)。サーバ本体の外向き HTTP (Effect HttpClient) はプロキシ環境変数を見ないため、ACP レジストリの取得や grok の版チェックはこの VM では失敗する (実測。版チェックの失敗は無害)。Devin の導入は、gpu-01 から ~/.t3/caches/acp-registry/registry.json と ~/.t3/tools/devin (247MB、プログラム配布物のみ) をコピーして種まきした (どちらもホーム配下なので VM 入れ替えでも残る)。レジストリの版が上がったら同じコピーをやり直す。`t3 status` では Service が not installed と出るが、これはユーザーサービスを見ているためで異常ではない。
- MacBook: T3 サービス起動時にログインシェル (zsh -ilc) の環境読み取り子プロセスがハングし、3773 が上がってこないことがある。切り分けは ~/.t3/userdata/logs/boot-service.log の "Failed to read PATH from login shell"。子プロセスを kill すると起動が進む (実測)。根本対処は .zshrc 側の初期化見直し。
- MacBook: デスクトップアプリ版 (T3 Code (Beta).app) は常駐サービスと同じ ~/.t3 を掴むため、そのまま開くと "This T3 home is unavailable" で起動できない (2026-11-23 実測、サービス PID 4136 と一致)。共存策としてアプリ専用 home ~/.t3-app を分け、ラッパー ~/Applications/T3 Code Client.app (AppleScript 製、`open --env T3CODE_HOME=$HOME/.t3-app -a 'T3 Code (Beta)' を実行、本家アイコン流用) から起動する形にした。アプリは 127.0.0.1:3773 で自前の空サーバを立てて起動し、サービス (tailnet IP:3773、HTTP 200) は無影響。サービス側 plist は T3CODE_HOME=/Users/ryo/.t3 を明示しているため競合しない。launchctl setenv で GUI 全体へ広げる方法は、GUI 起動ターミナルの t3 CLI の既定 home まで変わってしまうため採用しなかった。常駐サーバへの接続は、アプリの Settings → Connections → Add environment に、サービス側で発行した `t3 pair` のペアリング URL (またはホスト+トークン) を貼る方式 (ペアリングコードはユーザー自身が発行する)。2026-11-23 にユーザーがペアリングを完了し、サービス側の `t3 auth session list` で desktop / Electron クライアントのセッション発行と接続を確認済み。
- gpu-03: sqlite3 は公式バイナリ (glibc 2.38 要求) が動かず、Ubuntu jammy の deb を展開したラッパーにしてある。agmsg が "sqlite3 が無い" と言ったらこのラッパーの PATH を疑う。
- Mac mini / MacBook: 非対話 SSH の PATH に homebrew が入らない。コマンドの前に PATH を明示する。`timeout` コマンドは macOS には無い。
- gpu-02: linger は 2026-11-23 に有効化済み。再起動後に T3 が上がらない場合は loginctl の Linger を確認する。
