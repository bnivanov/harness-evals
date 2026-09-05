# OMP vs ZCode: pairwise comparison

**Status:** literature comparison. No scores. No runs claimed.  
**Date:** 2026-08-25  
**Project:** `bnivanov/llm-harness-eval`  
**Question:** Holding the model as fixed as the products allow, what does the official GLM agentic development environment change relative to Oh My Pi as a coding harness?

This note compares two coding harnesses. It does not rank GLM against Grok, Claude, or GPT. Community overlays are ecosystem, not the system under test. No scores are invented.

---

## Identity

**OMP (Oh My Pi)** is a MIT-licensed terminal coding agent. Source: [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi). CLI `omp`; package `@oh-my-pi/pi-coding-agent`; homepage [omp.sh](https://omp.sh). It is a fork of Mario Zechner's [Pi](https://github.com/badlogic/pi-mono), extended with sessions, tools, subagents, slash commands, and TypeScript extensions. The README (retrieved 2026-08-25) reports 60+ providers, 31 built-in tools, 14 LSP operations, 28 DAP operations, and about 80,000 lines of Rust in the native core.

**ZCode** is Z.ai / Zhipu's official Agentic Development Environment (ADE) for GLM. [zcode.z.ai/en](https://zcode.z.ai/en) calls it the "Official Harness for GLM-5.3." Docs at [zcode.z.ai/en/docs/welcome](https://zcode.z.ai/en/docs/welcome) describe an Electron desktop that centers agent chat and places a file manager, terminal, Git panel, and live browser preview around that conversation. The first-party loop is **ZCode Agent**, "deeply adapted for the GLM-5.3 model family" ([agents](https://zcode.z.ai/en/docs/agents)). The app is free; inference is billed through a GLM Coding Plan, API keys, or third-party providers ([connect models](https://zcode.z.ai/en/docs/configuration)).

**Out of scope as SUT.** OpenAI Codex is a different lab harness. Older ZCode pages describe a [multi-agent workspace](https://zcode.z.ai/en/docs/model-providers) that can host Claude Code, Codex, Gemini, or OpenCode inside the same desktop. That host-other-CLI mode is not ZCode Agent. Community overlays such as [emco1234/fable-mythos-zcode](https://github.com/emco1234/fable-mythos-zcode) are configuration packages on top of ZCode.

**Closed-source limit.** No public GitHub repository contains the ZCode ADE agent source. [zai-org](https://github.com/zai-org) publishes GLM model repos, [GLM-skills](https://github.com/zai-org/GLM-skills), and a [feedback](https://github.com/zai-org/feedback) tracker. Packaging trees and community Linux converters ship binaries or wrappers, not a readable control loop. Internals that are not in official docs are marked unknown.

---

## Method

Primary sources, in that order: GitHub for OMP; official ZCode docs and homepage for ZCode; zai-org repos where they exist. Secondary blogs and reverse-engineering notes are labeled as such. Vendor benches (OMP hashline tables, GLM-5.3 blog scores) are product claims, not this project's measurements.

---

## Architecture and control loop

OMP is a TypeScript monorepo on Bun with a native Rust N-API addon. `@oh-my-pi/pi-agent-core` owns the agent runtime, tool calling, and compaction. `@oh-my-pi/pi-coding-agent` owns the CLI, session lifecycle, and the coding tool surface. The loop is the usual coding-agent cycle: model turn, tool calls (`read`, `edit`, `bash`, `task`, …), persist session, compact when the window fills. Four wrappers share that engine: interactive TUI, one-shot `omp -p`, Node SDK, and stdio RPC / ACP ([README](https://github.com/can1357/oh-my-pi)).

ZCode Agent is a first-party desktop loop. Official docs do not publish the scheduler, tool-schema source, or compaction algorithm. What they do publish is the product-level state machine. The user starts a task, adds context (`@` files, `#` past conversations, attachments), picks an execution mode and a thought level, and optionally sets a Goal Mode objective. The agent then plans, edits, runs commands, drives the built-in browser, and reviews Git state inside one task ([welcome](https://zcode.z.ai/en/docs/welcome), [agents](https://zcode.z.ai/en/docs/agents)). Goal Mode adds a second loop around that: after every round a separate check decides whether the objective is met, using file changes, command output, and tests rather than a confident-sounding reply ([goal](https://zcode.z.ai/en/docs/goal)).

The real split is inspectable process versus a productized long-horizon session. OMP's loop is a program you can read, pin, and drive headless. ZCode's loop is a desktop workflow built so GLM-5.3's long-context training (stable 1M context, long-horizon RL, flexible effort) can keep goals, files, terminal output, browser state, execution mode, and Git branch in one task. Whether that extra product state reduces mid-task amnesia is empirical. The docs assert it. This repo has not measured it.

---

## Tools

OMP ships 31 tools in one namespace: `read`/`write`/`edit` (hashline), `ast_edit`/`ast_grep`, `grep`/`glob`, `bash` with in-process coreutils, persistent Python and Bun `eval` cells that can call back into agent tools, `lsp`, DAP `debug`, `task`/`hub`/`todo`/`ask`, `browser`, `computer`, `web_search` (23 backends), optional `github`. Memory tools sit behind `memory.backend`. Several tools are off by default. Hashline is the edit bet. The model points at content-hash anchors instead of retyping lines; stale anchors reject the patch. The README cites vendor-internal lifts (Grok Code Fast 1 edit pass rate 6.7% to 68.3%; Grok 4 Fast -61% output tokens). Those numbers are not reproduced here.

ZCode's ADE is the tool surface: file tree, integrated terminal, Git panel, a built-in browser the agent can drive, an element picker that turns a DOM node into chat context, background commands, and bundled find/grep replacements ([ADE tools](https://zcode.z.ai/en/docs/ADE-tools)). Subagent checklists name `Read`, `Grep`, `Glob`, `Bash`, `Edit`, `Write`, `WebFetch`, `WebSearch`, `TodoWrite` ([subagents](https://zcode.z.ai/en/docs/subagents)). MCP adds the rest. There is no public hashline equivalent, no first-party LSP/DAP catalog matching OMP's 14/28 operations, and no documented in-process shell.

OMP is denser in editor-grade code intelligence and edit protocol. ZCode is denser in a shared visual workspace the user can watch.

---

## Context and memory

OMP inherits instruction files already on disk (Cursor MDC, Cline rules, Codex `AGENTS.md`, Copilot `applyTo`, Gemini, Windsurf, and related layouts) without a migration step. Compaction is part of the agent core; `snapcompact` exists as a package with a SQuAD eval suite. Memory is agent-curated: `retain`, `learn`, `recall`, `reflect`, `memory_edit`, plus a per-session mental model. Backends are selectable (`local`, Hindsight, Mnemopi) and project-scoped by default.

ZCode reads two instruction files only: `~/.zcode/AGENTS.md` and workspace-root `AGENTS.md`. Nested files, `@import`, and runtime `CLAUDE.md` are out (onboarding can copy Claude files once). `/compact` is a user command. Automatic compaction reserves an output buffer (docs: about 34K tokens; a 1M window compacts around 966K) with no user-facing threshold. Project Memory is off by default. When on, the agent distills facts after successful turns into new sessions in that project. Memories are local, not git-tracked, not browsable or clearable from the UI, and invisible to subagents ([agents](https://zcode.z.ai/en/docs/agents)).

GLM-5.3's 1M context is a model property ZCode exposes as a product feature (Coding Plan names ending in `[1m]` are fixed at 1M). OMP uses whatever window the selected model reports. A 1M GLM session in OMP is still OMP's pipeline (roles, compaction, memory backend), not ZCode's task object that also holds browser and Git UI state.

---

## Auth and model pinning

This axis decides whether a later eval can hold the model fixed.

OMP is multi-model by construction. The README lists frontier APIs, coding-plan OAuth (including **Z.AI / GLM Coding Plan** and **Zhipu Coding Plan**), and local OpenAI-compatible servers. Ten roles route by intent (`default`, `smol`, `slow`, `plan`, `commit`, `vision`, `designer`, `task`, `advisor`, `tiny`). Fallback chains, path-scoped model sets, and round-robin keys are documented. Pinning GLM-5.3 in OMP is a first-class configuration, not a hack.

ZCode's product identity is GLM-native. Sign-in is Z.ai or BigModel Coding Plan; trial quota is GLM-5.3 / GLM-5-Turbo. The same settings panel also documents Anthropic, OpenAI, OpenRouter, Moonshot, MiniMax, Xiaomi MiMo, and arbitrary Anthropic/OpenAI-compatible custom providers ([configuration](https://zcode.z.ai/en/docs/configuration)). Thought-level maps exist for GLM-5.3 (`low`/`high`/`max`, default `max`), GLM-5.2, GPT, Claude, Kimi K3, and DeepSeek V4. ZCode Agent is GLM-optimized (prompt, cache story, Goal Mode, marketing) without being GLM-locked at HTTP. Coding Plan context windows are server-issued; local edits get overwritten on sync.

July 2026 secondary writeups (Developers Digest among them) still said ZCode did not support Claude or GPT. Official connect-models docs as of this fetch contradict that. Treat the docs as current.

The clean pin for this project is **GLM-5.3 via Coding Plan or the same API endpoint in both clients**. Pointing ZCode Agent at Grok or Claude through a custom provider is possible, but the loop and advertised cache hit rates are not claimed for those models. A Grok-fixed ZCode row would be a lab-stack system eval, not a harness-only contrast.

---

## Surfaces

OMP is terminal-first. Interactive TUI is the default. `omp -p` is the CI/script entry. RPC is NDJSON over stdio. ACP talks to editors (Zed is the documented example) and gates writes through `session/request_permission`. There is no first-party Electron ADE.

ZCode is a desktop ADE. Agent chat is the center; file manager, terminal, Git, and browser are panels. Official downloads cover macOS, Windows, and Linux Beta ([homepage](https://zcode.z.ai/en)). A CLI runtime (`zcode.cjs`) ships under `resources/glm/`. [zai-org/feedback#51](https://github.com/zai-org/feedback/issues/51) (discussed against App 3.8.1 / CLI 0.16.3 in mid-August 2026) reports a missing `@zcode/tui` package and broken CLI OAuth, blocking `zcode --prompt` / `zcode login` on some installs. Unofficial TUI wrappers that extract the bundled runtime are not the official SUT.

Unattended, pin-able, loggable turns are a supported OMP path. ZCode's supported path is the desktop session, plus remote/bot follow-up onto a machine that is already running the app.

---

## Extensibility

OMP extensions are TypeScript modules with the same tool API, slash commands, hotkeys, and TUI primitives as the builtins. MCP, skills, and `/reload-plugins` are first-class. First run imports rules, skills, and MCP configs already on disk from other agents. In-tree extras include a collab web client, a browser-relay Chrome extension, and `pi-metaharness` runners.

ZCode packages skills (`SKILL.md`), slash commands, subagents, hooks, and MCP into plugins with a `plugin.json` manifest ([plugin](https://zcode.z.ai/en/docs/plugin)). MCP lives in `~/.zcode/cli/config.json` or workspace `.zcode/config.json`, with `.agents/mcp.json` as fallback. Settings can import MCP and skills from Claude Code, Codex CLI, OpenCode, and similar. Custom subagents are user-level Markdown under `~/.zcode/agents/` (Beta; workspace-level from Settings is not available yet). Skills ship through plugin marketplaces, not a standalone skill store.

OMP extensions are the same language as the product. ZCode plugins sit on a closed host. Reverse-engineering `zcode.cjs` is not treated as a specification here.

---

## Safety

OMP approval is config-driven: `tools.approvalMode` (`yolo`, prompt tiers), per-tool `allow`/`prompt`/`deny`, flags `--approval-mode` / `--auto-approve` / `--yolo`. ACP routes destructive tools through the editor. Hashline rejects stale patches. Time-traveling stream rules abort mid-token and inject a reminder. `computer` and optional GitHub/security tools are gated. The README does not claim a kernel sandbox.

ZCode execution modes are the visible safety story ([safety confirmation](https://zcode.z.ai/en/docs/safety-confirm)): Ask before changes (default, confirm every edit or command); Edit automatically (edits apply, commands still confirm); Plan (plan first, conflicts with Goal Mode auto-continue); Full access (fewer confirmations). Permission requests pause the task and block the composer. Decisions include Allow, Always Allow, Reject, Always Reject, plus session/project variants. Clarifying questions can auto-continue after five minutes; permission prompts never do. Backgrounded Explore subagents are read-only.

ZCode makes the human-in-the-loop story obvious in a GUI. OMP makes the policy a file you can commit and replay. Neither public source describes a Landlock/Seatbelt-class sandbox for the default local loop.

---

## Multi-agent and Goal Mode

OMP's `task` tool fans out subagents, optionally into isolated worktrees (`pi-iso`: APFS clones, btrfs/zfs reflinks, overlayfs, projfs, rcopy). Yields can be schema-validated. Agent Hub (`Alt+A`) steers, revives, or kills workers. An `advisor` role attaches a second model that comments on every turn. Keywords `orchestrate` and `workflowz` opt a turn into parallel or deterministic multi-subagent work. `/vibe` is a director mode over persistent workers. There is no documented Goal Mode with a separate round-end verifier and usage budget.

ZCode Goal Mode is the long-horizon product ([goal](https://zcode.z.ai/en/docs/goal)). `/goal <objective>` sets one session objective. After each round a separate check looks for evidence (changed files, command output, tests). Unfinished todos block completion. Pause, resume, replace, and clear survive session close. A goal also stops at a usage budget. Plan mode cannot run with a goal. Built-in subagents are `general-purpose` (all tools) and `Explore` (read-only); custom roles add model, thought level, tool list, and `maxTurns`. Subagents cannot spawn subagents. Side conversations do not get Goal Mode. Forking copies history and goal progress without rolling back the disk.

OMP's multi-agent story is isolation and typed handoff. ZCode's is objective management plus a verifier, so the user does not have to type "continue."

---

## Open source vs proprietary

OMP is MIT, with the TypeScript/Rust tree on GitHub, nix flakes, Homebrew, bun, and a public changelog.

ZCode the ADE is proprietary. The app is free. GLM weights are a separate open-weight story (zai-org / Hugging Face; check license per drop). Public zai-org code does not include the ADE loop. Community ports grant no license to the app.

Reproducing OMP can start from a commit SHA. Reproducing ZCode starts from an installer version, an account, and docs that can move without a diff.

---

## Evaluation and reproducibility

OMP publishes harness-facing eval machinery in-tree: `pi-metaharness` (Harbor storage, REST/SSE, dashboard) and `typescript-edit-benchmark`. Hashline marketing quotes model-specific edit metrics. Those are vendor benches.

ZCode / GLM marketing quotes model benches (Terminal-Bench 3.0, DeepSWE, and related on the GLM-5.3 blog). Those are **model** scores, often under unspecified or lab harnesses, not ZCode-Agent-as-SUT scores. Feedback [#78](https://github.com/zai-org/feedback/issues/78) claims the same GLM-5.2 prompt behaved worse in ZCode Agent than in Claude Code and blames a thin system prompt. That is one reporter who read `zcode.cjs`. It is not a spec and not a score.

This file adds no numbers of its own.

---

## Remote and bot control

OMP collaboration is `/collab`: a relay link or QR, read-write pair or view-only, client-side sealed frames. The `browser` tool can attach to Chrome or drive other Electron apps. `computer` can drive the host desktop. There is no first-party WeChat / Feishu / Telegram bot.

ZCode splits where code runs from where you talk. Remote development uses an SSH host or local Docker container ([ADE tools](https://zcode.z.ai/en/docs/ADE-tools)). Remote Control is a phone scan onto a desktop session that already exists. Bot Channel documents WeChat and Feishu pairing, workspace allowlists, and reply granularity ([bot channel](https://zcode.z.ai/en/docs/bot-channel)). The homepage also lists Telegram. The Bot Channel doc fetched 2026-08-25 names only WeChat and Feishu, and says DingTalk, Discord, and WeCom come later. Telegram is a homepage claim not confirmed in that doc. Secondary tutorials are not official.

Remote-control and bot paths drive a desktop session that must already be running. They do not replace a headless CI runner.

---

## Where OMP is better

OMP is the better **research SUT** and the better **multi-model pin**. The loop is public MIT code. `omp -p`, RPC, ACP, and the Node SDK are documented unattended entry points. GLM-5.3 is one provider among sixty, so a later GLM-fixed cell can sit next to a Grok-fixed cell without changing products. Role routing, fallback chains, and path-scoped models freeze in config.

OMP is also denser as a **coding tool runtime**. Hashline, in-process grep/shell/AST, LSP, DAP, persistent kernels with tool re-entry, isolated worktrees, schema-validated subagent yields, and an advisor model are in the box. If the failure is a bad patch or a rename that missed a barrel file, OMP has an explicit mechanism. ZCode's public docs do not.

An OMP extension is a TypeScript module in the same API as the builtins. ZCode plugins sit on a closed host whose scheduler you cannot patch. Instruction-file inheritance is broader on OMP: it reads formats teams already committed. ZCode wants a single workspace `AGENTS.md` and will not merge nested files.

---

## Where ZCode is better

ZCode is the better **native GLM product**. The ADE exists so GLM-5.3's long-horizon training has a matching session object: goal, files, terminal, browser, execution mode, Git, thought level. Cache-hit and idle-time-task claims are Coding Plan product features. OMP can call the same API. It does not ship the GLM-specific Goal Mode verifier, the 1M `[1m]` SKU handling, or the in-app quota UI.

ZCode is also the better **operator surface for long work with a human still in the loop**. Goal Mode's round-end evidence check, pause/resume that survives restart, usage budget, side conversation, and conversation fork are productized. Execution modes plus a confirmation panel are easier to explain than a YAML approval matrix. The built-in browser with element picker is a first-class ADE panel, not a Puppeteer sidecar.

Remote follow-up is a ZCode category OMP does not occupy. WeChat and Feishu Bot Channel, mobile Remote Control, and SSH/Docker remote development keep a desktop task moving after the user leaves the keyboard.

A downloadable ADE (macOS, Windows, Linux Beta) plus a 5-day GLM trial is a lower onboarding cost than installing a Bun/Rust TUI and wiring `models.yml`.

---

## Evidence table

| Axis | OMP | ZCode Agent / ADE | Evidence | Confidence |
|------|-----|-------------------|----------|------------|
| Kind | CLI/TUI coding harness (Pi fork) | Electron ADE; first-party ZCode Agent | [oh-my-pi](https://github.com/can1357/oh-my-pi); [zcode.z.ai/en](https://zcode.z.ai/en) | High |
| License / source | MIT, public monorepo | Proprietary app; GLM weights separate | GitHub LICENSE; no ADE source in zai-org | High |
| Control loop | Readable agent core + coding-agent CLI | Unpublished; Goal Mode + execution modes documented | README; [goal](https://zcode.z.ai/en/docs/goal) | High on OMP; medium on ZCode internals |
| Edit protocol | Hashline (content-hash anchors) | `Edit`/`Write` named; format unpublished | README; [subagents](https://zcode.z.ai/en/docs/subagents) | High / low |
| LSP / DAP | 14 LSP ops, 28 DAP ops | Not documented as first-party tools | README | High / unknown |
| Context files | Inherits many vendor layouts | `~/.zcode/AGENTS.md` + workspace `AGENTS.md` only | README; [agents](https://zcode.z.ai/en/docs/agents) | High |
| Memory | `retain`/`recall`/backends | Optional Project Memory; not inspectable | README; agents doc | High |
| Model pin | 60+ providers; GLM Coding Plan listed | GLM-native; custom Anthropic/OpenAI/OpenRouter/etc. | README; [configuration](https://zcode.z.ai/en/docs/configuration) | High |
| Headless | `omp -p`, RPC, ACP, SDK | Bundled `zcode.cjs`; TUI/OAuth bugs reported | README; [feedback#51](https://github.com/zai-org/feedback/issues/51) | High / medium (CLI status drifts) |
| Goal / stop | User, plan mode, keywords | `/goal` + round verifier + budget | [goal](https://zcode.z.ai/en/docs/goal) | High |
| Subagents | `task` + isolated worktrees + hub | general-purpose, Explore, custom (Beta) | README; [subagents](https://zcode.z.ai/en/docs/subagents) | High |
| Safety UX | Config + ACP permissions | Four execution modes + confirm panel | [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/HEAD/docs/approval-mode.md); [safety](https://zcode.z.ai/en/docs/safety-confirm) | High |
| Bots | `/collab` relay | WeChat, Feishu documented; Telegram on homepage only | [bot channel](https://zcode.z.ai/en/docs/bot-channel); homepage | High for WeChat/Feishu; low for Telegram |
| Eval artifacts | In-tree metaharness / edit bench | Model blogs, not harness protocol | README packages; z.ai blog | Medium (vendor claims) |

---

## Unknowns

1. ZCode Agent system prompt, tool JSON schemas, edit format, and compaction. Closed binary. Feedback [#78](https://github.com/zai-org/feedback/issues/78) is not a spec.
2. Telegram bot control. Homepage lists it; Bot Channel doc fetched 2026-08-25 does not.
3. Official headless CLI. Feedback#51 reports missing `@zcode/tui` and broken CLI OAuth on some desktop builds. Re-check the installer before designing CI around `zcode --prompt`.
4. How much "deep GLM integration" is prompt and tools versus router and cache. The host is unreadable.
5. Whether a custom-provider Claude/GPT/Grok path is a fair harness or a GLM loop aimed at another HTTP API. Thought-level maps exist; Goal Mode and Coding Plan cache are documented around GLM.
6. OMP hashline pass-rate tables. Vendor-internal until a shared edit-failure corpus exists.
7. Linux ADE quality (official Beta versus community converters). Not exercised here.
8. Whether the current GLM-5.3 ADE still embeds Codex/Claude Code as hosted CLIs (legacy-styled docs). This comparison's SUT remains ZCode Agent either way.

---

## Fair empirical evaluation still needed

Nothing above is a performance result.

**Preferred pin: GLM-5.3, same endpoint, both harnesses.** OMP already lists Z.AI / GLM Coding Plan. ZCode Agent is the official client. Record base URL, model id (including `[1m]` if used), thought/effort, and auth class (Coding Plan OAuth versus API key). Do not mix Coding Plan quota with pay-as-you-go in one cell.

A Grok-fixed ZCode cell is not the native experiment. Custom providers can point ZCode Agent at non-GLM APIs; the product loop is still sold as GLM-5.3's harness. On a Grok-fixed table, ZCode belongs on a lab-stack / ADE track, not next to Pi and Grok Build.

**Surface control.** OMP: `omp -p` or RPC, `--approval-mode` frozen, commit SHA recorded. ZCode: documented desktop or CLI entry, execution mode frozen (Full access or Edit automatically, matching OMP yolo/auto). If official CLI login fails, skip scored ZCode rather than score a community TUI wrapper.

**Tasks.** Same three pre-declared tasks as other pairwise notes: focused edit, test-gated bugfix, multi-file feature with a checkable stop. Put the stop condition in ZCode's `/goal` string and in the OMP prompt. Do not enable fable-mythos-zcode. If that overlay is tested later, label it `ZCode + overlay`.

**Metrics.** Hidden-test success, cost (tokens or Coding Plan credits, reported separately), wall time, edit retries, human confirmation count, headless or not. No single harness-IQ column.

Until those runs exist, the only defensible summary is structural. OMP is the open, pin-able, tool-dense terminal harness that can also speak GLM. ZCode is the closed GLM ADE with Goal Mode, a shared visual workspace, and chat-tool remote control. Which of those properties moves SWE-style success is what this repo is for, and it is not yet measured.
