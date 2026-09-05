# OMP vs Hermes Agent: a pairwise harness comparison

**Status:** source review. No scores, no task runs, no ranking.  
**Date:** 2026-08-25  
**Question:** Holding models aside, how do the Oh My Pi coding harness and the Nous Research Hermes Agent harness differ as software that wraps an LLM?

This note compares **harnesses**. It does not compare the Nous Hermes *model* family (`hermes-3-*`, `hermes-4-*`, and related checkpoints). Hermes Agent is a Python runtime that will drive whatever provider you pin. The bundled skill `website/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent.md` states that distinction explicitly.

---

## Identity

| | OMP (Oh My Pi) | Hermes Agent |
|---|---|---|
| Product | Coding agent with the IDE wired in | Self-improving personal agent that also codes |
| Repo | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| HEAD reviewed | `969a94c1eeccb1b7528cd5621934bca1908ab622` (2026-08-24) | `0268c0b8c0e75d1fcbce37f39b14e63b8871a2a2` (2026-08-25) |
| Version | `@oh-my-pi/pi-coding-agent` **18.0.4** | `hermes-agent` **0.20.5** (`pyproject.toml`) |
| Binary | `omp` | `hermes` (`hermes-agent`, `hermes-acp` also registered) |
| License | MIT (Mario Zechner, Can Bölük, Stencil Labs, Inc.) | MIT (Nous Research, 2025) |
| Language | TypeScript + Rust natives | Python 3.11 to 3.13 |
| Docs | [omp.sh](https://omp.sh), in-tree `docs/` | [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com) |
| Stars at review | 27,302 | 236,122 |

Star counts are GitHub API snapshots from 2026-08-25. They measure attention, not coding-loop quality.

OMP is a fork of Mario Zechner's Pi (`pi-mono`). The coding-agent `package.json` still lists Zechner as a contributor. Hermes is a Nous Research product whose README leads with a learning loop, a messaging gateway, and a VPS/cloud story, not with an editor.

This project's taxonomy already split them. `research/llm-coding-harness-landscape-2026-08.md` filed Hermes under *Personal / always-on + coding-capable*. `landscape/agentic-tools-subscription-vs-byok.md` tags OMP as a CLI coding harness and Hermes as a CLI personal runtime. `possible-harnesses.md` called Hermes "learning / memory-oriented." Those labels match the source.

---

## Method

GitHub-first. Claims below cite files, commits, or first-party docs in the two checkouts. Evaluator notes (Hermes ~v0.20.x, binary `hermes`, portal/OAuth, OMP hashline/LSP/DAP/SuperGrok) were treated as hints and checked in source. They held.

No invented scores. README tables that report pass-rate lifts or token cuts are **vendor-reported**. They are cited as claims, not as results of this project.

Axes: architecture, tools, context/memory/learning, auth and model-pinning, surfaces, extensibility, safety, multi-agent, OSS, eval/reproducibility, coding specialization vs general agent.

---

## Methodological note: Grok-native track membership

`waves/wave-1-adversarial-review.md` argued that Hermes may not belong on a Grok-native science track. That is a **design claim about the experiment**, not a quality ranking of Hermes.

The original Wave 1 thesis is: hold a Grok family roughly fixed, vary the coding loop, measure harness effect (`BRIEF.md` RQ1; `DECISIONS.md`). Three facts in Hermes source make that cell expensive to defend.

1. **Job mismatch.** Hermes is a personal runtime. Default toolsets in `toolsets.py` share `_HERMES_CORE_TOOLS` across CLI *and* Telegram/Discord/Slack. Cron, TTS, home-assistant, and computer-use sit in the same product as `patch`. OMP's `package.json` description is "Coding agent CLI with read, bash, edit, write tools and session management." Different independent variables.

2. **Nested SUT.** The optional skill `optional-skills/autonomous-ai-agents/grok/SKILL.md` tells the agent to run `grok --no-auto-update -p '...'` through Hermes `terminal()`. That is Grok Build's coding loop inside Hermes. If that skill is on, a "Hermes" row can be Grok Build scored twice. Sibling skills do the same for Codex and Claude Code.

3. **Auth is not inclusion.** Hermes documents SuperGrok OAuth (`website/docs/guides/xai-grok-oauth.md`, provider `xai-oauth`, default chat model `grok-4.6`). OMP documents the same class of login (`packages/ai/src/registry/xai-oauth.ts`). OAuth availability does not make Hermes a coding-harness control. Grok Build CLI auth lives in `~/.grok/auth.json`. Hermes stores its own token in `~/.hermes/auth.json`. The grok skill's pitfalls section says a working Hermes `x_search` does **not** mean `grok` is logged in.

A defensible Hermes coding cell is still possible. Pin the same Grok slug and auth class as Track A, disable the `grok` / `codex` / `claude-code` delegation skills, use `hermes -z` or `hermes chat -q` with an explicit `--toolsets` that looks like a coding loop, and label the row "personal-runtime coding loop." That is Track C, or a constrained Track A footnote. It is not the same experiment as Grok Build × Pi × OMP.

The rest of this note compares the two products as they ship. Track membership is a later protocol choice.

---

## Architecture and control loop

Both are classic tool-calling loops. User text in, provider call, tool results appended, repeat until the model stops calling tools.

OMP splits the loop from the product. `@oh-my-pi/pi-agent-core` owns `agentLoop` / `runLoop` in `packages/agent/src/agent-loop.ts`. `AgentSession` in `packages/coding-agent/src/session/agent-session.ts` is shared across interactive, print, and RPC modes. I/O is a layer on top of that session, not a fork of the loop. Streaming, abort, steering during interruptible tools, and a documented non-compaction retry policy (`docs/non-compaction-retry-policy.md`) live in that stack.

Hermes concentrates the product in two large Python modules. `run_agent.py` defines `AIAgent` (about 9,200 lines). `agent/conversation_loop.py` runs the `while` loop against `max_iterations` and an iteration budget, then `_execute_tool_calls`. Dispatch goes through `model_tools.handle_function_call` into `tools/registry.py`. Architecture docs at `website/docs/developer-guide/architecture.md` draw one `AIAgent` serving CLI, gateway, ACP, batch, and API server.

API shape differs. OMP talks to a catalog of providers through `@oh-my-pi/pi-ai`. Hermes documents three primary API modes (`chat_completions`, `codex_responses`, `anthropic_messages`) and implements extras (`bedrock_converse`, `codex_app_server`). Providers `xai` and `xai-oauth` are wired to `codex_responses` in `agent/agent_init.py` because xAI exposes a Responses-style endpoint. `codex_app_server` can hand the turn to a Codex subprocess and leave the Hermes loop.

Headless paths exist on both sides, which matters for a later eval. OMP: `omp -p` / `--print`, optional `--mode json` or `--mode rpc`, `--max-time`, `--smoke-test`. Hermes: `hermes -z` / `--oneshot` (bypasses `cli.py`, stdout is the final text block) and `hermes chat -q`. `hermes_cli/oneshot.py` sets `HERMES_YOLO_MODE=1` for the call. Approvals are auto-bypassed in oneshot. That is convenient for CI and a confound if the scored protocol wanted a permission gate.

---

## Tools

OMP ships a small, coding-shaped tool list. `BUILTIN_TOOL_NAMES` in `packages/coding-agent/src/tools/builtin-names.ts` has 30 names: `read`, `bash`, `edit`, `write`, `grep`, `glob`, `lsp`, `debug`, `ast_grep`, `ast_edit`, `eval`, `task`, `web_search`, memory tools, `security_scan`, and others. README's "31 built-in tools" is 30 plus optional `generate_image`. The `edit` tool drives `@oh-my-pi/hashline`: content-hash anchors, stale-anchor rejection, preflight of multi-section patches so a partial batch does not land (`packages/coding-agent/src/edit/hashline/execute.ts`). `lsp` exposes 14 actions including rename and `rename_file` through `workspace/willRenameFiles`. `debug` exposes 28 DAP actions. Persistent kernels (`eval`) can call back into agent tools.

Hermes ships a large, personal-agent tool list. `toolsets.py` maps on the order of 90 tools into dozens of toolsets. File work is `read_file` / `write_file` / `patch` / `search_files`. Terminal execution has seven backends: local, Docker, SSH, Singularity, Modal, Daytona, Vercel Sandbox. Browser, MCP, cron, messaging, vision, and `delegate_task` sit beside those. There is a `"coding"` posture that keeps files, terminal, patch, delegate, and browser and drops messaging, TTS, image gen, Spotify, home-assistant, cron, and computer-use (`toolsets.py` comments at the coding toolset). LSP in Hermes is **post-write diagnostics**, not a first-class rename/navigation tool. `website/docs/user-guide/features/lsp.md` describes pyright/gopls/rust-analyzer/etc. feeding `lsp_diagnostics` on `write_file`/`patch`, gated on git-workspace detection, silent fallback if the server is missing.

The edit-protocol difference is load-bearing for any later coding eval. OMP's bet is hashline plus LSP writethrough. Hermes's bet is `patch` plus lint/LSP diagnostics after the write. Those are different failure modes. A single pass/fail column would mix them.

---

## Context, memory, and learning

OMP memory is **off by default**. `docs/memory.md` lists backends `off`, `local` (project-scoped summaries and lessons), `hindsight`, and `mnemopi`. Tools `retain` / `recall` / `reflect` / `learn` appear when a backend or autolearn is on. Compaction rewrites old history on the current branch (`docs/compaction.md`). Context files (`AGENTS.md`, `CLAUDE.md`, and kin) are discovered before the session starts (`docs/context-files.md`). Time-traveling stream rules abort a stream mid-token on a regex, inject a reminder, and retry (`docs/ttsr-injection-lifecycle.md`). Memory is project-scoped by default.

Hermes memory is **on by default** and is the product's identity. `MEMORY.md` (2,200 chars) and `USER.md` (1,375 chars) live under `~/.hermes/memories/` and are injected as a frozen system-prompt block (`website/docs/user-guide/features/memory.md`). `SOUL.md` is instance personality. The agent writes memory through a `memory` tool. Overflow errors rather than silent drop. Optional external providers (Honcho and others) attach one-at-a-time via `plugins/memory/`. Skills are procedural memory: `skill_manage`, autonomous skill creation after complex tasks, Skills Hub, agentskills.io. Session search uses SQLite FTS5. The conversation loop increments `_iters_since_skill` and nudges `skill_manage`. Profiles isolate `HERMES_HOME` so two agents do not share one memory file.

OMP learns about a *repo*. Hermes learns about a *person* and a long-lived home directory, then also reads project `HERMES.md` / `.hermes.md`. For a SWE-bench-style fixture that should not leak user biography across tasks, OMP's default-off memory is easier to freeze. Hermes needs an explicit profile, memory off, and skill-write policy per run.

---

## Auth and model pinning

Both are hybrid: BYOK keys and lab OAuth.

OMP provider id `xai-oauth` is labeled "xAI Grok OAuth (SuperGrok or X Premium+)" in `packages/ai/src/registry/xai-oauth.ts`. Catalog tests pin the SuperGrok default to `grok-4.6` (`packages/catalog/test/xai-oauth-bundle.test.ts`). Paid xAI API is a separate `xai` provider. Other OAuth paths include Anthropic, OpenAI Codex, GitHub Copilot, Google Antigravity / Gemini CLI, and Cursor. CLI pinning is `--model <id-or-role>` with roles such as `smol`, `slow`, `plan`, `task`, `advisor` (`docs/cli-reference.md`, `docs/models.md`). Fuzzy match accepts `xai-oauth/grok-4.6`.

Hermes stores OAuth in `~/.hermes/auth.json` (`hermes_cli/auth.py`). `PROVIDER_REGISTRY` starts with Nous Portal, OpenAI Codex, OpenAI API, `xai-oauth`, and continues through a long list of OAuth and API-key providers. Nous Portal is the first-party convenience path: `hermes setup --portal` logs in once for models plus Tool Gateway (search, image, TTS, cloud browser). xAI OAuth docs say default chat model `grok-4.6`, list `grok-build-0.1` as a coding-oriented SKU, and warn that some SuperGrok tiers return HTTP 403 on the OAuth inference surface (issue #26847), in which case the operator should switch to `XAI_API_KEY` / provider `xai`. Pinning is `hermes config set model.default grok-4.6` plus `model.provider xai-oauth`, or `hermes model`, or `--model` / `--provider` on oneshot.

Pinning is possible on both. Mixing SuperGrok OAuth with `XAI_API_KEY` inside one table is still a different ledger (`landscape/agentic-tools-subscription-vs-byok.md`). Hermes's extra trap is the second token at `~/.grok/auth.json` if the grok skill fires.

---

## Surfaces

OMP is a terminal coding product that can be driven from an editor. Default is TUI. Headless print, JSON, JSON-RPC, and ACP (`--mode acp` / `omp acp`) exist. `/collab` puts a live session on `my.omp.sh` with client-side sealed frames. `python/robomp` is a GitHub triage bot that drives `omp --mode rpc` on per-issue worktrees. Windows is a first-class native binary story, not a WSL shim.

Hermes is a personal agent with many doors into one `AIAgent`. CLI/TUI, Electron desktop (`apps/desktop/`), web dashboard, ACP (`hermes-acp`) for VS Code / Zed / JetBrains, cron with delivery to any platform, and a gateway with 20+ messaging adapters (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, email, Teams, and more). README's pitch is "talk to it from Telegram while it works on a cloud VM."

ACP on both sides means an IDE can host either loop. Hermes ACP is still an adapter over the personal agent. OMP ACP is the coding session in the editor's buffer.

---

## Extensibility

OMP: extensions, hooks, MCP (`mcp__<server>_<tool>`), slash commands, a plugin marketplace, skills, custom tools under `.omp/tools/`. CLI flags `--extension`, `--hook`, `--plugin-dir`, `--skills`.

Hermes: plugins (`~/.hermes/plugins/`, project `.hermes/plugins/`, pip entry points), MCP, Skills Hub, gateway/plugin/shell/webhook hooks, 100+ optional skills in the checkout, profile distributions. CONTRIBUTING.md says new *tools* are rarely needed and most capabilities should be skills.

Hermes's skill layer is thicker. OMP's extension surface is closer to a coding-agent plugin model. An eval must freeze skills and plugins the way it freezes the model.

---

## Safety

Neither project pretends in-process filters are a sandbox.

OMP tools declare `read` / `write` / `exec` tiers (`docs/approval-mode.md`). Modes: `always-ask`, `write`, and **`yolo` as default** (auto-approves read, write, and exec). `--approval-mode` and `--yolo` override. Bash has critical-pattern overrides. `security_scan` can run native reviews and Codex Security cloud scans. Subagents run in copy-on-write worktrees. Provider "sandbox" settings in the schema are transport tiers, not OS isolation.

Hermes `SECURITY.md` is unusually plain: "The only security boundary against an adversarial LLM is the operating system." Approval gates, redaction, scanners, and allowlists are heuristics. Isolation that counts is a non-default terminal backend (Docker, SSH, cloud sandbox) or wrapping the whole process. Approvals: `smart` / `manual` / `off`. DM pairing for gateway. `skills.write_approval` stages skill writes. Subagent auto-approve defaults to deny (`tools/delegate_tool.py`). Oneshot still forces YOLO.

For a coding eval, OMP's default yolo and Hermes oneshot's forced yolo both mean "headless success" will include destructive exec unless the protocol sets a stricter mode and logs it.

---

## Multi-agent

OMP: `task` fans out into isolated worktrees with schema-validated yields; Agent Hub steers workers; an `advisor` role runs a second model; `/collab` is multi-user on one session. Catalog entries such as `grok-4.20-multi-agent-*` are xAI-side models, not OMP's `task` tool.

Hermes: `delegate_task` with parallel workers and their own terminals; parallel tool-call segmentation in `_execute_tool_calls`. Plus the optional nested-harness pattern: shell out to `grok`, `codex`, or `claude`.

Count one system per scored run, or say so in the log.

---

## OSS

Both MIT, public GitHub, active `main`.

OMP: TypeScript monorepo, Bun, Rust natives, heavy in-tree tests (`packages/coding-agent` has well over a thousand `*.test.ts` files), `ci:test:smoke`. CONTRIBUTING is in an open-PR trial after a vouch requirement.

Hermes: Python, `uv.lock`, exact `==X.Y.Z` pins on core deps after the Mini Shai-Hulud `mistralai` incident (`pyproject.toml`, 2026-05-12). Architecture docs still say "~25,000 tests across ~1,250 files"; `tests/` at HEAD is larger than that claim. Issue volume is much higher than OMP's. That is a maintenance fact, not a quality score.

---

## Eval and reproducibility

OMP in-tree: `packages/typescript-edit-benchmark`, `packages/metaharness`, `scripts/edit-benchmark.py` with `PI_EDIT_VARIANT=hashline`, `omp if-bench`, session-stats. README cites [blog.can.ac/2026/02/12/the-harness-problem](https://blog.can.ac/2026/02/12/the-harness-problem/) for hashline vs str_replace lifts. Those numbers were not reproduced here.

Hermes in-tree: `evals/compaction/` (recall vs tokens), browser and read-tool evals, `batch_runner.py`, `mini_swe_runner.py` (custom SWE-style runner, Hermes trajectory format). No first-class Terminal-Bench or SWE-bench adapter found in `evals/`. Trajectory generation is aimed at training data, which is a different goal than fixture tests going green.

Both have headless entry points. Neither gives this project a filled `evaluation-log.md` row.

---

## Coding specialization vs general agent

OMP is a coding harness that grew IDE machinery: hashline, LSP as a tool, DAP, AST edits, git/PR URL schemes (`pr://`, `conflict://`), commit splitting, plan/review subagents. The README title line is the taxonomy.

Hermes is a general personal agent that grew coding affordances: patch, post-write LSP diagnostics, a coding toolset posture, ACP, and skills that *delegate* coding to lab CLIs. The README title line is the taxonomy.

That is the whole comparison, at the product level. Everything else is mechanism.

---

## Where OMP is better

**As a coding SUT.** The loop, tools, and docs are built to edit a repository. Hashline plus LSP rename/writethrough plus DAP is a coding-specific stack Hermes does not match. Hermes LSP is a diagnostic sidecar on writes. OMP LSP is how the agent is told to rename.

**Cleaner Track A pairing with Pi.** OMP is an explicit Pi fork. The informative experiment is four-tool Pi vs batteries OMP under one Grok pin (`waves/wave-1-adversarial-review.md`). Hermes is a different skeleton.

**Headless coding flags that look like other CLIs.** `omp -p` with `--mode json` and `--max-time` is the same shape as `grok -p` / `claude -p`. Hermes `-z` works, but default oneshot YOLO and the full personal toolset are extra protocol text.

**Edit-format research already in-tree.** Metaharness and the hashline grammar (`packages/hashline`) exist to measure the thing OMP claims. Hermes's evals emphasize compaction recall and trajectory dumps.

**Default memory will not leak a user biography into a fixture** unless you turn a backend on. That is the right default for a repo-scoped coding eval.

**No nested Grok Build skill in the default coding path.** OMP can *select* `grok-build` as a *model*. It does not instruct the agent to shell out to the `grok` CLI.

---

## Where Hermes is better

**As a long-lived personal agent.** Memory, skills that self-improve, FTS5 session search, Honcho-class providers, cron, and a multi-platform gateway are the product. OMP's memory/learn tools are repo-scoped add-ons. If the research question is "does a learning loop change multi-day assistant quality," Hermes is the SUT and OMP is the wrong control.

**Execution isolation options.** Seven terminal backends including Docker, SSH, and cloud sandboxes, with file tools routed through the same backend. OMP's isolation story for agents is worktrees and approval modes, not a first-class remote/container execution target in the core loop.

**Honest security write-up.** `SECURITY.md` names the OS as the only load-bearing boundary and tells reporters not to file in-process heuristics as vulnerabilities. That is clearer than most coding CLIs.

**Supply-chain posture in the Python install.** Exact pins and a written Mini Shai-Hulud rationale. OMP's JS/Rust graph is large; it does not advertise the same pin policy in `package.json`.

**Research trajectory pipeline.** `batch_runner.py` / `mini_swe_runner.py` / compression are built to emit training data. If this project ever studies harness traces as datasets, Hermes already speaks that format.

**Provider and portal convenience.** Nous Portal plus Tool Gateway is one OAuth for model and several hosted tools. OMP's catalog is also broad. Hermes's product pitch is "do not collect five keys."

**Surfaces for non-terminal work.** Talking to the agent from Telegram while a VM works is not a coding-eval feature. It is a real capability OMP does not attempt.

---

## Evidence table

| Axis | OMP | Hermes Agent | Evidence |
|------|-----|--------------|----------|
| Kind | Coding CLI / TUI, Pi fork | Personal runtime / CLI | READMEs; landscape memo |
| Version | 18.0.4, `omp` | 0.20.5, `hermes` | `packages/coding-agent/package.json`; `pyproject.toml` |
| Loop | `pi-agent-core` `agentLoop`; shared `AgentSession` | `AIAgent.run_conversation` → `conversation_loop` | cited files |
| Headless | `omp -p`, `--mode json\|rpc\|acp` | `hermes -z`, `chat -q`; oneshot YOLO | `docs/cli-reference.md`; `hermes_cli/oneshot.py` |
| Edit | Hashline `edit` + `ast_edit` | `patch` / `write_file` | hashline `execute.ts`; `toolsets.py` |
| LSP | 14-op `lsp` tool, writethrough | Post-write diagnostics | `lsp/types.ts`; `features/lsp.md` |
| DAP | 28-op `debug` | Not a first-class DAP tool | `tools/debug.ts` |
| Memory | Off by default; project-scoped | On by default; `MEMORY.md`/`USER.md` caps | `docs/memory.md`; `features/memory.md` |
| Learning | `learn` / skills optional | Autonomous skills + nudges | `builtin-names.ts`; README; conversation loop |
| Grok auth | `xai-oauth`, default `grok-4.6` | `xai-oauth`, default `grok-4.6`; separate `~/.grok/auth.json` | catalog test; xAI OAuth guide; grok skill |
| Nested coding CLI | No grok-skill delegation | Optional `grok -p` skill | `optional-skills/.../grok/SKILL.md` |
| Safety default | `yolo` | smart approvals; oneshot forces YOLO | `approval-mode.md`; `oneshot.py`; `SECURITY.md` |
| Multi-agent | `task` worktrees, advisor | `delegate_task`; optional lab CLIs | README; `delegate_tool.py` |
| License | MIT | MIT | `LICENSE` both |
| In-tree eval | Edit benches, metaharness | Compaction/browser/readtool; trajectories | package dirs; `evals/` |

---

## Unknowns

- **No runtime install in this pass.** Flag tables and docs can drift from the binary.
- **Vendor benches.** OMP README hashline lifts and Hermes compaction scores were not reproduced.
- **Live tool counts** once MCP and plugins register. Counts above are source registries at HEAD.
- **Hermes architecture.md test census** is stale vs `tests/` at HEAD.
- **Install state.** Protocol must record whether the grok skill, Portal, or a coding toolset was on.
- **SuperGrok OAuth 403** (Hermes issue #26847). If OAuth inference is blocked, the cell silently becomes `XAI_API_KEY`.
- **ACP / Windows.** Documented, not exercised here.

---

## What a fair empirical eval still needs

No pairwise winner follows from this note. A fair coding comparison would:

1. Freeze binaries (`omp` 18.0.4 / commit `969a94c1`; `hermes` 0.20.5 / commit `0268c0b8`) and print `--version` into the log.
2. Pin one model slug and one auth class. Recommendation for a Grok-capable cell: `grok-4.6` + `xai-oauth`, or label a `grok-build-0.1` system row separately. Do not mix SuperGrok OAuth with `XAI_API_KEY` in one table.
3. **Disable** Hermes optional skills `grok`, `codex`, `claude-code`, and any other nested coding CLI. Confirm with `hermes tools` / skills listing in the artifact.
4. Use headless argv only: `omp -p --mode json --max-time …` vs `hermes -z --model … --provider … --toolsets …`. Log the exact command. For Hermes, either accept oneshot YOLO or do not use `-z` if the protocol wants approvals.
5. Freeze memory: OMP `memory.backend: off`; Hermes a fresh `--profile` with memory writes off or a wiped `memories/` directory.
6. Pre-declare tasks (repair / feature / refactor) with fixture SHAs and a test oracle, as in the Wave 1 adversarial review's minimum protocol. Same prompt text.
7. Record edit format and sandbox/approval mode as columns, not as a footnote.
8. Keep Hermes out of a table titled "Grok-native harness effect" unless steps 2 through 5 hold. Otherwise put it on a personal-runtime track and compare it to OpenClaw-class systems, not to OMP.

Until those runs exist, the only honest summary is: **OMP is the stronger coding-harness candidate; Hermes is the stronger learning/memory personal-agent candidate; they should not share a Grok-fixed leaderboard without the constraints above.**
