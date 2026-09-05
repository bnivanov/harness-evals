# Oh My Pi versus DeepSeek Harness

A pairwise comparison of two open-source coding runtimes. The unit of analysis is the harness, not the model. Claims are pinned to trees cloned on 2026-08-25: Oh My Pi [`969a94c1`](https://github.com/can1357/oh-my-pi/commit/969a94c1eeccb1b7528cd5621934bca1908ab622) and DeepSeek Harness [`b150a551`](https://github.com/deepseek-ai/deepseek-harness/commit/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e). GitHub API snapshots are from the same day. Vendor README scores are hypotheses until a model-pinned eval reproduces them. Primary evidence is repo source. Community blogs that compare `dsh` to Pi, not OMP, are out of scope.

## Identity and disambiguation

**Oh My Pi**, binary `omp`, npm `@oh-my-pi/pi-coding-agent` 18.0.4, is a MIT-licensed Pi fork by Stencil Labs. The README calls it "a coding agent with the IDE wired in" and lists 60-plus providers, 31 built-in tools, 14 LSP operations, 28 DAP operations, and a Rust natives core. Upstream is Mario Zechner's Pi. This project's Wave 1 protocol already treats Pi as the minimal control and OMP as the batteries-included delta. Prime Agent is a third Pi-family fork. It is not OMP.

**DeepSeek Harness**, CLI `dsh`, npm `@deepseek-ai/dsh` 0.1.1-rc.2, is DeepSeek AI's first-party agent runtime. Everything is a plugin, including the agent loop, on [Cordis](https://github.com/cordiverse/cordis). The README marks a developer preview with compatibility-breaking changes. Homepage: [deepseek.com/harness](https://deepseek.com/harness/en/). This is not the DeepSeek V4 model, not Grok, and not a ranking of those weights.

Three nearby names are easy to mix up.

1. **Pi** is the tiny kernel OMP grew from. Four-tool-class loop, extension files, no IDE pretensions. Comparing OMP to `dsh` without saying "OMP already left Pi's default tool set" is a category error.
2. **Zagens** ([didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens)) is a third-party, DeepSeek-V4-oriented harness with its own Kernel V3, TUI, and desktop app. It is not Cordis and it is not first-party DeepSeek.
3. Official Python is `deepseek-harness-sdk` per [`docs/user/guide/python-sdk.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/user/guide/python-sdk.md). A similarly named PyPI client that is not this repo is a different product.

`dsh` also ships `@deepseek-ai/dsh-llm-pi-ai`, backed by [`@earendil-works/pi-ai`](https://www.npmjs.com/package/@earendil-works/pi-ai), beside an official DeepSeek adapter on `deepseek-official`. Using Earendil's LLM client as a plugin does not make `dsh` an OMP derivative. The loop, session log, sandbox, and UI are Cordis packages.

No SWE-bench or in-house scores are reported. None were run. The OMP README table that claims hashline lifts Grok Code Fast 1 from 6.7% to 68.3% is vendor marketing until reproduced. Star counts are social facts, not quality ranks.

## Architecture and control loop

OMP still sits on Pi's bet: a product loop with a rich host API. Extensions register tools, commands, and handlers. The loop stays the product. Runtime is `@oh-my-pi/pi-agent-core`. The CLI and TUI are `@oh-my-pi/pi-coding-agent`. You do not swap the loop from a YAML overlay. You fork or hook it.

`dsh` inverts that. [`docs/architecture.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md) is explicit. There is no privileged core to patch. Plugins contribute services, typed events, and reversible effects to a Cordis context. The default driver is `@deepseek-ai/dsh-agent-loop` on `ctx.agentLoop`. Other packages depend on `ctx.agents`, never on the loop package, so a replacement driver is a composition change. A running process is a profile: ordered bundles, `cordis.patch.yml`, optional `--patch`. `web` and `headless` ship as templates. `dsh --profile web --dump-config` prints the tree your machine boots.

The `dsh` turn is event-sourced. A step is one model request plus its tools. A turn is zero or more steps. Durable facts go on an append-only `SessionEvent` log. Model-visible means logged. `deriveMessages()` projects history. A runtime invariant asserts reconstructability. OMP sessions, per [`docs/session.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/session.md), are a versioned JSONL tree with `id`/`parentId`, compaction entries, and branch summaries. They fork and resume. They are not an event vocabulary plugins extend by declaration merging.

The Cordis inversion is real, not a slogan. It is also a tax. Replacing the loop is only useful if you have a second loop. Daily coding does not. A frozen eval driver can still prefer `dsh` because that driver is named and contract-tested in [`packages/core/agent-loop/tests/contract-regressions.spec.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/agent-loop/tests/contract-regressions.spec.ts).

## Tools

OMP's README claims 31 built-in tools. In-tree docs match: 31 files under [`docs/tools/`](https://github.com/can1357/oh-my-pi/tree/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/tools). Beside `read`/`write`/`edit`/`bash`/`grep`/`glob` sit `lsp`, DAP `debug`, `eval` with persistent Python and Bun kernels that re-enter agent tools, `task`, `ast_edit`/`ast_grep`, `browser`, `computer`, `web_search`, GitHub-as-filesystem URL schemes, and memory tools.

Default `edit` is **hashline**. Input is `[PATH#TAG]` sections whose four-hex tag must match the latest anchored snapshot. Stale tags reject before application. Grammar: [`packages/hashline/src/grammar.lark`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/hashline/src/grammar.lark). Tests live under `packages/hashline/test/`. Modes `apply_patch`, `patch`, and `replace` exist for models that cannot speak hashline. Treat the README's "tenfold lift" as a claim about that protocol, not about OMP-as-IQ.

`dsh` publishes a generated [tool schema catalog](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/tool-catalog.md). Shipped plugins cover shell, fs read/write/edit, `str_replace_editor`, `glob`/`grep`, `lsp` with four operations, web, todos, skills, `subagent`/`subagent_fork`, jobs, optional persistent terminals, TypeScript `run_code` that re-enters the guarded pipeline, plan-mode exit, ask-user, session-query, workflow, and experimental Agent Teams. There is no hashline package and no DAP tool.

LSP width is not close. OMP's action enum includes diagnostics, rename, code actions, symbols, and raw requests, with WorkspaceEdit application. `dsh` keeps a closed four-op seam so a provider swap does not change the model-facing schema. If a task is "attach lldb and read the frame," OMP has a first-party path and `dsh` does not. `run_code` and OMP `eval` are cousins: a program calls back into tools so one chat round trip is not required for every file touch.

## Context and memory

OMP memory is optional. `memory.backend` is `off` by default. `local` writes project-scoped `MEMORY.md` and `learned.md`. `hindsight` and `mnemopi` are alternate engines. Tools `retain`, `learn`, `recall`, `reflect`, and `memory_edit` exist when the backend supports them. Compaction is a first-class session entry. Stream rules abort a generation mid-token, inject a matching rule, and retry.

`dsh` compaction is a seam: start/summary/end events lock the log, and the summary rides a `user/message` replace so history stays reconstructable. Skills are `ctx.skills` plus a model-facing `skill` tool. I did not find OMP-style cross-session `retain`/`learn`/`recall`. Session-query tools search this run's event log. For a long unattended science run you would pin OMP's memory backend. For a replayable single-task eval, `dsh`'s reconstructability invariant is the cleaner audit trail.

## Auth and model pinning

OMP `/login` is provider-scoped. SuperGrok / X Premium+ is first-class as `xai-oauth`: RFC 8628 device code against `https://auth.x.ai`, Responses API at `https://api.x.ai/v1`, usage probes on `cli-chat-proxy.grok.com`. Docs list `grok-4.6` as the OAuth default, plus `grok-build` SKUs, with subscription cost recorded as zero. `XAI_API_KEY` is a different provider, `xai`. This repo's Wave 1 review already said mixing those ledgers is not a Grok-fixed experiment.

`dsh` stores secrets as credential references. Settings never hold the literal key. The first-party adapter is DeepSeek V4 Flash / Pro / vision on `deepseek-official`. Catalog providers and custom OpenAI-compatible gateways go in `settings.yaml` under `llm-pi-ai`. Tests show the bundled pi-ai catalog includes `xai`. That is API-shaped xAI, not the SuperGrok device-code flow in OMP's `packages/ai/src/registry/oauth/xai-oauth.ts`. I did not find an `xai-oauth` login in `dsh`. Pinning Grok on `dsh` currently means an API key or a custom route.

OMP headless pinning is a CLI flag: `--model`, `--smol`, `--slow`, `--plan`. `dsh --profile headless` exists, but model identity is a composed plugin setting, not a launcher `--model grok-4.6` in the CLI README. A `dsh` session that has already sent a request keeps the model recorded in its log.

## Surfaces

OMP is TUI-first. `omp -p` is print/headless. `--mode json` emits structured events. `--mode rpc` is JSONL over stdio. ACP drives the same agent from an editor. `/collab` shares a live session, including a browser guest.

`dsh`'s documented path is `npx @deepseek-ai/dsh web` on `http://127.0.0.1:3080`. The CLI launches profiles: `dsh web`, `dsh --profile headless "job"`, `dsh plugin`. The CLI README mentions a TUI profile "assuming the tui profile is installed." I did not find a first-party TUI package in this clone. `@deepseek-ai/dsh-acp` is automation-only JSON-RPC. Interactive rendering belongs to the web host. Python SDK and TypeScript JSON-RPC examples cover programmatic clients.

Calling OMP an IDE is shorthand for TUI plus LSP/DAP plus ACP. It is not VS Code.

## Extensibility

OMP extensions export a factory over `ExtensionAPI`. Skills, marketplaces, and MCP sit on that host. MCP discovery reads `.omp/mcp.json` and also translates Claude, Codex, Gemini, OpenCode, Cursor, Windsurf, and VS Code MCP files. Extensions hook the loop. They do not replace it.

`dsh` extensions are the product. A plugin is `export function apply(ctx)`. Community packages use the `dsh-plugin` topic. MCP is one Cordis row per server, tools named `mcp__<server>__<tool>`, with HMR reconnect. Optional subagent backends include a locked `@openai/codex@0.147.0` and Claude Code. Those are nested SUTs. Leave them off a Grok-pinned cell. If you need to A/B a sandbox or a loop without a process restart, `dsh` has the vocabulary. If you need to drop a script in `~/.omp` and keep coding, OMP does.

## Safety and approvals

This is the largest eval confound in the pair.

OMP's default `tools.approvalMode` is **`yolo`**. `read`, `write`, and `exec` auto-approve unless a tool policy or user override says otherwise. Modes `write` and `always-ask` exist. `bash` can still force prompts on destructive patterns, but a bare critical override is ignored in yolo. MCP tools default to the `write` tier. Unknown custom tools default to `exec`, which yolo then allows.

`dsh` approval is fail-closed. Outcomes are `allowed-once | rejected | cancelled | unavailable`. A missing or throwing answerer is `unavailable`, and callers deny. Session policy is `ask` or `never`. `never` is the documented strict headless stance. Default permission presets bundle `workspace-write` with `ask`, and `danger-full-access` with `never`. Sandbox modes are `read-only`, `workspace-write`, and `danger-full-access`, implemented with Linux bwrap/Landlock, macOS Seatbelt, and a Windows ACL restricted-token runner. Enforcement may report `partial` on older Landlock ABIs. Network is outside this vocabulary.

An OMP yolo run and a `dsh` ask+workspace-write run are not the same independent variable. Pin approval and sandbox before attributing pass rate to "harness quality."

## Multi-agent

OMP `task` fans out subagents, optionally into isolated worktrees, with schema-validated yields and `agent://` paths. Agent Hub is a TUI roster with steer, revive, and kill. An advisor model can watch every turn on its own context.

`dsh` treats subagents as a named-provider registry: continuable children, one-shot forks, and foreign CLIs share `ctx.subagents`. Experimental Agent Teams add a durable roster, mailbox, and task DAG, disabled in `dsh-base`. That is more kinds of delegation, including "call another lab's CLI as a child," and less of a single polished hub in the terminal.

## OSS versus preview governance

Both trees are MIT. On 2026-08-25 the GitHub API reported OMP `has_issues: true` and `open_issues_count: 1768`. PRs were temporarily open to everyone per the README. `dsh` sets `has_issues: false`. GraphQL reported 4457 Discussions. [CONTRIBUTING.md](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/CONTRIBUTING.md) says the project cannot accept external pull requests and asks people to write plugins instead. That is a published runtime plus a plugin ABI, not a patch-the-monorepo commons.

npm `0.1.1-rc.2` plus a breaking-change warning is a freeze risk. Pin the git SHA. Do not float `@deepseek-ai/dsh`. OMP `18.0.4` looks like a mature series and is still a fast-moving fork. Pin that SHA too. Stars the same day: OMP 27,300; `dsh` 193,830, repo created 2026-08-13. The `dsh` figure is a twelve-day GitHub event, not a quality instrument.

## Eval and reproducibility

`dsh` testing policy is unusually strict: unit tests, a per-file 100% coverage gate on `packages/*/*/src`, keyless ACP and headless JSONL snapshots, web Chromium snapshots, and with-key e2e that self-skip without secrets. Policy text says to verify the world, not the agent's self-report. One ACP scenario pins full system-prompt and tool-schema content.

OMP has a large Bun test tree, hashline tests, approval-mode tests, SuperGrok usage tests, and CI badges. I did not find an equivalent coverage-plus-transcript-snapshot PR requirement. Headless entries are `omp -p --mode json` and `dsh --profile headless`.

## Fit for Grok-pinned science versus daily coding

**Grok-pinned science.** OMP is currently the only one of this pair that implements SuperGrok OAuth as a native provider with a documented default of `grok-4.6` and a separate `xai` API-key ledger. Wave 1 already named OMP as the batteries cell against Pi. `dsh` can likely call xAI through pi-ai's catalog or a custom route, but that is `XAI_API_KEY` science unless someone writes an OAuth plugin. The first-party `dsh` path is DeepSeek V4. Using `dsh` as a Grok harness is a composition, not the product default. Approval defaults also disagree. Science that wants "same Grok, different loop" should pin `xai-oauth` versus `xai` explicitly, pin approval to the same tier, disable OMP memory backends, disable `dsh` Agent Teams and foreign subagent providers, and log edit protocol (hashline versus str_replace).

**Daily coding.** OMP is the terminal IDE: hashline, LSP width, DAP, worktree subagents, advisor, collab, MCP imported from whatever else you already configured. Default yolo will scare a security reviewer and delight a solo user. `dsh` is the browser-first, policy-first, plugin-first runtime you recompose when you care about Landlock, fail-closed approvals, an official DeepSeek adapter, and swapping the loop. Developer preview means your plugins will break. CONTRIBUTING means you will not land the fix in the monorepo. You will publish a plugin.

## Where OMP is better

Hashline is a real edit contract with a grammar, snapshot tags, and tests. `dsh` still speaks unique-literal replace. If models waste turns on stale patches, that mechanism is the hypothesized cause, and only OMP ships it as default.

The built-in tool set is a coding IDE. Fourteen LSP ops including rename and diagnostics, twenty-eight DAP ops, persistent kernels that call tools, GitHub/PR/conflict URL schemes, ast_edit with an accept card. `dsh` LSP is four navigation queries. There is no debugger tool.

SuperGrok OAuth is implemented, documented, and tested, including billing-proxy usage and the `xai` versus `xai-oauth` split. For this project's Grok-fixed thesis that is not a convenience. It is the pin.

TUI, print, JSON, RPC, ACP-as-editor, and collab are one binary. Headless `omp -p --mode json --model grok-4.6 --approval-mode write` is a scriptable eval command with flags the Wave 1 protocol can freeze.

Memory backends, stream-rule injection, and an advisor model are productized. Cross-session lessons are a first-party path.

Issue tracker is on. You can file a bug against the loop you are measuring.

## Where DeepSeek Harness is better

The loop is a plugin. Session log is the source of truth, with an invariant that model-visible traffic is reconstructable. Snapshot tests pin assembled transcripts. That is a better scientific object than a TUI product that happens to have `--print`.

Safety defaults match how you would want an agent to touch a repo you care about. Fail-closed approval, `ask` as the interactive default, `never` for unattended CI, Landlock/Seatbelt/Windows ACL sandbox with an honest `partial` enforcement bit. OMP's yolo default is the opposite bet.

Capability seams mean one filesystem/subprocess provider swap moves bash, PTY, and LSP together, including toward a remote sandbox. Subagent providers can be another lab's CLI. That is how you compose harnesses rather than pick one forever.

First-party DeepSeek V4 adapter, credential references that never land in config, and a Web UI that is the documented product. If the model under test is DeepSeek, this is the native runtime in a way OMP is not.

Testing policy is stricter on paper: coverage gate, Loader-booted real compositions, web GUI snapshots, with-key smokes that the authors refuse to ration because they are DeepSeek. Plugin docs and generated catalogs are drift-checked. The architecture map is something you can audit.

Governance is plugin-shaped. You cannot PR the kernel today, but you also are not supposed to. Contributions land as out-of-tree plugins.

## Evidence table

| Claim | Source | Kind |
| --- | --- | --- |
| OMP identity, 31 tools, Pi fork, MIT, binary `omp` | [README.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/README.md), npm 18.0.4 | Primary |
| 31 tool doc pages | [`docs/tools/`](https://github.com/can1357/oh-my-pi/tree/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/tools) | Primary |
| Hashline default edit + grammar | [`docs/tools/edit.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/tools/edit.md), `packages/hashline` | Primary |
| DAP tool | [`docs/tools/debug.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/tools/debug.md) | Primary |
| LSP 14-action enum | [`docs/tools/lsp.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/tools/lsp.md) | Primary |
| Approval default `yolo` | [`docs/approval-mode.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/approval-mode.md) | Primary |
| SuperGrok `xai-oauth` device-code + default `grok-4.6` | [`docs/provider-quirks.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/provider-quirks.md) | Primary |
| Headless `omp -p` | [`docs/cli-reference.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/cli-reference.md) | Primary |
| Memory backends default off | [`docs/memory.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/memory.md) | Primary |
| Hashline pass-rate table | OMP README | Vendor hypothesis |
| `dsh` identity, Cordis, developer preview, MIT | [README.md](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/README.md) | Primary |
| Loop is a plugin; profiles/bundles; turn/step | [`docs/architecture.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md) | Primary |
| Tool catalog including `str_replace_editor`, `run_code`, four-op `lsp` | [`docs/tool-catalog.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/tool-catalog.md) | Generated primary |
| Fail-closed approval; `ask`/`never` | [`docs/subsystems/approval.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/approval.md) | Primary |
| Sandbox modes + Landlock/Seatbelt/ACL | [`docs/subsystems/sandbox.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/sandbox.md) | Primary |
| Presets `workspace-write`+`ask` | [`docs/subsystems/permission-presets.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/permission-presets.md) | Primary |
| `dsh-llm-pi-ai` uses `@earendil-works/pi-ai`; `xai` in catalog tests | [package README](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/llm/llm-pi-ai/README.md), `catalog.spec.ts` | Primary |
| Official DeepSeek adapter defaults V4 Flash/Pro | [`packages/llm/llm-deepseek/README.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/llm/llm-deepseek/README.md) | Primary |
| Headless profile; web on :3080 | [apps/cli README](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/apps/cli/README.md), root README | Primary |
| No external PRs; Discussions | [CONTRIBUTING.md](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/CONTRIBUTING.md) | Primary |
| Testing tiers and 100% gate | [`docs/testing.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/testing.md) | Primary |
| ACP automation-only | [`packages/acp/acp/README.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/acp/acp/README.md) | Primary |
| GitHub metadata 2026-08-25 | API: OMP 27300 stars, 1768 open issues+PRs; `dsh` 193830 stars, issues disabled, 4457 Discussions | Snapshot, not quality |
| Zagens is a different DeepSeek-V4 harness | [didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens) | Disambiguation only |

## Unknowns and limits

This pass cloned `--depth 1` and read docs plus selected tests. It did not boot either binary, run either test suite, or complete OAuth. Whether SuperGrok OAuth can be mounted on `dsh` via a community plugin was not verified. Whether `dsh` headless can select `xai/grok-4.6` from documented settings.yaml was not executed. Landlock `full` versus `partial` on this kernel was not measured. Hashline lifts remain unreproduced. Star counts were not audited for inflation. A `dsh` TUI profile may exist out of tree. Agent Teams and `dsh-tool-cordis` are documented as opt-in. Default `web` composition was not dump-config verified.

## What a fair empirical eval still needs

Hold the model fixed. For Grok science that means one slug and one auth class. Candidate A is SuperGrok OAuth `xai-oauth/grok-4.6` on OMP. Candidate B on `dsh` is only fair if the same OAuth ledger can be used. If it cannot, report `dsh`+`XAI_API_KEY` as a different system, or drop Grok and run DeepSeek V4 Flash as `dsh`'s native cell against OMP's DeepSeek provider.

Pin approval. Do not compare OMP yolo to `dsh` ask. A defensible pair is OMP `write` or `always-ask` versus `dsh` `workspace-write`+`ask`, plus a second cell of OMP yolo versus `dsh` `danger-full-access`+`never` if the question is unattended throughput.

Pin tools that change the independent variable. Disable OMP memory backends and advisor unless those are the treatment. Disable `dsh` Codex/Claude subagent providers, Agent Teams, and schedule plugins. Log whether each edit was hashline, replace, or str_replace.

Use headless entry points: `omp -p --mode json` and `dsh --profile headless`, both with a wall-clock cap. Pin git SHAs, not latest npm. Tasks should include at least one LSP-rename, one failing test loop, and one stale-file edit if the hypothesized mechanism is hashline. Do not score until those pins are in the eval log. Architecture reading is not a leaderboard.
