# OMP vs Zazen: pairwise comparison of Oh My Pi and Zagens

**Repo:** [bnivanov/llm-harness-eval](https://github.com/bnivanov/llm-harness-eval)
**Date:** 2026-08-25
**Sources frozen:** OMP `969a94c1eeccb1b7528cd5621934bca1908ab622` (2026-08-24); Zagens `a55959f77b3382e0b3709460ac97c4540fdec973` (2026-08-01, tag line v0.9.0)
**This filename** stays `omp-vs-zazen.md` because the request named Zazen. The product under comparison is **Zagens**.

No scores. Vendor README numbers are labeled as claims and are not treated as measurements.

---

## Method

Primary evidence is GitHub source: README, architecture docs, loop/tool implementations, tests, CI workflows, licenses. Vendor blogs and in-tree marketing articles are secondary. Star counts are popularity, not quality.

Axes: architecture and control loop; tools; context and memory; auth and model pinning; surfaces; extensibility; safety and approvals; multi-agent; OSS vs proprietary; eval and reproducibility.

This paper is a **design comparison**. It does not claim which harness wins on SWE-bench, Terminal-Bench, or this project's Wave 1 tasks.

---

## Identity: Zazen is Zagens

The user asked for **Zazen**. The closest public coding harness is **Zagens** ([didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens)): an MIT Rust agent platform for DeepSeek V4, Kernel V3 event-sourced turns, Tauri desktop plus `zagens-tui` plus headless CLI, and composable completion gates documented as LHT.

**Search performed 2026-08-25.** GitHub `gh search repos "zazen"` plus web queries for `"zazen" coding agent/harness` returned no 2026 coding-agent harness named Zazen. Hits that were discarded:

| Hit | Why discarded |
| --- | --- |
| [stormwarning/zazen-eslint-config](https://github.com/stormwarning/zazen-eslint-config) | ESLint `@zazen` config, archived |
| [zenchain-protocol/zazen](https://github.com/zenchain-protocol/zazen) | MetaMask Zenchain snap for validator keys |
| [zazencodes/*](https://github.com/zazencodes) | YouTube/course repos, not an agent loop |
| vim colorschemes, meditation timers, voxel engines | Unrelated |

No stronger-named Zazen coding harness exists in the public 2026 search window. **Decision: compare OMP vs Zagens.** If a later product actually named Zazen ships a coding loop, reopen this identity table before scoring.

**Do not confuse Zagens with:**

- DeepSeek first-party **`dsh`** / [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness). That is a Cordis "everything is a plugin" runtime. Separate paper.
- **Z.ai ZCode**, a GLM-family ADE. Different vendor, different model lock.
- **CodeWhale / deepseek-tui**, which Zagens [NOTICE.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/NOTICE.md) names as *runtime lineage*. From v0.7.x the Kernel V3 loop diverges; NOTICE says upstream turn-engine merge is no longer feasible.

Zagens' own [docs/article-deepseek-agent-comparison.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/article-deepseek-agent-comparison.md) still argues Office `write_office` as a differentiator. The v0.9.0 README says built-in Office mode was **removed**. Treat that article as stale vendor copy.

### Identity table

| Name as spoken / written | Resolved product | Kind | Role in this paper |
| --- | --- | --- | --- |
| OMP / Oh My Pi / `omp` / `@oh-my-pi/pi-coding-agent` | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | OSS coding harness, Pi fork | Primary left-hand SUT |
| Zazen | **No product found** | Misspelling / mishearing | Filename only |
| Zagens | [didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens) | OSS DeepSeek-V4 agent platform | Right-hand comparator |
| `dsh` / DeepSeek Harness | deepseek-ai/deepseek-harness | First-party plugin runtime | Out of scope |
| ZCode | Z.ai ADE | Proprietary GLM ADE | Out of scope |
| CodeWhale / deepseek-tui | Upstream lineage of Zagens sidecar | Different product | Cited only as NOTICE lineage |

---

## Snapshots

**OMP.** TypeScript + Rust monorepo. Binary `omp`, npm `@oh-my-pi/pi-coding-agent`, [omp.sh](https://omp.sh). MIT. LICENSE credits Mario Zechner, Can Bölük, and Stencil Labs. Explicit fork of [Pi](https://github.com/badlogic/pi-mono); [docs/porting-from-pi-mono.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/porting-from-pi-mono.md) still tracks a 2026-03-22 upstream marker. At freeze: ~27,300 stars, 2,671 forks, created 2025-12-31. Default surface is a terminal TUI; headless `-p`, RPC, and ACP are first-class.

**Zagens.** Rust workspace `0.9.0` in [Cargo.toml](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/Cargo.toml). MIT. [zagens.com](https://www.zagens.com/). At freeze: 15 stars, 2 forks, created 2026-06-07. README is a **DeepSeek V4** local platform, not hosted SaaS. Default model in [config.example.toml](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/config.example.toml) is `deepseek-v4-pro`. The config banner says it is not affiliated with DeepSeek Inc.

These are not two skins of the same loop. OMP is a model-agnostic daily coding CLI grown from Pi's four-tool skeleton. Zagens is a DeepSeek-shaped sidecar with an event log and completion gates. Holding "harness" fixed and swapping the name already smuggles incompatible independent variables. Wave 1's adversarial review said that about Pi vs OMP vs Prime. This pair is worse.

---

## Architecture and control loop

**OMP** keeps a classical agent loop. [`packages/agent/src/agent.ts`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/agent/src/agent.ts) calls `agentLoop` in [`agent-loop.ts`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/agent/src/agent-loop.ts): transform context, convert to LLM messages, stream, execute tools, next turn. [`packages/agent/README.md`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/agent/README.md) documents `prompt()` as `agent_start` → turns of LLM + tools → `agent_end`. Compaction is a session rewrite, not an event-sourced kernel: [docs/compaction.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/compaction.md) lists six triggers including overflow recovery and mid-turn threshold maintenance. SnapCompact can archive history as dense bitmaps. There is no append-only `KernelEvent` table that a replay machine must re-derive.

**Zagens** replaced the imperative turn loop. [docs/tech/AGENT_KERNEL_V3.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/tech/AGENT_KERNEL_V3.md) says Kernel V3 landed 2026-06-16 as the sole production path. Entry is `handle_deepseek_turn` in [`crates/core/src/engine/turn_loop/run.rs`](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/crates/core/src/engine/turn_loop/run.rs). `LiveTurnMachine` plans effects; `EffectInterpreter` runs them; events double-write to SQLite `kernel_events`. Resume is log-first. Golden fixtures live under [`fixtures/harness/kernel-v3-replay/`](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/fixtures/harness/kernel-v3-replay/README.md); CI runs `cargo test -p zagens-core golden_replay`.

The interesting Zagens bet is **not trusting the model when it says done**. [docs/harness/LONG_HORIZON_CODE_TASKS.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/harness/LONG_HORIZON_CODE_TASKS.md) and [COMPOSABLE_HARNESS.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/harness/COMPOSABLE_HARNESS.md) specify layered gates: operator manifest, model `[verify:]` replay, toolchain exit codes. Iron rule in COMPOSABLE_HARNESS: no LLM as judge. Adjudication is exit codes and path/glob hits. OMP has todos, advisor notes, and stream-rule injection ([docs/ttsr-injection-lifecycle.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/ttsr-injection-lifecycle.md)), but those still sit *inside* a loop that ends when the model stops calling tools. Zagens can force continue when the checklist is open.

Doc drift warning: [RUNTIME_ARCHITECTURE.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/tech/RUNTIME_ARCHITECTURE.md) still talks about a `deepseek-runtime` binary and a deleted ratatui TUI. The v0.9.0 README ships `zagens`, `zagens-tui`, and `zagens-runtime`. Prefer README + crates over that ADR snapshot when they conflict.

---

## Tools

**OMP** lists 29 named builtins in [`builtin-names.ts`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/coding-agent/src/tools/builtin-names.ts), including `read`/`bash`/`edit`, `lsp`, `debug`, `task`, `hub`, browser/computer, and memory tools. Hidden: `yield`, `goal`, `think`. README claims 31 tools, 14 LSP ops, 28 DAP ops. The distinctive edit path is **hashline**: [packages/hashline](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/hashline/README.md) binds hunks to a content hash and rejects stale anchors. LSP/DAP are wired into writes and debug sessions, not bolted on as plugins. GitHub is `pr://` / `issue://` on the same FS-shaped `read`. Native in-process grep/glob/brush is the Windows story.

**Zagens** registers `ToolSpec` implementations under [`crates/runtime-server/src/tools/`](https://github.com/didclawapp-ai/zagens/tree/a55959f77b3382e0b3709460ac97c4540fdec973/crates/runtime-server/src/tools). Representative set from README and that tree: files, git, `exec_shell`, `apply_patch` ([apply_patch.rs](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/crates/runtime-server/src/tools/apply_patch.rs) uses unified diffs with fuzz), T4 `assert_*`, T5 `explore_codebase` / `edit_and_check`, intent composites `investigate` / `answer_from_repo` / `change_and_verify`, optional web search, memory, browser CDP, `draft_skill`. [TOOLS_PRINCIPLES.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/tech/TOOLS_PRINCIPLES.md) says the serialized tool catalog is byte-stable so DeepSeek's KV prefix cache hits. That is a model-family constraint OMP does not organize around.

Edit-protocol confound for any later eval: OMP hashline vs Zagens `apply_patch`+fuzz. If patches fail, you measured the format, not "harness IQ." Wave 1 already flagged this for OMP vs Codex vs Pi.

OMP README tables that claim Grok Code Fast 1 went from 6.7% to 68.3% "the moment the edit format stops eating the model" are **vendor claims**. They are not reproduced here.

---

## Context and memory

OMP memory is optional and backend-swappable. [packages/coding-agent/README.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/coding-agent/README.md): `memory.backend` is `off` | `local` | `hindsight`; README also mentions Mnemopi. Tools: `retain`, `learn`, `recall`, `reflect`. Compaction and branch summaries are first-class session entries. Time-traveling stream rules inject mid-token without paying context tax every turn.

Zagens splits "same chat, new brain" from lossy compact. LHT **Cycle** archives the transcript to `~/.zagens/sessions/{id}/cycles/{n}.jsonl` when input tokens cross a threshold defaulting to 768K, then seeds a new buffer with `StructuredState` plus a briefing. `recall_archive` BM25-searches old cycles. Topic memory is its own crate (`crates/topic-memory`). User memory is opt-in via `[memory]` in config, injected as `<user_memory>`. Prefix fingerprints `static_prefix_sha256` / `full_prefix_sha256` are emitted per model step for KV observability.

OMP compaction is a summarizer fighting a context window. Zagens cycle is an archival restart with a checklist that is supposed to survive the swap. Different failure modes: OMP can lose detail in a summary; Zagens can lose mid-edit if a cycle fires on a dirty boundary, which the spec tries to prevent.

---

## Auth and model pinning

This axis decides whether a head-to-head is even a harness comparison.

**OMP** is hybrid BYOK plus lab OAuth. [docs/providers.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/providers.md) lists Anthropic, OpenAI, Gemini, Groq, OpenRouter, Mistral, xAI, Ollama, custom `models.yml`, extension-registered providers. Credential order: CLI `--api-key`, `models.yml`, stored OAuth, `/login` key, env, leftover store. [docs/models.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/models.md) defines roles `default`, `smol`, `slow`, `vision`, `plan`, `designer`, `commit`, `tiny`, `task`, `advisor` as `provider/modelId` selectors. DeepSeek is in the catalog and has a dedicated [toolconv/deepseek.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/toolconv/deepseek.md) for the fullwidth-pipe tool envelope. You *can* pin DeepSeek V4. The product is not built around that pin.

**Zagens** is DeepSeek-first. `provider = "deepseek"` and `default_text_model = "deepseek-v4-pro"` in the example config. Other OpenAI-compatible endpoints are listed: nvidia-nim, openai, openrouter, novita, fireworks, sglang, vllm, ollama, moonshot, and more. README: "Optimized for DeepSeek V4. You bring API keys. We do not host models." There is no SuperGrok OAuth story, no Codex plan login, no Copilot seat. Pinning Grok here is swimming upstream.

For this repo's Track A thesis, hold Grok fixed, vary harness. **Zagens is not a Track A cell.** It is a DeepSeek-family comparator. Pinning the same DeepSeek slug on OMP and Zagens is a different experiment, and a more honest one for this pair.

---

## Surfaces

OMP: interactive TUI, `omp -p` print/headless, `--mode json|rpc|acp|rpc-ui`, Bun SDK `createAgentSession`, Python RPC, ACP into Zed, `/collab` live share. [docs/cli-reference.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/cli-reference.md). Nix, Homebrew, bun, mise. CLI on all three OS.

Zagens: three skins, one engine. Tauri 2 desktop, full-screen `zagens-tui`, headless `zagens exec` / `zagens serve`. Desktop installer is **Windows-only** at v0.9.0; macOS/Linux use TUI or CLI. Desktop talks HTTP+SSE to a sidecar; TUI/CLI can be in-process. Architecture tests try to keep the desktop crate off `core` / `runtime-server` path deps ([`crates/desktop/tests/architecture_boundary.rs`](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/crates/desktop/tests/architecture_boundary.rs)).

If the eval needs headless CI, both have a path: `omp -p` vs `zagens exec --json`. Desktop Zagens is not the SUT unless the task is "operator watching LHT."

---

## Extensibility

OMP: extensions, skills, slash commands, custom TypeScript commands, MCP, plugin marketplace, hooks, SDK tool factories, `models.yml` custom providers. It also *reads other agents' instruction files in place*: Cursor MDC, Cline rules, Codex AGENTS.md, Copilot `applyTo`. That inheritance is a practical onboarding advantage.

Zagens: MCP, skills with **stage gates**, `draft_skill` + human promote ([h4-draft-skill-security.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/harness/h4-draft-skill-security.md)), Gate-as-Code `zagens gate`, hooks, scheduled **night queue**, OpenAPI `/v1/*` sidecar. Extensibility is heavier and more "platform." Skills can carry verify stages the engine enforces. The private `doc_Private/` tree holds eval notebooks the public clone does not ship.

---

## Safety and approvals

Default posture is inverted.

OMP [docs/approval-mode.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/approval-mode.md): `tools.approvalMode` default is **`yolo`**, auto-approving read, write, and exec. Modes `always-ask` and `write` exist. `bash.patterns` can deny or prompt on `rm -rf /` class commands; in yolo a bare critical override is ignored unless the tool or user policy is `prompt`/`deny`. There is no OS Seatbelt/WFP matrix in the docs reviewed. Isolation for subagents goes through `pi-iso` worktrees, not a host sandbox profile.

Zagens example config: `approval_policy = "on-request"`, `sandbox_mode = "workspace-write"`. Modes include `read-only`, `danger-full-access`, `external-sandbox`. [SANDBOX_CAPABILITY_MATRIX.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/tech/SANDBOX_CAPABILITY_MATRIX.md): macOS Seatbelt enforced when `sandbox-exec` exists; Windows elevated sandbox with restricted token + ACL + WFP; Linux bwrap when installed, Landlock still degraded. Runtime Bearer token is kept out of the WebView. [SECURITY.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/SECURITY.md) asks for private vulnerability reports.

An eval that leaves both on defaults is not measuring the same permission world. YOLO OMP vs on-request Zagens will confound "did the agent wait for a human" with "did the agent finish the task."

---

## Multi-agent

OMP: `task` fans out into isolated worktrees with schema-validated yields ([docs/tools/task.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/tools/task.md)). Agent Hub (`Alt+A`) steers, revives, kills. A second **advisor** model watches every turn on its own context ([docs/advisor-watchdog.md](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/docs/advisor-watchdog.md)). `/review` spawns reviewer subagents. `/collab` is multi-human on one agent, not multi-agent.

Zagens: **CRAFT** sub-agents, fix-loop verdicts, P1 blackboard ([docs/craft-v2-improvements.md](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/docs/craft-v2-improvements.md), status still marked draft in places). LHT Phase 4 macro-alternates implementation segments with CRAFT QA. README: gates and CRAFT are "production-usable but still evolving." Sub-agent step journals exist to reduce black-box runs.

OMP's multi-agent feels like a daily-driver fan-out with a human Hub. Zagens' multi-agent is a reliability machine coupled to gates. Neither has public, pinned, cross-harness scores on the same tasks.

---

## OSS vs proprietary

Both MIT, both self-hosted, both BYOK. Neither is a closed lab CLI.

Differences that still matter:

- **Community size.** OMP is a high-traffic fork with npm/Homebrew/Nix distribution. Zagens is a small, young repo. That affects bug surface, prompt tuning, and whether a stranger can get help. It is not a quality oracle.
- **Lineage.** OMP still ports from pi-mono. Zagens still attributes deepseek-tui/CodeWhale and has forked the kernel hard.
- **Private docs.** Zagens parks eval suites in `doc_Private/`. OMP's metaharness, hashline tests, and typescript-edit-benchmark live in the public tree.
- **Affiliation.** Zagens is DeepSeek-*shaped*, not DeepSeek-official. OMP is not xAI-official either, but it treats Grok as one provider among many.

---

## Eval and reproducibility

**OMP** ships eval machinery in-tree: [`packages/metaharness`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/metaharness/README.md) unifies Harbor, TypeScript edit, and SnapCompact runs behind a dashboard; auth stays on a host gateway so containers never see keys. [`packages/hashline`](https://github.com/can1357/oh-my-pi/tree/969a94c1eeccb1b7528cd5621934bca1908ab622/packages/hashline) and `packages/coding-agent/test/` cover edit and security fixtures. [`.github/workflows/ci.yml`](https://github.com/can1357/oh-my-pi/blob/969a94c1eeccb1b7528cd5621934bca1908ab622/.github/workflows/ci.yml) is a large public CI graph.

**Zagens** ships **kernel replay** goldens and LHT TOML fixtures. [`.github/workflows/harness-regression.yml`](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/.github/workflows/harness-regression.yml) is a scheduled headless batch plus a weekly ~35 min stress job that needs an API key; it is deliberately not on every PR. `zagens trace benchmark` and replay packs exist. The docs/harness README says full eval notebooks are maintainer-only.

Replaying a Zagens turn from `kernel_events` is a stronger *engine* reproducibility story than OMP's JSONL transcripts. Reproducing a *task outcome* across machines is easier to start with OMP because `-p`, Harbor adapters, and edit benches are public. Those are different kinds of reproducibility. This project needs the second kind first.

---

## Where OMP is better

1. **Model-agnostic pinning for this repo's science.** Track A wants Grok held fixed. OMP documents `provider/modelId` roles, xAI OAuth and API keys, and a deep catalog. Zagens' default world is DeepSeek V4. You can point Zagens at an OpenAI-compatible Grok endpoint only as a non-native experiment.

2. **Daily coding tool depth.** Hashline, LSP rename-through-writes, DAP against real debuggers, AST edit with accept cards, GitHub-as-filesystem, in-process native search/shell on Windows. That is a thicker coding surface than Zagens' apply_patch + composites. Source: builtin-names, hashline README, docs/tools/lsp.md, docs/tools/debug.md.

3. **Headless and embed surfaces for eval.** `omp -p`, JSON mode, RPC, ACP, Bun SDK. Metaharness already thinks about Harbor trials. Zagens `exec` exists, but the public eval kit is thinner and partly private.

4. **Default operator UX for short tasks.** Interactive TUI plus print mode, no sidecar required. Zagens desktop is a supervised child process; even the TUI is a three-column platform. For "fix this test in 15 minutes," OMP's loop is the smaller object.

5. **Distribution and inspectability.** bun/npm/Homebrew/Nix, 27k stars, public packages under `@oh-my-pi/*`. Easier to install a pinned binary next to Pi for the Pi-vs-OMP delta that Wave 1 actually cares about.

6. **Advisor + Hub as a human steering model.** A second model watching turns, plus live subagent control, is implemented and documented. CRAFT on Zagens is more ambitious and more in flux.

---

## Where Zagens is better

1. **Completion is a machine property.** LHT + composable gates refuse prose-only "done" when checklists, manifests, or toolchain oracles disagree. COMPOSABLE_HARNESS's MicroStack02 note is the right failure mode: the model cleared its *own* graph at 100% with half the deliverables missing. OMP todos do not close that hole.

2. **Event-sourced turns you can replay.** Kernel V3's `kernel_events` log, `ReplayTurnMachine`, and golden fixtures are a control-loop audit story OMP does not have. Session resume from the log is specified, not hoped.

3. **Default safety posture.** on-request approvals and workspace-write sandbox, plus OS enforcement on macOS/Windows, match "local agent that runs shell" better than OMP's yolo default. Linux enforcement is still honest-about-degraded in the matrix.

4. **Long-horizon cycle/handoff.** Archiving a cycle and seeding StructuredState is a more explicit answer to million-token windows than compaction summaries. Night queue and Gate-as-Code target unattended refactors, which is a different product than a pair-programming TUI.

5. **DeepSeek V4 KV discipline.** Byte-stable tool catalogs, prefix fingerprints, reasoning_effort defaults, and a turn function literally named `handle_deepseek_turn` are the native pairing for that model family. OMP can speak DeepSeek's tool tokens; Zagens is built so the cache and the gates assume that family.

6. **Sidecar isolation of the WebView.** Desktop never holds the runtime Bearer in the frontend. That is a real architecture constraint, tested, not a README flourish.

If the question is "which OSS loop should we trust to finish a multi-hour DeepSeek refactor without believing the model's summary," Zagens is the more serious design. If the question is "which loop do we pin next to Pi and Grok Build," it is OMP.

---

## Evidence table

| Claim | Kind | Source |
| --- | --- | --- |
| No 2026 coding harness named Zazen in GitHub search | Search | `gh search repos "zazen"` 2026-08-25; discarded ESLint, Zenchain snap, ZazenCodes |
| Zagens is the Zazen candidate | Source | [didclawapp-ai/zagens README](https://github.com/didclawapp-ai/zagens/blob/a55959f77b3382e0b3709460ac97c4540fdec973/README.md) |
| Not `dsh` | Source | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness); Zagens NOTICE lineage is CodeWhale, not Cordis |
| OMP is a Pi fork | Source | OMP README; docs/porting-from-pi-mono.md; LICENSE |
| OMP loop is prompt/turn/tools | Source | packages/agent README, agent.ts, agent-loop.ts |
| Zagens Kernel V3 is event-sourced | Source | docs/tech/AGENT_KERNEL_V3.md; crates/core/.../run.rs; fixtures/harness/kernel-v3-replay |
| LHT gates shipped | Source | docs/harness/LONG_HORIZON_CODE_TASKS.md, COMPOSABLE_HARNESS.md; README v0.9.0 |
| OMP builtins list | Source | builtin-names.ts |
| Hashline format | Source | packages/hashline/README.md |
| Zagens apply_patch + fuzz | Source | crates/runtime-server/src/tools/apply_patch.rs |
| OMP approval default yolo | Source | docs/approval-mode.md |
| Zagens approval default on-request, workspace-write | Source | config.example.toml |
| Sandbox matrix | Source | docs/tech/SANDBOX_CAPABILITY_MATRIX.md |
| OMP model roles | Source | docs/models.md |
| Zagens default DeepSeek V4 Pro | Source | config.example.toml |
| OMP headless `-p` / ACP / RPC | Source | docs/cli-reference.md |
| Zagens TUI+CLI all OS, desktop Windows-only | Source | README.md |
| OMP metaharness public | Source | packages/metaharness/README.md |
| Zagens harness regression scheduled, not PR-blocking | Source | .github/workflows/harness-regression.yml |
| Zagens eval notebooks private | Source | docs/harness/README.md → `doc_Private/` |
| Office mode removed in 0.9.0 | Source | README.md "Shipped today" |
| In-tree Zagens vs CodeWhale article still claims write_office | Vendor, stale | docs/article-deepseek-agent-comparison.md |
| OMP edit-format lift 6.7%→68.3% | Vendor | OMP README "Every tool, benchmaxxed" |
| Star counts | Metadata | `gh repo view` 2026-08-25 |

---

## Unknowns

- Live binary versions on any evaluator machine. This paper froze git SHAs, not installed `omp --version` / `zagens --version` output.
- Whether Zagens Linux Landlock has shipped since the 2026-08-01 commit. README still says Linux OS sandbox is degraded unless bwrap is present.
- CRAFT production quality. Specs say evolving; craft-v2-improvements.md is still titled Draft.
- Whether OMP hashline gains survive when the *same* DeepSeek V4 slug is pinned, or only on Grok-family models the README advertises.
- Cost, latency, and token use. Not measured.
- How complete Zagens' OpenAI-compatible Grok path is in practice. Config lists compatible endpoints; no source reviewed here is a Grok-native integration test.
- Desktop Zagens macOS/Linux installer timeline. README says planned.
- Private `doc_Private/` eval numbers. Not in the public clone; cannot be cited.

---

## What a fair empirical eval still needs

Do not drop Zagens into Wave 1 Track A next to Grok Build × Pi × OMP. That would repeat the "agent zoo" error.

A defensible OMP vs Zagens cell needs:

1. **Identity freeze.** SUT name in the eval log is Zagens, SHA above or newer, filename in this repo may keep "zazen."
2. **Shared model pin.** Same DeepSeek V4 id, same `auth_class` (API key, not mixed OAuth), same `base_url`. Report as harness×DeepSeek, not harness-in-general. A second arm that pins Grok on OMP only is *not* this comparison.
3. **Shared permission class.** Either both yolo/auto or both prompt-on-exec. Record sandbox_mode. Do not compare OMP yolo to Zagens on-request and call it intelligence.
4. **Shared edit-protocol log.** Hashline vs apply_patch failures as a separate column.
5. **Headless only.** `omp -p --mode json` vs `zagens exec --json`. No desktop, no TUI operator help.
6. **Tasks that stress each bet.** One short edit-and-test. One long refactor with an operator manifest Zagens can gate and OMP must encode as instructions/todos only. Same fixture SHAs, time budget, network policy.
7. **Stop condition.** Wall clock and "gates green vs model said done." Count forced continues on the Zagens side.
8. **No ranking until the matrix is filled.** Two harnesses × one model × three tasks is the minimum publishable rectangle.

Until those exist, the only honest ranking is architectural: OMP is the better general coding CLI and the better Track A relative of Pi; Zagens is the better DeepSeek long-horizon gate-and-replay platform. Mixing those into one success% column would be a category error.

---

## Source freeze

| Tree | HEAD | Date |
| --- | --- | --- |
| [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | `969a94c1eeccb1b7528cd5621934bca1908ab622` | 2026-08-24 |
| [didclawapp-ai/zagens](https://github.com/didclawapp-ai/zagens) | `a55959f77b3382e0b3709460ac97c4540fdec973` | 2026-08-01 |
