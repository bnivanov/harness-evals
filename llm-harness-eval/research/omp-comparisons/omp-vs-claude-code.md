# OMP versus Claude Code: a harness comparison

**Status:** desk research, no scored runs  
**Date:** 2026-08-25  
**Scope:** control loop, tools, context, skills, hooks, subagents, MCP, auth, surfaces, safety. Not Claude-the-model versus Grok-the-model.  
**Audience:** `bnivanov/llm-harness-eval` public notes

This note compares two coding *harnesses*. OMP is an open fork of Pi with a large built-in tool set. Claude Code is Anthropic's first-party agent, sold across terminal, IDE, desktop, and web. The contrast is not which chatbot is smarter. It is how each wrap turns a model into a repo worker, and which pieces of that wrap are locked to Anthropic's models or hosted stack.

Vendor marketing already has [omp.sh/vs/claude-code](https://omp.sh/vs/claude-code). This write-up does not reuse that copy. Claims come from GitHub, official docs, and one vendor edit microbenchmark whose method is quoted, not treated as SWE-bench.

---

## Identity

| | **OMP (Oh My Pi)** | **Claude Code** |
|---|---|---|
| What it is | Terminal-first coding agent. Fork of [Pi](https://github.com/badlogic/pi-mono) by Mario Zechner; coding surface by Can Bölük / Stencil Labs | Anthropic's agentic coding product. Same engine advertised across CLI, IDE, desktop, and browser |
| Binary / package | `omp`; `@oh-my-pi/pi-coding-agent` | `claude`; npm `@anthropic-ai/claude-code` is documented as deprecated. Installers at [overview](https://code.claude.com/docs/en/overview) |
| Source | Full MIT monorepo: TypeScript agent + Rust natives | Proprietary. GitHub is a **tracker**, not the CLI tree |
| License | [MIT](https://github.com/can1357/oh-my-pi/blob/main/LICENSE) | [All rights reserved](https://github.com/anthropics/claude-code/blob/main/LICENSE.md), Anthropic Commercial Terms |
| Docs | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi), [omp.sh](https://omp.sh) | [anthropics/claude-code](https://github.com/anthropics/claude-code), [code.claude.com/docs](https://code.claude.com/docs/en/overview) |
| Model posture | Multi-provider, role-routed, BYOK-first | Claude-family first. Cloud providers for Claude. Gateway retargets exist; they are not a first-class catalog |

**Closed-source limit, stated once.** `anthropics/claude-code` ships a README, changelog, plugins, and a one-line license. It does not ship the agent loop. [Issue #47465](https://github.com/anthropics/claude-code/issues/47465) records that visitors reasonably expect source and do not find it. Claims below about Claude Code internals are *documented behavior*, not audited code. OMP's loop, tools, and hook runner can be read in tree.

---

## Method

Primary sources, retrieved 2026-08-25.

OMP: [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) README; [docs/sdk.md](https://github.com/can1357/oh-my-pi/blob/main/docs/sdk.md), [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md), [lsp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/lsp-config.md), [agent-hub.md](https://github.com/can1357/oh-my-pi/blob/main/docs/agent-hub.md); [omp.sh](https://omp.sh); Can's [harness-problem post](https://blog.can.ac/2026/02/12/the-harness-problem/).

Claude Code: official docs for [overview](https://code.claude.com/docs/en/overview), [how it works](https://code.claude.com/docs/en/how-claude-code-works), [features](https://code.claude.com/docs/en/features-overview), [tools](https://code.claude.com/docs/en/tools-reference), [memory](https://code.claude.com/docs/en/memory), [hooks](https://code.claude.com/docs/en/hooks), [sub-agents](https://code.claude.com/docs/en/sub-agents), [models](https://code.claude.com/docs/en/model-config), [costs](https://code.claude.com/docs/en/costs), [sandboxing](https://code.claude.com/docs/en/sandboxing), [headless](https://code.claude.com/docs/en/headless), [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview), [enterprise](https://code.claude.com/docs/en/third-party-integrations); tracker [README](https://github.com/anthropics/claude-code/blob/main/README.md) and [LICENSE.md](https://github.com/anthropics/claude-code/blob/main/LICENSE.md).

One composite bench with a primary artifact: Harbor [PR #44](https://github.com/harbor-framework/terminal-bench-2-1/pull/44), Terminal-Bench 2.1, Claude Opus 4.7 *plus* Claude Code. Secondary aggregator tables that disagree with each other are not quoted. No SWE-bench Verified or Pro figure is reproduced. Those tables score a **model+harness** pair. This pass did not retrieve an official current dump.

---

## Architecture and control loop

Both products are gather-context, take-action, verify loops. Claude Code says so in [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works): the model reasons, tools act, the harness supplies tools, context, and the execution environment. A question may stop after search. A bug fix cycles all three phases. The user can interrupt. That is the public architecture. System prompt, compaction, and the permission classifier are not in the public tree.

OMP's loop is inspectable. `@oh-my-pi/pi-agent-core` owns tool calling and state. `@oh-my-pi/pi-coding-agent` owns the CLI and SDK. `createAgentSession()` is the embedding entry, with print, RPC, and ACP wrappers around the same session. The README's "~80k lines of Rust core" is a size claim for in-process grep, glob, embedded bash, AST, PTY, and desktop control, not a quality score. The bet is that fork/exec on `rg` and `bash` is a tax, and that Windows without WSL should still run the same binary.

Two loop-level differences matter for evals.

**Edits.** Claude Code's `Edit` tool is exact `old_string` / `new_string` replacement. Docs are blunt: one whitespace mismatch misses; duplicates require a longer unique string or `replace_all`. That is the format Can's post calls `str_replace`, and it is the format this project will actually be measuring if we run Claude Code. OMP's `edit` tool is hashline: reads tag lines with short content hashes; patches name those anchors; a stale file rejects before apply. That is a harness choice, not a model upgrade. It also means an "edit success" metric is not comparable across the two SUTs unless the protocol scores *task* success, not patch-format compliance.

**Course correction without waiting for the next turn.** OMP's time-traveling stream rules abort a generation mid-token on a regex, inject a reminder, and retry. Claude Code's documented steer is interrupt-and-type, plus hooks and skills. Mid-stream abort-and-retry is not in the public Claude Code feature list. Whether the closed binary does something similar internally is an unknown.

---

## Tools

OMP advertises 31 named tools, pinable with `--tools`. The eval-relevant set is `read` / `write` / `edit` / `ast_edit` / `ast_grep` / `grep` / `glob`, `bash`, `eval` (persistent Python and Bun with tool re-entry), `lsp`, `debug` (DAP), `task` / `hub`, `browser`, `computer`, `web_search`, optional `github`. Internal URL schemes (`pr://`, `agent://`, `skill://`, `conflict://`) make GitHub objects and subagent outputs look like files. That design is in source, not a slogan.

Claude Code's [tools reference](https://code.claude.com/docs/en/tools-reference) is a longer product catalog: `Read`, `Edit`, `Write`, `Bash`, `Grep`, `Glob`, `Agent`, `Skill`, `WebFetch`, `WebSearch`, `LSP`, plan/worktree, `Workflow`, `SendMessage`, plus Anthropic-hosted tools (`Artifact`, `RemoteTrigger`, `PushNotification`, `SendUserFile`) that the same page marks unavailable on Bedrock, Vertex, Foundry, or when feature-flag fetching is off. Those last ones are **product-locked**. You cannot reproduce them in OMP.

**LSP.** Both have an `lsp` / `LSP` tool. OMP auto-detects a large built-in server list from cwd markers and PATH; config merges `~/.omp`, `.claude`, `.codex`, `.gemini`. Claude Code's how-it-works page still says code intelligence "requires [code intelligence plugins](https://code.claude.com/docs/en/discover-plugins#code-intelligence)." The tools page describes post-edit diagnostics and symbol navigation once a language server is running. For a fair eval, treat LSP as present-but-configured, not as a guaranteed default on both.

**Debugger.** OMP's `debug` tool is DAP. Claude Code's documented debug path is still Bash, tests, and reading traces. A "Debug" *persona* is not a debugger. If a task needs attach/step/evaluate, OMP has a harness feature Claude Code does not document as first-class.

**Shell.** Claude Code's Bash tool is a separate process per command; env vars do not persist; cwd carry-over is a special case. OMP embeds brush plus in-process coreutils and keeps shell sessions. That will change failure modes on Windows and on tasks that assume `export` survives.

---

## Context and memory

Claude Code's memory story is well documented. `CLAUDE.md` loads every session, at managed / user / project / local scopes, with `@import` and path-scoped `.claude/rules/`. Auto memory writes `MEMORY.md`; the first 200 lines or 25KB load next time. Compaction is automatic; `/context` shows what ate the window; MCP tools can be deferred via tool search. Subagents get their own windows and return summaries. It is also prompt-shaped. The memory page says CLAUDE.md is context, not enforcement. A rule that must hold belongs in a hook.

OMP does not own `CLAUDE.md` as a brand. It reads files other tools already wrote: Cursor MDC, Cline `.clinerules`, Codex `AGENTS.md`, Copilot `applyTo`, `.claude/`, in place. Memory tools `retain` / `recall` / `reflect` / `learn` sit behind `memory.backend` (local, Hindsight, or Mnemopi) and are off by default. The agent can promote a lesson into a managed skill. Whether that beats Claude Code auto memory is an empirical question this pass does not answer.

---

## Skills, hooks, instruction files

The extension *vocabulary* has converged. Both have skills (`SKILL.md`, description always in context, body on demand), hooks on lifecycle events, MCP as extra tools, subagents, and a packaging layer.

Claude Code's layering is the one enterprises will already have. Features-overview is explicit: CLAUDE.md for always-on rules, skills for on-demand workflows, hooks for "must happen every time," MCP for external systems, plugins to ship the bundle, managed policy files users cannot override. Hooks are shell, HTTP, MCP tool, LLM prompt, or a subagent, bound to events such as `PreToolUse`. They run on terminal, IDE, desktop, and web. A hook that must fire in CI, in VS Code, and on claude.ai/code is a Claude Code feature. OMP cannot match that claim.

OMP's hooks are TypeScript factories. `pi.on("tool_call")` can block or rewrite arguments; `tool_result` can redact. `--hook` is an alias for `--extension`. Skills load from `~/.omp/agent/skills`, `.omp/skills`, and also `.claude/skills`. MCP configs load from `.mcp.json` and the IDE-shaped files Claude/Cursor/VS Code already use. For a repo that already has a Claude Code setup, OMP's pitch is "point it at the same tree." Do not assume a `.claude/settings.json` hook block executes unchanged inside `omp`. The TS hook API is not Claude Code's JSON hook schema.

---

## Auth, model pinning, subscription versus BYOK

This axis is where "same model, vary harness" usually dies.

**Claude Code** is subscription-first. `/login` on a Claude Pro/Max/Team/Enterprise plan shares a usage pool with chat and Cowork. If `ANTHROPIC_API_KEY` is set, docs and this repo's billing map say the CLI bills API rates and **ignores the plan**. Enterprise can point at Bedrock, Vertex, Foundry, or Claude Platform on AWS. Model aliases are Claude aliases: `sonnet`, `opus`, `haiku`, `fable`, `best`. `ANTHROPIC_BASE_URL` "changes where requests are sent, not which model answers them." Community gateways can retarget the Anthropic Messages API at OpenRouter or LiteLLM. That is a *retarget*, not a documented multi-provider catalog. Several tools and permission features then fall off because they need Anthropic-hosted infrastructure or feature flags.

**OMP** is BYOK-first hybrid. The README lists sixty-plus providers and ten roles (`default`, `smol`, `slow`, `plan`, `commit`, `vision`, `designer`, `task`, `advisor`, `tiny`), with fallback chains, path-scoped models, and round-robin keys. OAuth exists for Anthropic, Codex, Copilot, SuperGrok, and others. You can pin Grok on `default` and a cheap model on `smol` without a proxy. That is the harness this project can actually hold Grok-fixed against Pi.

**Model-locked Claude Code features**, from official pages rather than rumor: auto permission mode's background classifier; Fable 5 availability and usage-credit consent; `EndConversation` only on named Claude families and interactive Anthropic surfaces; Artifacts / Routines / phone push / SendUserFile on Anthropic-hosted paths. Treat those as product, not as portable harness.

A same-Claude API-key cell is *possible*: OMP talking to `api.anthropic.com`, Claude Code with `ANTHROPIC_API_KEY` and `--bare` for CI. It is still not the product most people mean by "Claude Code," which is `/login` plus plan limits plus cloud teleport. Do not collapse those cells.

---

## Surfaces and extensibility

Claude Code is many surfaces on purpose. Terminal CLI, VS Code and Cursor extensions, JetBrains, desktop, claude.ai/code, mobile, Remote Control, Slack, GitHub Actions / GitLab CI, `claude --teleport` between web and local. Settings, CLAUDE.md, and MCP are supposed to follow the engine. The Agent SDK exposes the same loop in Python and TypeScript under Commercial Terms. Anthropic forbids third parties from offering claude.ai login through that SDK. Embedding Claude Code is a licensed product, not an MIT import.

OMP's four entry points are TUI, `omp -p`, in-process Bun SDK, and `omp --mode rpc` / `omp acp`. ACP is how it rides inside Zed. `/collab` puts a live session on a relay. No first-party VS Code Marketplace listing showed up in the sources used here. If the eval needs an IDE click-path, Claude Code wins by existing. If it is headless CLI, both have print mode; Claude Code's `--bare` is the documented way to stop a teammate's `~/.claude` from contaminating CI.

Extensibility follows license. OMP extensions use the same `registerTool` / event bus as built-ins. You can read why a tool failed. Claude Code extensions are skills, hooks, MCP, plugins, and in-process MCP custom tools. You cannot patch `Edit`. You can wrap it.

---

## Safety and approvals

Claude Code has the more complete *policy* story. Permission modes cycle with Shift+Tab: Auto, Manual, Accept edits, Plan. Auto is the documented default on Pro/Max/Team for interactive terminal and VS Code; a classifier reviews actions. Allow/deny rules in settings, managed org policies, sandboxed Bash (Seatbelt on macOS, bubblewrap on Linux/WSL2; native Windows unsupported), file checkpoints with Esc-Esc rewind, and PreToolUse hooks as enforcement. That is what a security team can write a standard against.

OMP's safety is more local. `ask` for structured questions; `ast_edit` stages a preview until `xd://resolve`; hashline rejects stale anchors; ACP routes writes through `session/request_permission`; hooks can fail closed on `tool_call`. Isolation for subagents uses `pi-iso` (APFS clones, reflinks, overlayfs). There is no documented OS sandbox equivalent to Claude Code's `/sandbox` panel, and no org-managed policy file that users cannot override. Fine on a throwaway eval VM. Not an enterprise rollout comparison.

---

## Subagents

Both spawn workers with separate context.

Claude Code: `Agent` tool; file-based `.claude/agents/` with frontmatter for tools, model, permission mode, isolation, skills, hooks; CLI `--agents` JSON; background by default; `SendMessage` and agent teams; dynamic `Workflow` scripts that run many subagents and return one result; cross-session messaging. The parent sees a summary, not the child's tool trace, unless you go looking. That matches a product that wants the main window clean.

OMP: `task` fans out, optionally into isolated worktrees; typed yield the parent reads as `agent://...`; peers can DM; Agent Hub (`Alt+A`) shows live transcripts, cost, steer, revive, kill. An `advisor` role is a second model that comments on the main turn. The design is "watch the workers," not "hide them." For evals that need to attribute which worker broke the tree, OMP's artifacts are easier to inspect.

---

## Open source, eval, reproducibility

OMP is MIT, including the SDK. You can pin a commit, read the system prompt builder, and diff a harness change. `@oh-my-pi/pi-metaharness` and `@oh-my-pi/typescript-edit-benchmark` live in the same monorepo. That does not make published numbers independent. Can's [12 Feb 2026 post](https://blog.can.ac/2026/02/12/the-harness-problem/) describes an in-house suite: 180 mutated React files, 3 runs, four tools only, pass if the file matches the pre-mutation original after format. Hashline versus patch versus replace. Grok Code Fast 1 is quoted as 6.7% to 68.3% when the *edit format* changed, same weights. Gemini 3 Flash +5 percentage points versus replace. Grok 4 Fast -61% output tokens. Treat that as a **vendor edit-format microbenchmark**, not SWE-bench, and not "OMP beats Claude Code."

Claude Code's public numbers, when they appear, are composites. Harbor [PR #44](https://github.com/harbor-framework/terminal-bench-2-1/pull/44) submitted **Claude Opus 4.7 (max) + Claude Code** on Terminal-Bench 2.1 at 68.9% ± 1.4% after disqualifications. Pair dated 2026-05-01, not a harness-only score. Later secondary blogs quote Fable 5 / Opus 5 pairings that do not agree with each other. This note does not pick among them. `--bare` plus `-p` plus `--output-format json` is the documented CI shape. You still cannot pin the closed binary's prompt the way you pin an OMP commit. The Claude Code SUT will drift with auto-update unless the eval pins an installer version.

---

## Evidence table

| Claim | OMP | Claude Code | Evidence quality |
|---|---|---|---|
| License / source | MIT, full tree | Proprietary; GitHub is tracker + plugins | High. LICENSE files and issue #47465 |
| Loop inspectable | Yes | Documented only | High |
| Default edit tool | Hashline anchors | Exact `str_replace` | High. README + tools-reference |
| Built-in DAP debugger | Yes | Not documented as a tool | High for presence/absence in docs |
| LSP | Built-in auto-detect | Tool + plugin/server setup | Medium. Config stories differ |
| Skills / MCP / hooks / subagents | Yes, TS-native + discovery of `.claude` | Yes, productized, org-managed | High for existence; medium for import fidelity |
| Native multi-provider pin | Yes, roles + fallbacks | Claude aliases; gateway is a retarget | High |
| Subscription path | Optional OAuth to many labs | Default `/login` shared with chat | High |
| IDE / web / mobile / cloud VM | ACP, collab web | First-party family | High |
| OS command sandbox | Isolation backends for tasks; no `/sandbox` equivalent found | Seatbelt / bubblewrap Bash sandbox | High for Claude Code; medium-negative for OMP |
| Headless CI | `omp -p`, SDK, RPC | `claude -p`, `--bare`, Agent SDK | High |
| Same-Grok native cell | Yes | No | High |
| Same-Claude API cell | Yes | Yes, if key set | High. Product `/login` cell is different |
| Independent SWE-bench harness-only | None retrieved | None retrieved | n/a |
| Vendor / composite benches | Hashline 180-task suite | Harbor TB2.1 Opus 4.7+Code | High as composites; **not** harness-only |

---

## Where OMP is better

**You can read the harness.** Wave 1's thesis is "holding a model fixed, how much does the loop change." OMP lets you name the loop: hashline versus replace, DAP, typed subagent yields, TTSR. Claude Code lets you name the *product*. If a run fails, OMP's failure is a file you can patch. Claude Code's is a changelog.

**Model is a parameter.** Ten roles, fallback chains, Grok OAuth, local llama.cpp, Anthropic API. The cell "Grok 4.6, OMP, API key X" is real. "Grok 4.6, Claude Code, native" is not. Gateway folklore does not make it native.

**Coding-tool density on the default path.** LSP auto-detect, DAP, hashline, ast-grep, GitHub-as-filesystem, persistent `eval` kernels. Claude Code can grow toward some of that with plugins and `gh`. OMP ships it. Headless evals will actually run those tools without a marketplace step.

**Fork-friendly CI.** Pin a git SHA. MIT SDK in-process. Discovery of `.claude/` can still contaminate a run; `createAgentSession` can turn it off.

**Worker observability.** Agent Hub and `agent://` outputs are files you can inspect. Claude Code's documented default is summary-back. Fine for UX. Worse for attributing which subagent dirty-wrote `src/`.

---

## Where Claude Code is better

**It is the product people already run.** Surfaces, SSO, managed CLAUDE.md, managed MCP allowlists, GitHub code review, Routines that keep running when the laptop is shut, teleport from phone to terminal. If the research question is "what does the modal 2026 Claude user get," Claude Code is the SUT. OMP is the alternative.

**Permission and sandbox story.** Auto mode, classifier, allow/deny, org policies that local settings cannot punch through, OS-enforced Bash sandbox, checkpoints. OMP can block `rm -rf` in a hook. Claude Code can refuse to run the command outside a Seatbelt/bubblewrap jail and then snapshot the file it did edit. Those are different safety levels. Call them that.

**Context productization.** CLAUDE.md load order, path-scoped rules, auto memory, `/context`, deferred MCP tool search, `--bare` for clean CI. The features-overview page is a taxonomy other harnesses now copy. OMP's inheritance of eight on-disk formats is generous. It is a compatibility layer, not a single documented memory model a team can standardise on.

**Subagent *product* depth.** Named teammates, workflows as scripts, cross-session messaging, isolation flags in frontmatter, SDK parity. OMP's `task` + Hub is strong for a TUI. Dynamic workflows have no OMP equivalent in the sources reviewed.

**Headless as an Anthropic surface.** `claude -p` with structured output, SIGTERM semantics, Agent SDK in Python and TypeScript, OpenTelemetry. OMP's SDK is Bun-first; RPC covers other languages. For a mixed Python research stack, Claude's SDK is easier, license notwithstanding.

**Claude-tuned loop, when Claude is the model.** If the model is Opus or Fable, Claude Code is the harness Anthropic ships those models into. Tool schemas, cache breakpoints, and the classifier are trained and tested together. OMP will call the same API. It will not have that joint optimization. A "fair" same-Claude comparison may still show Claude Code ahead *because the lab tuned the wrap*. That is a real harness effect. It is not evidence that Claude Code is better for Grok.

---

## Unknowns

- Exact Claude Code system prompt, compaction, and auto-mode classifier. Closed.
- Whether OMP's `.claude/` importer executes Claude Code *hooks* or only skills, agents, commands, and MCP JSON.
- Default LSP on a cold Claude Code install versus OMP auto-detect, no plugins.
- Prompt-cache and usage accounting for `/login` versus `ANTHROPIC_API_KEY` in both harnesses.
- Windows: OMP's in-process shell versus Claude Code's Git-for-Windows Bash or PowerShell. Not compared on hardware.
- Current Terminal-Bench 2.1 ranking for any OMP+model pair. Not retrieved. Do not invent one.

---

## Fair empirical eval still needed

A publishable harness contrast needs tasks, pins, and a model policy. This pair makes the policy ugly.

**Track that can hold a model fixed.** Same Claude API model id, same key, `omp -p` versus `claude --bare -p`, same repo, same three tasks, no MCP, no cloud. Report cost, turns, tests passed. Even here the edit tools differ, so score the *task*, not "did the patch apply on the first try." Hashline will look better on first-try apply. That is the microbenchmark Can already ran. Do not rediscover it and call it SWE-bench.

**Track that cannot.** Grok-fixed OMP versus Claude Code. There is no honest native cell. Call Claude Code a Track B lab stack, as the Wave 1 adversarial review already recommended, or retarget through a gateway and label the cell `claude-code+gateway+grok`, which is a third harness.

**Do not mix `/login` Claude Code with API OMP** in one table titled "harness only." Those are different ledgers and different routing.

Until those runs exist, the qualitative result is simple. OMP is the open, model-parameterized, debugger-and-hashline coding loop. Claude Code is the closed, Claude-joint, multi-surface, policy-complete product. Pick the SUT that matches the claim. Do not average them.
