# OMP pairwise synthesis

**Status:** academic synthesis of completed pairwise papers. No scored runs. No invented ranks.  
**Date:** 2026-08-25  
**Question:** Across nine OMP pairwise papers, which design claims survive as systematic, which advantages are comparator-specific, and what that implies for Track A versus Track B.

This note does not re-research the harnesses from scratch. Primary evidence is the pairwise papers listed below. GitHub URLs are those the papers already cited. Vendor README numbers stay labeled vendor.

Pairwise sources (open PRs unless noted):

| Comparator | Paper | PR |
|---|---|---|
| DeepSeek Harness (`dsh`) | [`omp-vs-deepseek-harness.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-deepseek-harness-8f61/research/omp-comparisons/omp-vs-deepseek-harness.md) | [#7](https://github.com/bnivanov/llm-harness-eval/pull/7) |
| Zagens (spoken "Zazen") | [`omp-vs-zazen.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-zazen-bedb/research/omp-comparisons/omp-vs-zazen.md) | [#5](https://github.com/bnivanov/llm-harness-eval/pull/5) |
| Cline | [`omp-vs-cline.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-cline-a8df/research/omp-comparisons/omp-vs-cline.md) | [#12](https://github.com/bnivanov/llm-harness-eval/pull/12) |
| Hermes Agent | [`omp-vs-hermes.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-hermes-ccf6/research/omp-comparisons/omp-vs-hermes.md) | [#10](https://github.com/bnivanov/llm-harness-eval/pull/10) |
| Claude Code | [`omp-vs-claude-code.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-claude-code-07ea/research/omp-comparisons/omp-vs-claude-code.md) | [#9](https://github.com/bnivanov/llm-harness-eval/pull/9) |
| Kilo Code | [`omp-vs-kilo-code.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-kilo-code-10a5/research/omp-comparisons/omp-vs-kilo-code.md) | [#11](https://github.com/bnivanov/llm-harness-eval/pull/11) |
| Codex | [`omp-vs-codex.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-codex-3995/research/omp-comparisons/omp-vs-codex.md) | [#8](https://github.com/bnivanov/llm-harness-eval/pull/8) |
| ZCode | [`omp-vs-zcode.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-zcode-54f4/research/omp-comparisons/omp-vs-zcode.md) | [#6](https://github.com/bnivanov/llm-harness-eval/pull/6) |
| Prime Agent | [`omp-vs-prime-agent.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/omp-vs-prime-agent-12dc/research/omp-vs-prime-agent.md) | [#4](https://github.com/bnivanov/llm-harness-eval/pull/4) |

OMP snapshots in those papers converge on [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) commit `969a94c1` (2026-08-24), binary `omp`, npm `@oh-my-pi/pi-coding-agent` 18.0.4, MIT, Stencil Labs / Can Bölük, fork of Mario Zechner's Pi.

---

## Identity and category map

These nine comparators are not nine members of one class. A single success% column would mix lab-locked products, personal runtimes, plugin kernels, and IDE platforms with a terminal coding fork. The Wave 1 adversarial review already said that. The pairwise papers confirm it at product resolution.

Resolved identities (do not reopen unless a later paper is unsure):

| Spoken / written name | Resolved product | Kind | Coding SUT? |
|---|---|---|---|
| OMP / Oh My Pi / `omp` | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | OSS coding CLI, Pi fork | Yes. Track A batteries cell. |
| DeepSeek / `dsh` | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | First-party plugin runtime on [Cordis](https://github.com/cordiverse/cordis) | Yes, but DeepSeek-native. Not Zagens. Not the DeepSeek model. |
| Zazen | No 2026 coding harness found | Filename only | Compare **Zagens**. |
| Zagens | [didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens) | OSS DeepSeek-V4 agent platform (Kernel V3) | Yes, as a DeepSeek-family platform. Not `dsh`. |
| Cline | [cline/cline](https://github.com/cline/cline) | Model-agnostic IDE agent + CLI/SDK | Yes. Parent of Roo/Kilo *product DNA*, not of Kilo's 2026 engine. |
| Hermes | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Personal / learning agent; coding is an affordance | Only under constraints. Not a coding-first SUT. |
| Claude Code | Anthropic product; GitHub is a [tracker](https://github.com/anthropics/claude-code) | Vendor ADE / lab family (CLI, IDE, desktop, web) | Yes as Track B ceiling. Closed loop. |
| Kilo Code | [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) | Multi-surface platform. 2026 engine is an [OpenCode](https://github.com/anomalyco/opencode) fork behind `kilo serve`. Product DNA Cline→Roo. | Yes. Do not collapse into Cline. |
| Codex | [openai/codex](https://github.com/openai/codex) family (CLI/IDE/desktop/cloud) | Vendor ADE / lab family | Yes as Track B OpenAI baseline. Not the 2021 Codex *model*. Not ZCode. |
| ZCode | Z.ai GLM ADE ([zcode.z.ai](https://zcode.z.ai/en)) | Vendor ADE, GLM-5.3-native | Yes as Track B ADE. Closed loop. |
| Prime Agent | [PrimeIntellect-ai/prime-agent](https://github.com/PrimeIntellect-ai/prime-agent) | Experimental RLM agent with a Pi-shaped TUI | Architecture SUT. Same skeleton family as OMP, different loop. |

Four categories, not one column:

1. **Coding SUTs (named-tool CLI loops).** OMP, and as a control not in this pairwise set, Pi. Cline CLI and Kilo `kilo run` can be forced into this category if the protocol freezes headless CLI and disables IDE chrome.
2. **Personal / always-on agents.** Hermes. Memory, gateway, cron, and optional delegation to `grok` / `codex` / `claude` are the product. `omp-vs-hermes.md` and the Wave 1 review agree that SuperGrok OAuth does not make Hermes a Track A coding harness.
3. **Vendor ADEs and lab families.** Claude Code, Codex, ZCode. Multi-surface products co-designed with a lab model. Grok is not the native pin.
4. **Plugin runtimes and DeepSeek-shaped platforms.** `dsh` (Cordis, loop is a plugin). Zagens (Kernel V3, LHT gates, DeepSeek V4 default). Kilo as shipped (OpenCode server plus original gateway, sandbox, memory, IDE rebuilds).

Prime is a fifth kind hiding in the Pi family. `omp-vs-prime-agent.md` is explicit. Pi→OMP moved tooling and edit reliability inside the same class of named-tool loop. Pi→Prime replaced the schema with one `ipython` tool, `rlm()` children, and a Continual Harness. Putting Prime on a Grok-native leaderboard next to OMP double-counts the TUI skeleton and under-samples non-Pi Grok-capable CLIs.

---

## Where OMP is systematically better

Only claims that survive against several comparators, not one-off product wins.

**Hashline is the recurring independent variable.** Default `edit` binds hunks to a four-hex content hash from the latest read. Stale tags reject or recover before a wrong hunk lands. Grammar and tests live in [`packages/hashline`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/hashline/README.md). Every coding pairwise paper names this as OMP's edit bet. The comparators speak `str_replace`, `apply_patch`, Cline `editor`, Hermes `patch`, unpublished ADE `Edit`, or Prime Python I/O. The README table that claims Grok Code Fast 1 went from 6.7% to 68.3% when the format stopped eating the model is a **vendor edit-format microbenchmark** ([Can's post](https://blog.can.ac/2026/02/12/the-harness-problem/)). No pairwise paper reproduced it. The mechanism still survives as a column a later eval must log, not as a Wave 1 score.

**Language tools are in the CLI, not borrowed from an IDE host.** Fourteen LSP operations including rename through `workspace/willRenameFiles`, twenty-eight DAP operations, `ast_edit` / `ast_grep`, persistent `eval` kernels that re-enter agent tools. `dsh` keeps a four-op LSP seam and no DAP. Cline and Hermes treat LSP as post-write diagnostics. Kilo's `lsp` is experimental. Codex and Claude Code lean on shell, MCP, or plugins. ZCode and Prime do not ship a matching first-party catalog. Against IDE products this means OMP still has rename when you take the editor away. Against other CLIs it is a thicker coding surface.

**Grok is a documented pin, not a rumor.** Provider `xai-oauth` is SuperGrok / X Premium+ device-code OAuth against `https://auth.x.ai`, default slug `grok-4.6`, separate from paid `xai` / `XAI_API_KEY` ([provider quirks](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/provider-quirks.md)). Ten roles pin `provider/modelId`. Headless `--model` is a launcher flag. That combination is what Track A needs. `dsh` can call xAI through `@earendil-works/pi-ai` as a plugin. That is API-shaped xAI, not SuperGrok device login, and does not make `dsh` an OMP derivative. Cline and Kilo are `XAI_API_KEY` or Gateway. Prime's official providers list is API key only. Claude Code, Codex, ZCode, and Zagens are not Grok-native products. Hermes *does* implement `xai-oauth` with the same default slug. Necessary, and not sufficient for Track A, because Hermes can still shell out to `grok -p`.

**The loop is inspectable and the binary is scriptable.** MIT monorepo. Pin a git SHA. `omp -p`, `--mode json|rpc|acp`, `--approval-mode`, `--tools`, `--max-time`. In-tree metaharness and the TypeScript edit benchmark exist to measure the edit claim. Claude Code's GitHub is a tracker ([issue #47465](https://github.com/anthropics/claude-code/issues/47465)). ZCode has no public ADE loop. `dsh` is MIT but a developer preview that refuses external kernel PRs. For this repo's hold-the-model-fixed question, a loop you can read is the object, not a courtesy.

**Default memory will not leak a person into a fixture.** `memory.backend` is `off` unless configured (`local` / `hindsight` / `mnemopi`). Hermes injects `MEMORY.md` / `USER.md` by default (`omp-vs-hermes.md`). That contrast is eval-shaped. It is not a claim that OMP learns better.

**Instruction-file inheritance is broader than the IDE natives.** OMP reads Cursor MDC, Cline `.clinerules`, Codex `AGENTS.md`, Copilot `applyTo`, Claude, Gemini, Windsurf in place. Cline does not ship a symmetric `.omp` importer. ZCode wants workspace-root `AGENTS.md` only. Kilo injects `.kilocoderules` and does not ingest `.roorules` / `.clinerules`. Practical onboarding, not a quality score.

**Coding specialization versus adjacent jobs.** Against Hermes, OMP is the coding SUT and Hermes is the learning/memory personal agent (`omp-vs-hermes.md`). Against Prime, OMP is still a named-tool coding IDE and Prime is a REPL/RLM research runtime (`omp-vs-prime-agent.md`). Those are category facts that survive because both papers refuse to score the mismatch as intelligence.

What does *not* survive as a systematic OMP win: safety defaults, OS sandbox, long-horizon completion gates, IDE/cloud surface families, event-sourced replay, or "more tools therefore better." Tool cardinality itself drifts in the papers (README "31", `builtin-names.ts` 29 or 30 plus hidden/gated names). Count is not the thesis. Hashline, LSP/DAP, and a writable Grok pin are.

---

## Where the other harness is better

Organized by comparator, then by axis. Design advantages from the pairwise papers, not measured win rates.

### DeepSeek Harness (`dsh`). `omp-vs-deepseek-harness.md`

**Loop.** The agent loop is a Cordis plugin. Session log is the source of truth. Model-visible traffic is reconstructable. Snapshot tests pin assembled transcripts ([architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md)). OMP JSONL sessions fork and resume. They are not an event vocabulary plugins extend by declaration merging.

**Safety.** Fail-closed approval (`allowed-once | rejected | cancelled | unavailable`). Interactive default `ask`. Headless `never`. Sandbox modes `read-only` / `workspace-write` / `danger-full-access` with Linux bwrap/Landlock, macOS Seatbelt, Windows ACL ([sandbox.md](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/sandbox.md)). OMP default `yolo` is the opposite bet ([approval-mode.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/approval-mode.md)).

**Eval fitness.** Coverage gate, Loader-booted compositions, web Chromium snapshots, with-key smokes that skip without secrets. First-party DeepSeek V4 adapter. If the model under test is DeepSeek, this is the native runtime.

**Surfaces / model-pin.** Documented product is `dsh web` on `:3080`. Headless is a profile, not `dsh --model grok-4.6`. Grok on `dsh` is composition.

### Zagens. `omp-vs-zazen.md`

**Loop.** Kernel V3 is event-sourced. Events double-write to SQLite `kernel_events`. Golden replay fixtures live in CI ([AGENT_KERNEL_V3.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/tech/AGENT_KERNEL_V3.md)). LHT plus composable gates refuse prose-only "done." Iron rule: no LLM as judge. Adjudication is exit codes and path hits ([COMPOSABLE_HARNESS.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/harness/COMPOSABLE_HARNESS.md)). OMP todos still sit inside a loop that ends when the model stops calling tools.

**Safety.** Example config `approval_policy = "on-request"`, `sandbox_mode = "workspace-write"`. Seatbelt / restricted-token+WFP / bwrap, Landlock still degraded in the matrix at freeze ([SANDBOX_CAPABILITY_MATRIX.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/tech/SANDBOX_CAPABILITY_MATRIX.md)).

**Model-pin.** Default `deepseek-v4-pro`. Byte-stable tool catalogs for DeepSeek KV prefix cache. Not a Track A cell.

**Surfaces.** Tauri desktop plus `zagens-tui` plus `zagens exec`. Desktop Windows-only at v0.9.0.

### Cline. `omp-vs-cline.md`

**Loop.** Plan/Act is a control system: tool presets, command-guard hook, prompt contracts, mode-tagged user messages. OMP plan mode is a write fence plus optional `modelRoles.plan` swap.

**Safety.** HITL default. VS Code forces governed tools to `autoApprove: false`. Workspace undo via git stash/ref checkpoints (`/undo`). OMP default checkpoint rewinds *conversation*, not the tree. Example git-checkpoint hook is not Cline's `/undo`.

**Surfaces.** VS Code is the product. JetBrains is a closed client on the shared core. CLI `--json` / `--yolo` / pipe. Cron, messaging, teams.

**Eval fitness.** `cline --json`, stdin piping, `evals/` with pass@k analysis, even while Layer 2 smoke tests were partially disabled during the SDK CLI migration.

**Model-pin.** Hybrid ClinePass / BYOK / ChatGPT-plan OAuth. Grok is `XAI_API_KEY`, not SuperGrok OAuth. Common Grok class with OMP is likely the API-key ledger, which drops OMP's SuperGrok advantage on purpose.

### Hermes Agent. `omp-vs-hermes.md`

**Loop / tools.** Personal runtime. ~90 tools in toolsets. Seven terminal backends (local, Docker, SSH, Singularity, Modal, Daytona, Vercel Sandbox). Coding posture exists and still is not OMP's job.

**Safety.** `SECURITY.md` names the OS as the only load-bearing boundary. Isolation that counts is a non-default terminal backend. Subagent auto-approve defaults to deny. Oneshot `hermes -z` still forces YOLO.

**Surfaces.** CLI, Electron desktop, web dashboard, ACP, cron, 20+ messaging adapters. "Talk to it from Telegram while it works on a cloud VM."

**Eval fitness.** Trajectory pipeline (`batch_runner.py`, `mini_swe_runner.py`) aimed at training data. Compaction recall evals. Nested `grok` / `codex` / `claude-code` skills must be **off** or the row is another harness scored twice.

**Model-pin.** SuperGrok OAuth is real (`~/.hermes/auth.json`, default `grok-4.6`). Separate from `~/.grok/auth.json`. Issue #26847 records SuperGrok tiers returning HTTP 403 on OAuth inference, silently becoming `XAI_API_KEY`.

### Claude Code. `omp-vs-claude-code.md`

**Surfaces.** Terminal, IDE extensions, desktop, claude.ai/code, mobile, Slack, GitHub Actions, `claude --teleport`. Settings, CLAUDE.md, and MCP are supposed to follow the engine.

**Safety.** Permission modes including Auto with a background classifier. Org policies local settings cannot punch through. Seatbelt / bubblewrap Bash sandbox. File checkpoints with Esc-Esc rewind. Native Windows sandbox unsupported.

**Loop / context.** CLAUDE.md load order, path-scoped rules, auto memory, `/context`, deferred MCP tool search, `--bare` for clean CI. Subagent product depth: named teammates, workflow scripts, cross-session messaging. Closed source. Claims about internals are documented behavior.

**Model-pin.** Claude-family first. `/login` shares a pool with chat and Cowork. `ANTHROPIC_API_KEY` bills API rates and ignores the plan. Same-Claude API-key cell with OMP is possible. Native Grok cell is not. Gateway retarget is a third harness.

Harbor [PR #44](https://github.com/harbor-framework/terminal-bench-2-1/pull/44) is **Claude Opus 4.7 (max) + Claude Code** on Terminal-Bench 2.1 at 68.9% ± 1.4%. Composite. Not harness-only.

### Kilo Code. `omp-vs-kilo-code.md`

**Loop.** Every surface is a client of `kilo serve` (OpenCode processor). VS Code rebuild GA dated 2026-04-02. Legacy Roo tree is `kilocode-legacy`. Scoring "Kilo vs Cline" is a different paper.

**Safety.** Allow/ask/deny rulesets plus `@kilocode/sandbox` (Seatbelt / bubblewrap). Plan and Ask agents are permission-hardened. `kilo run --auto` is CI yolo.

**Tools / context.** `semantic_search` and `kilo_memory_*` when enabled. `.kilocoderules`. Not `.clinerules`.

**Surfaces.** VS Code, JetBrains, CLI, hosted cloud/review/claw/app. Agent Manager is VS Code-only (parallel chats, git worktrees, one server).

**Model-pin.** Gateway plus optional BYOK. README "500+ models" was **not verified** on the public catalog (369 unique ids on 2026-08-25). `kilo-auto/*` is routing. Log `routedModelID`. SuperGrok OAuth as OMP-style provider: unknown.

**Eval fitness.** `kilo run --auto` is documented CI. In-tree PostHog key gated by `KILO_TELEMETRY_LEVEL`. Merge automation absorbs `anomalyco/opencode` tags (`.opencode-version` `v1.18.13` at freeze).

### Codex. `omp-vs-codex.md`

**Surfaces.** Family: `codex` TUI, `codex exec`, IDE extension, ChatGPT desktop, Codex Web / GitHub review / Slack. Shared `~/.codex/config.toml`. Cloud **requires** ChatGPT login.

**Safety.** OS sandbox default `workspace-write` plus approval `on-request`. Seatbelt, bubblewrap, native Windows sandbox. Cloud secrets stripped before the agent phase.

**Loop / tools.** Lab loop co-designed with GPT. House format `apply_patch`. Narrow local catalog. MCP for the rest. Platform: app-server, official SDK, CLI-as-MCP-server, enterprise RBAC.

**Model-pin.** Not Grok-native. Custom `model_providers` would be a science project that drops cloud and feeds Grok an `apply_patch` dialect OMP argues Grok fails. OpenAI vendor claim: ARC-AGI-3 retained reasoning plus compaction raised GPT-5.6 Sol from 13.3% to 38.3% while cutting output tokens sixfold. Composite. Not a Wave 1 number.

**Eval fitness.** `codex exec` with JSON events. Public stable tag `rust-v0.149.1` (2026-08-24). Apache-2.0 harness. Models and cloud stay separate.

### ZCode. `omp-vs-zcode.md`

**Loop.** Closed ADE. Goal Mode is a second loop: after every round a separate check looks for file changes, command output, and tests rather than a confident reply ([goal](https://zcode.z.ai/en/docs/goal)). Usage budget. Pause/resume survives session close.

**Surfaces.** Electron ADE. File manager, terminal, Git, built-in browser with element picker. Remote SSH/Docker. Bot Channel documents WeChat and Feishu. Telegram is a homepage claim not confirmed in the Bot Channel doc fetched 2026-08-25. Headless `zcode --prompt` had reported TUI/OAuth breakage ([feedback#51](https://github.com/zai-org/feedback/issues/51)).

**Safety.** Four execution modes. Default asks before changes. Permission prompts never auto-continue. No documented Landlock/Seatbelt-class sandbox for the default local loop.

**Model-pin.** Official harness for GLM-5.3. Custom Anthropic/OpenAI/OpenRouter providers exist. July 2026 secondary writeups that said ZCode did not support Claude or GPT are stale against official connect-models docs. A Grok-fixed ZCode row is still a lab-stack system, not a harness-only contrast. GLM-5.3 blog benches are **model** scores, often under unspecified harnesses.

### Prime Agent. `omp-vs-prime-agent.md`

**Loop.** One tool, `ipython`. File ops, shell, skills, subagents, and harness CRUD happen as Python in a persistent kernel. `rlm()` children return a handle at admission. Continual Harness state `H = (ρ, G, K, M)` is CRUD-editable. `/refine` applies a small evidence-backed edit. Base system prompt stays immutable.

**Eval fitness.** `--autonomous` with shell gates and turn/token/wall-clock limits. Daemon attach/detach, goals, heartbeats, schedules. Built as an unattended research runtime. Official README: **not a security sandbox**. Use a disposable clone.

**Model-pin.** `XAI_API_KEY` only in official provider docs. SuperGrok OAuth incomplete.

**Vendor numbers.** ARC-AGI-3 **95.5% RHAE Best@1** with Opus 5, plus long-context tables versus Claude Code / Codex / Pi-mono, are Prime Intellect's composites with mixed models. Do not import them into Wave 1.

---

## Comparison matrix

Cells are design facts from the pairwise papers, not scores. "?" means the cited paper left it unverified.

| Axis | OMP | `dsh` | Zagens | Cline | Hermes | Claude Code | Kilo | Codex | ZCode | Prime |
|---|---|---|---|---|---|---|---|---|---|---|
| **Kind** | Coding CLI, Pi fork | Plugin runtime | DeepSeek-V4 platform | IDE agent + CLI | Personal agent | Lab ADE family | OpenCode-fork platform | Lab ADE family | GLM ADE | RLM + Pi TUI |
| **Loop** | Named tools, `agentLoop` | Cordis plugin, event log | Kernel V3 + LHT gates | `AgentRuntime` + Plan/Act | `AIAgent` conversation | Closed gather/act/verify | `kilo serve` processor | Lab loop + `apply_patch` | Closed + Goal Mode | One `ipython` + `rlm()` |
| **Edit** | Hashline default | `str_replace_editor` | `apply_patch` + fuzz | `editor` default | `patch` / `write_file` | Exact `str_replace` | `edit`; GPT `apply_patch` | `apply_patch` | Unpublished `Edit`/`Write` | Python I/O |
| **LSP/DAP** | 14 / 28 tools | LSP 4 ops; no DAP | No matching catalog | IDE diagnostics; no core LSP/DAP | Post-write diagnostics | LSP via plugins; no DAP tool | LSP experimental; no DAP | Shell/MCP | Not documented | Import in Python |
| **Safety default** | `yolo` | `ask` + workspace-write | on-request + workspace-write | HITL (`autoApprove: false`) | smart; oneshot YOLO | Auto + classifier (plan) | rulesets + OS sandbox | workspace-write + on-request | Ask before changes | Not a sandbox |
| **OS sandbox** | No kernel profile | Landlock/Seatbelt/ACL | Seatbelt/WFP/bwrap | Not found in SDK core | Optional Docker/SSH/cloud | Seatbelt/bwrap (no native Win) | Seatbelt/bwrap | Seatbelt/bwrap/Win sandbox | Not documented | Isolation ≠ security |
| **Surfaces** | TUI, `-p`, RPC, ACP | Web-first, headless profile | Desktop (Win), TUI, `exec` | VS Code, JB, CLI, SDK | CLI, desktop, gateway, ACP | CLI, IDE, desktop, web, cloud | VS Code, JB, CLI, cloud | CLI, IDE, desktop, cloud | Electron ADE + bots | TUI, daemon, `-p` |
| **Grok pin** | `xai-oauth` + `xai`; `grok-4.6` | API via pi-ai catalog; no xai-oauth | Not product | `XAI_API_KEY` only | `xai-oauth` (nested `grok` risk) | No native | BYOK `xai`; SuperGrok **?** | No as product | Custom provider ≠ native | `XAI_API_KEY` only |
| **Headless** | `omp -p --mode json` | `--profile headless` | `zagens exec --json` | `cline --yolo --json` | `hermes -z` (forces YOLO) | `claude -p --bare` | `kilo run --auto` | `codex exec` | Bundled CLI, reported breakage | `prime-agent -p` / `--autonomous` |
| **Source** | MIT, full tree | MIT, no external kernel PRs | MIT, small repo | Apache-2.0; JB closed | MIT | Proprietary tracker | MIT (OpenCode + Kilo) | Apache-2.0 harness | Proprietary ADE | MIT |
| **This repo's track** | A (with Pi, Grok Build) | B DeepSeek-native | B/C DeepSeek long-horizon | B OSS IDE | C personal-runtime | B ceiling | B OpenCode-family | B OpenAI baseline | B GLM ADE | C architecture |
| **Cited paper** | all | `omp-vs-deepseek-harness.md` | `omp-vs-zazen.md` | `omp-vs-cline.md` | `omp-vs-hermes.md` | `omp-vs-claude-code.md` | `omp-vs-kilo-code.md` | `omp-vs-codex.md` | `omp-vs-zcode.md` | `omp-vs-prime-agent.md` |

---

## Tensions and conflicts

The pairwise papers mostly agree. Where they do not, prefer GitHub-cited claims.

**Tool cardinality on the same OMP SHA.** Papers count 29, 30, or 31 names depending on whether they read `docs/tools/`, `builtin-names.ts`, or the README. Documentation drift inside freeze `969a94c1`, not a disagreement about hashline or LSP/DAP. Log `--tools` at run time.

**Marketing versus GitHub.** Kilo README "500+ models" versus a public Gateway fetch of 369 ids. Prefer the fetch. Zagens `RUNTIME_ARCHITECTURE.md` still names a deleted TUI. README v0.9.0 ships `zagens` / `zagens-tui` / `zagens-runtime`, and Office mode was removed. Prefer README plus crates. Cline SDK checkpoints default off while the README implies `/undo` in the UI. Surface-specific. Hermes architecture.md test census is stale versus `tests/` at HEAD.

**Apparent identity fights that are not fights.** `dsh` and Zagens both say DeepSeek. The papers agree they are different products: first-party Cordis versus third-party Kernel V3, NOTICE lineage CodeWhale. Kilo and Cline papers agree not to collapse them. Cline is the Plan/Act parent. Kilo's 2026 engine is an OpenCode fork. Prime SuperGrok is API-key only in official docs. Hermes and OMP SuperGrok are different trees. July 2026 blogs that said ZCode lacked Claude/GPT are stale against official connect-models docs. The ADE loop remains sold as GLM-5.3's harness.

No pairwise paper claims a task winner. Several quote vendor benches. Those remain vendor.

---

## Fair empirical eval still needed

Architecture reading is not a leaderboard. `evaluation-log.md` is still empty. One protocol that could actually be run:

**Freeze the question in the log header.** Either Track A (harness effect under pinned Grok) or a labeled system row (lab stack × default model × auth × surface). Never both in one success% column.

**Shared pins for every scored cell**

1. `binary_version` and git SHA (or installer version for closed ADEs).
2. `model_slug` as a concrete id, not a picker default and not `kilo-auto/*`.
3. `auth_class`: `oauth-supergrok` | `xai-api-key` | `anthropic-login` | `anthropic-api-key` | `chatgpt-plan` | `openai-api-key` | `glm-coding-plan` | `glm-api-key` | `deepseek-official` | `kilo-gateway` | `openrouter`. Do not mix ledgers inside a table titled "harness only."
4. `surface`: headless CLI only for the scored rectangle. Exact argv in the matrix. IDE, desktop, cloud, and bots are separate experiments.
5. `approvalMode` / sandbox. Do not compare OMP default `yolo` to anyone's ask/workspace-write and call the faster one smarter. Pair OMP `write` or `always-ask` with the comparator's interactive default, or run a second unattended cell of OMP `yolo` versus `never` / `--auto` / `danger-full-access`.
6. `edit_format` as its own column: hashline | str_replace | editor | apply_patch | patch | python-io | unpublished. Failed apply is not harness IQ.
7. Memory, advisor, nested lab-CLI skills, Agent Teams, `/refine`, MCP extras: off unless they are the treatment.
8. Three pre-declared tasks (repair / feature / refactor), shared prompt text, fixture SHAs, wall-clock cap, test oracle. Score the *task*, not first-try patch apply. Include one rename-shaped refactor if LSP is the hypothesized mechanism, and one stale-file multi-edit if hashline is.

**Grok-pinnable versus model-locked**

| Cell | Grok-pinnable as product? | Honest pin | Notes |
|---|---|---|---|
| OMP | Yes | `xai-oauth/grok-4.6` or `xai/grok-4.6` | Track A. Do not mix those two auth classes. |
| Pi (Track A control, not in this pairwise set) | Yes | Same slug and `auth_class` as OMP | The only clean delta. |
| Grok Build | Native, likely `grok-build-0.1` | Label as system row if un-pinnable to BYOK slug | Wave 1 review. |
| Hermes | Yes, with traps | `xai-oauth/grok-4.6`, grok/codex/claude skills **off**, fresh `--profile`, memory off | Track C footnote, not unconstrained Track A. |
| Cline | API-key only | Shared class is `XAI_API_KEY` or OpenRouter | Drops SuperGrok. |
| Kilo | BYOK `xai`; SuperGrok **?** | Concrete `provider/model-id`; disable `kilo-auto/*`; log `routedModelID` | Gateway credits ≠ SuperGrok. |
| Prime | `XAI_API_KEY` only | Label `xai-api-key`; freeze `/refine` | Track C. |
| `dsh` | API via catalog, not xai-oauth | Same `XAI_API_KEY` as OMP, or drop Grok and run DeepSeek V4 native | Track B DeepSeek, or a labeled Grok-via-key system. |
| Zagens | Not product | Same DeepSeek V4 id and base URL on OMP and Zagens | Track B/C. A Grok-only OMP arm is not this pair. |
| Claude Code | No native | Same Claude API model id + `ANTHROPIC_API_KEY` + `--bare`, or Track B `/login` system | Gateway+Grok is a third harness. |
| Codex | No as product | Track B: Codex × default GPT/Codex SKU × auth × sandbox | Custom Grok provider is a stunt. |
| ZCode | Custom provider ≠ native | GLM-5.3, same endpoint, both clients; record `[1m]` and thought level | Skip scored ZCode if official CLI login is broken. |

**Minimum publishable rectangles**

- Track A: Grok Build × Pi × OMP, one slug, one auth class, three tasks, headless, nine runs before any rank. OMP's science pair is Pi, not Codex.
- Track B systems, separate files: Codex (OpenAI native), Claude Code (ceiling), `dsh` (DeepSeek native), ZCode (GLM ADE), Kilo (OpenCode-family, with OpenCode itself as control if funded), Cline (IDE+CLI parent).
- Track C architecture: Prime (REPL/RLM), Zagens (gates + replay), Hermes (personal-runtime coding loop, constrained).

Until those pins exist, the only honest ranking is architectural.

---

## Implications for Track A versus Track B

[`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md) already said publishable Wave 1 is Track A: **Grok Build × Pi × OMP**, pinned slug, pinned auth, three tasks, headless. The nine pairwise papers do not reopen that membership. They thicken the reasons.

**Track A stays small.** OMP vs Pi is the only clean experiment in this set: same lineage, same class of loop, independent variable = tools + hashline + LSP/DAP. Prime looks related and is not. It changes the schema. Hermes looks Grok-native because OAuth exists and is not, unless nested skills and memory are frozen. Cline and Kilo can pin a Grok key. They cannot sit next to SuperGrok OAuth OMP without relabeling the ledger. Codex, Claude Code, ZCode, `dsh`, and Zagens fail the native pin.

**Track B is where the pairwise work earns its keep.** The papers supply honest system rows the original Wave 1 zoo tried to cram into a Grok-native header. Codex without Claude Code is still a half baseline. Claude Code is the missing ceiling, never a Grok SUT. Kilo is an OpenCode-family platform, not a Cline rename. `dsh` is the DeepSeek-native plugin runtime. Zagens is the DeepSeek-shaped gate-and-replay platform. Mixing those two because both say DeepSeek repeats the Amp/FX/Codex mistake. ZCode is the GLM ADE. A GLM-5.3 pin on OMP versus ZCode Agent is a real Track B cell. A Grok-fixed ZCode cell is not.

**Do not average categories.** OMP's systematic strengths (hashline, LSP/DAP, inspectable Grok pin, headless flags) are the Track A independent variables. The others win on OS sandbox, Plan/Act, Goal Mode, LHT gates, event logs, IDE/cloud families, personal memory. Those are different questions. One success% column will crown whoever does not wait for a human, or whoever's model was jointly trained with the wrap, and call it harness quality.

**Vendor numbers stay in footnotes.** OMP hashline 6.7%→68.3%, OpenAI ARC-AGI-3 13.3%→38.3%, Harbor 68.9% Opus+Claude Code, Prime 95.5% RHAE Best@1, Kilo "500+", GLM-5.3 blog benches. First-party or composite. Not this project's results.

The claim this repo can currently defend is narrower than a community ranking. OMP is the open, Grok-pinnable, IDE-wired Pi fork that Track A is for. The other eight products win on axes Track A is not measuring. Run the 3×3 before adding any of them to a scored table.

---

## Sources

Pairwise papers as in the opening table. Trees those papers already used, retrieved 2026-08-25 unless a paper froze an earlier SHA:

- OMP: [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) `@969a94c1`
- `dsh`: [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) `@b150a551`
- Zagens: [didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens) `@a55959f7`
- Cline: [cline/cline](https://github.com/cline/cline) `@491b30b`
- Hermes: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) `@0268c0b8`
- Claude Code docs: [code.claude.com/docs](https://code.claude.com/docs/en/overview); tracker [anthropics/claude-code](https://github.com/anthropics/claude-code)
- Kilo: [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode); OpenCode pin `v1.18.13`
- Codex: [openai/codex](https://github.com/openai/codex) `rust-v0.149.1`; [developers.openai.com/codex](https://developers.openai.com/codex)
- ZCode: [zcode.z.ai/en](https://zcode.z.ai/en)
- Prime: [PrimeIntellect-ai/prime-agent](https://github.com/PrimeIntellect-ai/prime-agent)

This repo, method only: [`BRIEF.md`](../../BRIEF.md), [`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md), [`landscape/agentic-tools-subscription-vs-byok.md`](../../landscape/agentic-tools-subscription-vs-byok.md).
