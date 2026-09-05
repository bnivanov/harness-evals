# OMP versus Cline: a pairwise harness comparison

**Status:** source review, no scored runs  
**Date:** 2026-08-25  
**Question:** Holding a coding model as fixed as practical, how do Oh My Pi (OMP) and Cline differ as harnesses, and which differences are already visible in public GitHub trees versus which still need a controlled eval?  
**Method:** Primary evidence is the public repositories. Community tier lists and vendor ranks are not performance evidence. Roo Code and Kilo Code are out of scope. They are other papers.

**Trees read**

| Product | Repo | HEAD (this review) | License |
|---------|------|--------------------|---------|
| OMP / Oh My Pi | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | `969a94c1eeccb1b7528cd5621934bca1908ab622` (2026-08-24) | MIT |
| Cline | [cline/cline](https://github.com/cline/cline) | `491b30b806fdb8c93513f821f2b87d63a61542f5` (2026-08-25) | Apache-2.0 |

---

## 1. Identity

**OMP** is a terminal-first coding agent published as `@oh-my-pi/pi-coding-agent` with CLI `omp`. The README calls it "a coding agent with the IDE wired in" and an explicit fork of Mario Zechner's Pi (`badlogic/pi-mono`). `LICENSE` lists Mario Zechner, Can Bölük, and Stencil Labs, Inc. The README advertises 60+ providers, 31 built-in tools, 14 LSP operations, 28 DAP operations, and a Rust native core. `packages/coding-agent/package.json` maps `omp` to `src/cli.ts`. Homepage: [omp.sh](https://omp.sh).

**Cline** is a model-agnostic agent shipped as a VS Code extension (`saoudrizwan.claude-dev`), a JetBrains plugin, CLI `cline`, and `@cline/sdk`. The README leads with human-in-the-loop approval, Plan/Act, checkpoints, MCP, and a headless CLI. Publisher: Cline Bot Inc. The JetBrains client is documented as not open-sourced. Kanban (`cline/kanban`) is a sibling product, not the system under test here.

Both are hybrid on billing. OMP is BYOK-first with lab OAuth, including SuperGrok as `xai-oauth`. Cline is BYOK-first with a hosted Cline gateway, optional ClinePass, and ChatGPT-plan OAuth via `openai-codex`. Those are different auth classes. Mixing them in one harness-effect table would confound the comparison. See `landscape/agentic-tools-subscription-vs-byok.md`. Star counts are not used as quality evidence.

---

## 2. Evidence table

Claims below are *what the trees implement*, not scores.

| Axis | OMP | Cline | Primary evidence |
|------|-----|-------|------------------|
| Control loop | `agentLoop` / `runLoop` in `packages/agent/src/agent-loop.ts` | `AgentRuntime.execute`; `LocalRuntimeHost` / `SessionRuntime` | Both trees |
| Plan/Act | Write guard + `modelRoles.plan`; `--plan` | `plan`/`act`/`yolo` presets; command-guard; CLI `switch_to_act_mode`; VS Code toggle only | `presets.ts`, `command-guard-extension.ts`, `plan-mode-guard.ts` |
| Edit protocol | Hashline content-hash tags, stale-anchor reject/recover | Default `editor`; `apply_patch` off in act/plan/yolo presets | `packages/hashline/`; Cline `presets.ts` |
| Language tools | Built-in `lsp` (14) and DAP (28) | No core LSP/DAP. VS Code diagnostics. Example TS LSP plugin | OMP `lsp/types.ts`, `debug.ts`; Cline `integrations/diagnostics/` |
| Built-in tools | 29 names + 3 hidden + gated image/tts. README "31" | Nine `DefaultToolNames` plus spawn/team/MCP | `builtin-names.ts`; Cline `constants.ts` |
| Browser | Built-in `browser` and `computer` | VS Code `browser_action` (Puppeteer). CLI: `fetch_web_content` | OMP `tools/browser`; Cline `BrowserSession.ts` |
| Checkpoints | Conversation `checkpoint`/`rewind`. Git stash is an example hook | Git stash/ref workspace snapshots. SDK default off. CLI `/undo` | OMP `tools/checkpoint.ts`; Cline `checkpoint-hooks.ts` |
| Approvals | Default `"yolo"`; also `always-ask` / `write` | HITL default. VS Code `autoApprove: false`. CLI `--yolo` | OMP `settings-schema.ts`; Cline `sdk-tool-policies.ts` |
| Auth / Grok | `xai` key vs `xai-oauth` SuperGrok, default `grok-4.6`. Ten roles | `xai` + `XAI_API_KEY`. Also `cline`, `cline-pass`, `openai-codex`. No SuperGrok OAuth module | OMP `descriptors.ts`, `xai-oauth.ts`; Cline `builtins.ts` |
| Surfaces | TUI, `--print`, json/rpc/acp, SDK. No VS Code extension | VS Code, JetBrains (closed), CLI, SDK, Hub | Both READMEs |
| Multi-agent | `task`, worktrees, Agent Hub, advisor | `spawn_agent`, teams, `--team-name`, cron, messaging | OMP `task/`; Cline `extensions/tools/team/` |
| OSS | MIT monorepo. Opt-in OTEL | Apache-2.0 core. JetBrains not OSS. Hosted ClinePass | Both `LICENSE` |
| Headless / eval | `omp --print`, `--smoke-test`, metaharness | `cline --json`, `--yolo`, pipe. `evals/` smoke tests partially disabled | OMP `cli/flag-tables.ts`; Cline `evals/README.md` |

---

## 3. Architecture and control loop

Both products are classic tool-calling agents. The interesting difference is where the loop lives and what it is allowed to do between model turns.

OMP's loop is `packages/agent/src/agent-loop.ts`. `agentLoop` emits `agent_start`, then `runLoop` runs an inner cycle of stream-assistant, execute tools, repeat, plus an outer cycle that continues when steering arrives after the agent would otherwise stop. Caps include `MAX_PAUSED_TURN_CONTINUATIONS = 8`. There is no ProtoBus. The coding-agent package wraps that loop with tools, sessions, and a TUI.

Cline detaches the same kind of loop from the VS Code host. `AgentRuntime.execute` is the iteration engine. `SessionRuntime` instantiates a fresh `AgentRuntime` per run. `LocalRuntimeHost` owns turns, persistence, and checkpoints. The VS Code extension still talks to that core over ProtoBus / HostBridge. The CLI and SDK can run the core without ProtoBus. That is why Cline can claim one engine across IDE and terminal while still having IDE-only tools such as `browser_action`.

**Plan/Act.** Cline's Plan/Act is a product invariant. `ToolPresets.plan` sets `enableEditor: false` and keeps bash on for read-only investigation. `createPlanModeCommandGuardExtension` is a `beforeTool` hook that rejects file-editing `run_commands` before approval UI. System prompt contracts in `sdk/packages/shared/src/prompt/cline.ts` distinguish plan from act, and user messages are wrapped in `<user_input mode="...">` so a mid-session switch is visible to the model. On the CLI, `switch_to_act_mode` can complete the run and auto-continue. In VS Code, `planModeSwitchTool` is false. The user toggles Plan/Act in the UI. That is a deliberate host difference inside one product.

OMP also has plan mode. `PlanModeState` tracks an enabled flag and a plan file. Entering plan can swap the model to `modelRoles.plan`. `tools/plan-mode-guard.ts` keeps the working tree read-only and allows writes under `local://` so the plan artifact can still be edited. That is a write fence plus a role swap, not Cline's full tool-preset plus command-guard plus mode-tag machinery. Calling both "Plan/Act" without that distinction would overstate the similarity.

---

## 4. Tools, edits, and language services

OMP's advertised bet is that agents fail on mechanics: stale line numbers, whitespace, missing types, no debugger. The tree matches that pitch.

Hashline is a separate package with a grammar (`packages/hashline/src/grammar.lark`) and a model-facing spec (`src/prompt.md`). Each section is `[PATH#TAG]` where TAG is a 4-hex content hash from the last `read`. Ops include ranged `PUT`, block `PUT`, inserts, `CUT`, `REM`, `MV`. Stale tags are rejected or recovered against a `SnapshotStore`. This project's Wave 1 review already flagged hashline as an independent variable. If OMP wins an edit-heavy task against Cline, the first alternative explanation is the patch language.

Cline's default write path is the `editor` tool. `apply_patch` is in `DefaultToolNames`, but every preset this review inspected sets `enableApplyPatch: false`. Treat Cline as an editor-tool culture unless a session turns patch on.

On language services the gap is structural. OMP's `lsp` and `debug` tools expose rename, hover, diagnostics, and a DAP session. Cline's IDE host reads VS Code diagnostics after edits. That is a feedback channel, not a tool the model can call for rename. The TypeScript LSP plugin under `sdk/examples/plugins/` is an example, not a default.

OMP's builtin set is large. Cline's core catalog is small and MCP/plugins are the expansion path. Cardinality is not a score. A larger schema can help or can waste context.

Browser is not the same feature. OMP ships `browser` and `computer` for TUI/CLI. Cline's interactive Puppeteer session is VS Code-hosted. A headless `cline` eval that never opens VS Code is not testing `browser_action`.

---

## 5. Context, memory, and checkpoints

OMP sessions are JSONL trees under `~/.omp/agent/sessions/` with a mutable leaf pointer (`session/session-manager.ts`). Compaction lives in `packages/agent/src/compaction/` including a streaming v2 path and optional OpenAI remote compact. Memory backends are settings-gated: `off` by default, then `local` / `hindsight` / `mnemopi`, with tools `retain`, `recall`, `reflect`, `learn`. Skills load from `.omp/skills/` and user dirs. Rule discovery is unusually promiscuous. `discovery/cline.ts` imports `.clinerules`. Other loaders cover AGENTS.md, Cursor, Claude, Codex, Gemini, Copilot. OMP will obey a Cline project's rules file if you point it at that repo. The reverse is not true as a first-class importer in the Cline tree.

Cline's instruction loader (`user-instruction-config-loader.ts`) reads `.clinerules`, `.cline/{skills,rules,workflows,hooks}`, `AGENTS.md`, and `.agents/skills`. Compaction has `auto` / `manual` / `overflow_recovery` modes and basic versus agentic strategies. Session data goes through SQLite stores under `resolveClineDataDir()`.

**Checkpoints are the easy false friend.** Cline's checkpoint hooks write git stash/ref snapshots (`CHECKPOINT_STASH_MESSAGE_PREFIX = "cline checkpoint session="`) and expose compare/restore on `ClineCore`. That is workspace undo. SDK default is opt-in (`enabled` defaults to false in `CoreCheckpointConfig`). How often the VS Code UI turns this on for end users is not fully pinned from the SDK default alone. OMP's `checkpoint` / `rewind` tools, per `prompts/tools/checkpoint.md`, exist to dump exploratory tool noise from the *conversation* and keep a short report. Git stash checkpoints in OMP are `examples/hooks/git-checkpoint.ts`. Default OMP does not give you Cline-style working-tree restore. Default Cline SDK does not give you OMP-style conversation rewind. Name the mechanism in any eval log.

---

## 6. Auth, model pinning, BYOK, and subscription

OMP's catalog splits paid xAI API (`xai`, `XAI_API_KEY`, default `grok-4.6`) from SuperGrok OAuth (`xai-oauth`, `XAI_OAUTH_TOKEN` or `/login`, default `grok-4.6`). The OAuth client in `packages/ai/src/registry/oauth/xai-oauth.ts` is RFC 8628 device flow against `https://auth.x.ai`, scope including `grok-cli:access`, billing proxy `https://cli-chat-proxy.grok.com/v1/billing`. Those two paths are different products with the same model name. OMP also defines ten roles in `config/model-roles.ts`: default, smol, slow, vision, plan, designer, commit, tiny, task, advisor. Plan mode can retarget the model. Fallback chains are a config concern (`retry.fallbackChains` in settings). For this project's Track A, OMP is the SuperGrok-native Pi fork. Cline is not.

Cline's `BUILT_IN_PROVIDER` list includes `cline`, `cline-pass`, `anthropic`, `openai-codex`, `openrouter`, `bedrock`, `vertex`, `gemini`, `ollama`, `lmstudio`, `xai`, and more. The `xai` builtin uses `XAI_API_KEY` and `https://api.x.ai/v1`. No `xai-oauth` module showed up in this clone. Grok on Cline is BYOK API or whatever the Cline/OpenRouter catalogs expose, not SuperGrok device login. ClinePass is subscription-gated (`"no access to clinepass subscription models yet"` in `sdk/packages/llms/src/providers/errors.ts`) and feature-flagged. `cline auth` offers Cline OAuth, ChatGPT subscription, OCA, or a raw API key. That is a real hybrid, and it is *Cline's* hybrid, not xAI's.

Pinning: OMP can pin a provider/model on the CLI and also pin *roles*. Cline pins `providerId` + `modelId` per session. Neither tree implements a scientific "hold Grok 4.6 on SuperGrok OAuth" switch that the other product understands. A fair pairwise run must declare `auth_class` and `model_id` in the eval log. OMP SuperGrok OAuth versus Cline `XAI_API_KEY` is not a harness comparison.

---

## 7. Surfaces and extensibility

OMP is a TUI with IDE-class tools inside the terminal: LSP, DAP, hashline, in-process grep/bash. Editor attachment is ACP (`omp acp`), documented as something Zed spawns, not a command humans run by hand. Headless is `omp --print` / `-p` and JSON/RPC modes. There is no first-party VS Code or JetBrains product in the oh-my-pi tree.

Cline still treats the VS Code extension as the primary surface. JetBrains is a closed client on the shared core. The CLI is a first-class second surface with `--json`, piping, `--yolo`, and `--zen` for a hub daemon. `@cline/sdk` embeds the loop. Cline Hub is in-repo. Kanban is adjacent, not the system under test.

Both speak MCP. OMP names tools `mcp__<server>_<tool>`. Cline names them `serverName__toolName`. OMP also has extensions, plugins, hooks, slash commands, and an `xd://` device protocol. Cline's SDK `registerTool` path includes a subprocess sandbox. Neither MCP story was executed here. Cline's extra surfaces (cron, Slack/Telegram/Discord, persisted teams) matter for an operator product. They are mostly orthogonal to a single-repo coding-task eval unless the task is multi-agent by design.

---

## 8. Safety, multi-agent, and licensing

Default permission posture is inverted.

OMP's settings schema defaults `tools.approvalMode` to `"yolo"`. `always-ask` and `write` exist. Per-tool `allow|deny|prompt` overrides exist. ACP still routes destructive ops through `session/request_permission`. Subagents can isolate into worktrees (`task/worktree.ts`, `crates/pi-iso`). Plan mode is a write fence. The default interactive binary will execute unless you tighten it.

Cline's README default is approval on every edit and command, with auto-approve as an opt-in. VS Code forces governed tools to `autoApprove: false` so the AutoApproveBar decides. CLI `--yolo` and the `yolo` preset flip that for CI. Plan mode is a second safety layer. Loop-detection and mistake-tracker modules exist under `sdk/packages/core/src/runtime/safety/`. This review did not find an OS-level sandbox around `run_commands` in the SDK core. Commands run on the host. Same class of risk as OMP bash, with more UI friction in the IDE default.

Multi-agent: OMP's `task` tool plus worktrees plus Agent Hub is a fan-out design inside one TUI. Cline's `spawn_agent` and `AgentTeamsRuntime` plus `--team-name` is a coordinator/specialist design with SQLite-backed child sessions. YOLO preset in Cline *disables* spawn/teams. Autonomous Cline is a smaller toolset. OMP yolo is the opposite, still holding the full tool list unless you deny tools.

Licensing: OMP is MIT and the client you run is in the repo, including ACP. Cline is Apache-2.0 for the published core, CLI, VS Code extension, SDK, and Hub. The JetBrains plugin is explicitly not open-sourced. Hosted Cline/ClinePass inference is proprietary. Telemetry in both is OTEL-shaped and off unless configured. Cline also talks to `https://data.cline.bot` for PostHog feature flags. "Fully open" is true of OMP's agent binary in a way it is not true of Cline-on-JetBrains.

---

## 9. Where OMP is better

These are design advantages visible in source, not measured win rates.

**Edit reliability protocol.** Hashline is a specified, tested patch language with content-hash anchors. Cline's default editor path has no equivalent in-tree spec of that form. For a harness eval that counts failed apply-then-retry loops, OMP gives you a mechanism you can name.

**Language-aware tools without an IDE host.** LSP and DAP are built-in. Cline gets diagnostics for free in VS Code and almost nothing of that shape in CLI-only runs. If the research question is terminal-native harness quality, OMP is the one that still has rename, hover, and a real debugger.

**Grok subscription pinning.** SuperGrok OAuth is a first-class provider with its own id, default `grok-4.6`, device-code client, and billing proxy. Cline's xAI path in this tree is an API key. For this project's Track A, OMP can sit next to Pi and Grok Build on the same auth class. Cline cannot without a BYOK key, which is a different meter.

**Role routing.** Ten model roles plus plan-entry model swap is a harness feature Cline does not copy. Cost and latency experiments that route `smol` versus `default` are OMP-native.

**Headless default.** `omp --print` plus default yolo matches a scripted coding eval. Cline can do the same with `--yolo`, leaving the IDE approval culture. Convenient, and a safety debit listed under Cline.

**Rule import.** OMP will load `.clinerules`. Cline does not ship an OMP `.omp/rules` importer of the same explicitness.

**OSS completeness of the agent you actually run.** MIT, no closed JetBrains client in the critical path, ACP instead of a proprietary IDE plugin. Reproducers can clone and run.

---

## 10. Where Cline is better

**The IDE is the product.** VS Code diffs, approval UI, diagnostics after writes, and a JetBrains plugin are not features OMP approximates with a TUI. If the unit of analysis is "developer stays in the editor," Cline is the harness. OMP's ACP path to Zed is real and thin by comparison. It was not exercised here.

**Plan/Act as a control system.** Cline encodes plan as tool presets, a command-guard hook, prompt contracts, and mode-tagged user messages. OMP's plan mode is a write guard and optional model role. For tasks where premature edits are the failure mode, Cline's structure is the stricter independent variable.

**Workspace undo.** Git stash/ref checkpoints restore files. OMP's default checkpoint restores *context*, not the tree. The example git-checkpoint hook is not the same as Cline's `/undo` story. Operators who fear agent damage will prefer Cline's checkpoint design, especially in the IDE.

**Human-in-the-loop by default.** VS Code forces approval callbacks on edits, shell, and MCP. OMP defaults to yolo. That is a product philosophy gap. It will also confound "did the agent finish" if one system pauses for clicks and the other does not.

**Shared core across many surfaces.** One SDK loop in CLI, VS Code, Hub, and embedders, with a documented plugin API and subprocess sandbox. OMP's SDK exists, but Cline's surface matrix is wider: messaging, cron, teams, Kanban as a sibling. For an org that wants one agent in Slack and in VS Code, Cline is the closer fit.

**Eval and CI packaging.** `cline --json`, stdin piping, `--yolo`, and an `evals/` tree with pass@k analysis exist even while smoke tests are partially disabled during the SDK CLI migration. OMP has `--print` and a metaharness. Cline's CLI README is the clearer CI contract.

**Hosted subscription if you want one.** ClinePass and `cline auth` are a vendor ledger. Worse for a Grok-fixed science table. Better if the question is whether a team can buy a plan and not manage keys.

**Lineage without treating forks as the parent.** Cline is the parent of Roo/Kilo. This paper does not score the forks. The parent still has the Plan/Act and approval DNA they copied, which matters when choosing a VS Code baseline for later waves.

---

## 11. Unknowns

- JetBrains plugin behavior, approvals, and checkpoint UX. Source is not in `cline/cline`.
- Whether the VS Code UI enables checkpoints even though SDK `CoreCheckpointConfig.enabled` defaults to false. README implies yes. The SDK default says opt-in. Surface-specific.
- SuperGrok entitlement inside Cline's hosted `cline` / OpenRouter catalogs. Not verified by running auth. The `xai` builtin is API-key.
- Hashline apply-success versus Cline `editor` on the same model. Specified, not measured.
- Whether OMP's default yolo plus 31 tools over-spends context relative to Cline's small core catalog.
- ACP-in-Zed quality versus Cline-in-VS Code.
- Cline eval smoke-test health after the SDK CLI migration (`evals/README.md`: Layer 2 partially disabled).
- Runtime cost, latency, and token use. No runs.
- Plugin/MCP ecosystems in practice. Both trees support MCP. Neither was driven against the same server.
- Roo/Kilo divergence. Explicitly not researched.

---

## 12. Fair empirical evaluation still needed

This document is a mechanism map. It does not contain a winner.

A defensible pairwise eval would freeze:

1. **Surface.** Either both headless CLI (`omp --print` vs `cline --yolo --json`) or admit IDE-vs-TUI as the factor and stop calling it a pure harness effect.
2. **Model identity.** Same slug, for example `grok-4.6`, not "whatever the picker opened."
3. **Auth class.** SuperGrok OAuth versus `XAI_API_KEY` versus Cline gateway versus OpenRouter are four systems. Pick one both can actually use. Today that common class is likely `XAI_API_KEY` or OpenRouter, which *drops* OMP's SuperGrok advantage on purpose.
4. **Approvals.** Set OMP to `always-ask` or Cline to `--yolo`. Do not compare default OMP yolo to default VS Code HITL and call the faster one smarter.
5. **Plan mode.** Either both in act, or both start in plan with a documented switch rule. Cline CLI can self-switch. Cline VS Code cannot.
6. **Edit protocol logging.** Record hashline reject/recover versus Cline editor failures as a separate column.
7. **Checkpoints.** Off, or on with a note that OMP conversation rewind ≠ Cline git restore.
8. **Browser.** Disable VS Code-only `browser_action` unless the task needs it and OMP `browser` is also in play.
9. **Tasks.** Pre-declare three tasks. Include at least one refactor that would use LSP if present, and one apply-heavy multi-file edit. No ranking until the matrix is filled.
10. **No Roo, no Kilo, no community tiers.**

Until that protocol exists, the honest summary is architectural. OMP is the Pi fork with hashline, LSP/DAP, and SuperGrok OAuth, terminal-first, yolo-default. Cline is the Plan/Act IDE agent with a shared SDK core, HITL defaults, workspace checkpoints, and a hybrid ClinePass/BYOK ledger. They overlap as model-agnostic coding agents with MCP and a CLI. They do not overlap as experimental units unless you pin the confounds above.

---

## Sources

**OMP.** [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) @ `969a94c`. Paths cited inline and in the evidence table, including `packages/agent/src/agent-loop.ts`, `packages/hashline/`, `packages/coding-agent/src/tools/builtin-names.ts`, `lsp/types.ts`, `tools/debug.ts`, `tools/plan-mode-guard.ts`, `tools/checkpoint.ts`, `config/model-roles.ts`, `config/settings-schema.ts`, `packages/ai/src/registry/oauth/xai-oauth.ts`, `modes/acp/acp-mode.ts`, `discovery/cline.ts`.

**Cline.** [cline/cline](https://github.com/cline/cline) @ `491b30b`. Paths cited inline and in the evidence table, including `sdk/packages/agents/src/agent-runtime.ts`, `extensions/tools/presets.ts`, `command-guard-extension.ts`, `hooks/checkpoint-hooks.ts`, `sdk/packages/shared/src/prompt/cline.ts`, `sdk/packages/llms/src/providers/builtins.ts`, `apps/vscode/src/sdk/sdk-tool-policies.ts`, `apps/vscode/src/services/browser/BrowserSession.ts`, `apps/cli/src/runtime/interactive/mode.ts`, `evals/README.md`.

**This project, method only.** `BRIEF.md`, `DECISIONS.md`, `landscape/agentic-tools-subscription-vs-byok.md`, `waves/wave-1-adversarial-review.md`.
