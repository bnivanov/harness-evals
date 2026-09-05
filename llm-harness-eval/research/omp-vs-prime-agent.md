# Feature deep dive: OMP vs Prime Agent

**Status:** research note (no scores; no runs claimed)  
**Date:** 2026-08-25  
**Audience:** Bobby, for *understanding* two Pi-lineage products before they share an eval table

This is not a leaderboard. Both sit on or next to [Pi](https://pi.dev). They answer different questions about what a coding loop should be. Treating them as "Pi plus more stuff" is how Wave 1 overweighted one OSS skeleton.

Official homes, used below:

| Product | Site / repo |
|---------|-------------|
| **Pi** | [pi.dev](https://pi.dev) · [earendil-works/pi](https://github.com/earendil-works/pi) (was `badlogic/pi-mono`) |
| **OMP (Oh My Pi)** | [omp.sh](https://omp.sh) · [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) |
| **Prime Agent** | [primeintellect.ai/blog/prime-agent](https://www.primeintellect.ai/blog/prime-agent) · [PrimeIntellect-ai/prime-agent](https://github.com/PrimeIntellect-ai/prime-agent) |

Vendor-reported numbers (OMP edit-format lifts, Prime ARC-AGI-3 / long-context tables) are **first-party claims**. They are not this project's results. Star counts are ignored.

---

## 1. Lineage

**Pi is the shared ancestor, not the shared product.** Mario Zechner's minimal terminal harness (now Earendil Works) ships four default tools (`read`, `write`, `edit`, `bash`), tree-structured sessions, skills, and four modes: interactive TUI, print/JSON, RPC, SDK. It deliberately skips MCP, subagents, plan mode, and permission popups. You extend it. You do not wait for the core to grow a debugger.

**OMP is a coding-first fork/rewrite of Pi.** Can Bölük's README is explicit: "Originally built on Mario Zechner's Pi, omp adds everything you're missing," and later "rewritten as a coding-first surface." The public binary is `omp`. The TypeScript packages still wear `@oh-my-pi/pi-*` names. A large Rust/N-API core (`pi-natives`, embedded bash, in-process grep/glob) sits under the TS loop. What shipped that Pi leaves to extensions: hash-anchored edits, LSP, DAP, ~31 tools, subagents, role-based routing, SuperGrok OAuth, ACP into editors. MIT.

**Prime Agent began as a hard fork of `pi-mono` and then changed the loop.** The coding-agent README still carries inherited `@earendil-works/pi-*` identifiers and a source-package `pi` bin for internal compatibility. Public releases rewrite the command to `prime-agent`. The TUI, session JSONL, extensions, and `/login` UX are Pi-shaped. The *agent* is not: one tool (`ipython`), recursive `rlm()` children, and a Continual Harness that `/refine` can edit. Prime Intellect's own README: "Our agent and TUI is built on top of `pi`." MIT.

Three products, one skeleton, two *independent variables*:

| Pair | What actually moved |
|------|---------------------|
| Pi → OMP | Tooling and edit reliability. Same class of loop (named tools, TUI cards, slash commands). |
| Pi → Prime | Loop architecture (REPL/RLM + self-editable harness state). Same TUI family, different model-facing schema. |

OMP vs Prime is therefore **not** "which fork added more features." OMP is Pi with a coding IDE wired in. Prime is Pi's TUI wrapped around a different machine.

---

## 2. Loop architecture

### Pi (control)

The model sees a small tool schema. It reads files, writes or patches them, runs `bash`, repeats. Context is the transcript plus `AGENTS.md` / skills. Compaction summarizes old turns. Subagents and MCP are things you build or install.

### OMP: many tools, hash-anchored edits, IDE protocols

The model still speaks *tools*. There are just a lot of them, and several are the interesting part.

**Edit model.** Default `edit` consumes [hashline](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/README.md): sections headed `[PATH#TAG]` where `TAG` is a four-hex content hash from the latest `read` / `grep` / successful `edit`. Hunks name original line ranges (`SWAP`, `DEL`, `INS`) or tree-sitter blocks. Stale tags are rejected (or recovered against a snapshot) instead of writing a wrong hunk into a moved file. `write` creates or overwrites. `ast_edit` / `ast_grep` add structural rewrites. Other edit modes (`apply_patch`, `patch`, `replace`) exist; hashline is the default unless a model is excluded.

OMP's own blog claims large pass-rate / token lifts once the edit format stops fighting the model (e.g. Grok Code Fast 1, Grok 4 Fast). **Vendor-reported. Not a Wave 1 number.**

**Tools.** README lists **31** built-in tools in one namespace. Core coding set: `read`, `write`, `edit`, `ast_edit`, `ast_grep`, `grep`, `glob`, `bash`, `eval` (persistent Python *and* JS cells that can call back into agent tools), `lsp`, `debug`, `task`, `hub`, `todo`, `ask`. Optional / setting-gated: `github`, `security_scan`, `browser`, `computer`, `web_search`, image/TTS, memory tools. Pin with `--tools`. Discover extras via `xd://`.

**LSP / DAP.** `lsp` exposes diagnostics, navigation, symbols, renames, code actions, raw requests (README: 14 ops). Renames go through `workspace/willRenameFiles`. `debug` drives a DAP session (README: 28 ops): breakpoints, stepping, threads, stack, variables. Documented adapters include lldb, dlv, debugpy.

**Subagents.** `task` fans work into isolated worktrees; results come back schema-validated. Agent Hub (`Alt+A`) inspects live children. Subagents run headless with `yolo` approval so they do not stall on prompts. The parent `task` call is the authorization boundary.

**Sessions.** Pi-style tree JSONL: `/tree`, `/fork`, `--continue` / `--resume`. Extra: `/collab` live share, `/vibe` director mode, `/fresh` stream reset, session import from Claude Code / Codex, ACP into Zed.

**Providers.** 60+ listed. API keys **and** OAuth. Roles (`default`, `smol`, `slow`, `plan`, `commit`, `advisor`, …) pin different models to different jobs. xAI is first-class both ways: `XAI_API_KEY` **and** SuperGrok / X Premium+ `xai-oauth` (`XAI_OAUTH_TOKEN` wins for that provider). Changelog: default Grok slug for both paths is `grok-4.6`.

**`eval` is not Prime's loop.** OMP *has* persistent kernels. They are one tool among many. The model still chooses `edit` / `lsp` / `bash` as separate calls.

### Prime: one IPython tool, `rlm()` children, `/refine`

The model sees **one** built-in tool: `ipython`. File ops, shell, skills, subagents, compaction, and harness CRUD happen as Python in a persistent kernel. Skills and MCP integrations are imported modules, not extra JSON-schema tools.

**`rlm(...)`.** Spawns a real child Prime Agent (own model, kernel, session tree, history). The call returns at *admission* with a handle, not the child's answer. Results arrive via `agent_message.send(...)`. Children persist; you can message them later, including after compaction. Fan-out is ordinary `async` Python. A2A messaging is limited to the "nuclear family" (parent / sibling / child).

**Continual Harness.** State `H = (ρ, G, K, M)`: supplemental prompt notes, subagent specs, skills, memory. Lives at `rlm.harness` and on disk (`harness/harness_state.json` session-local; optional global under `~/.prime/agent/harness/`). Same CRUD for each kind. The **base system prompt stays immutable**.

**`/refine`.** Reviews the current trajectory and applies a small evidence-backed CRUD edit (prompt note, memory, skill description, or subagent spec). Planning runs in the background. Apply is a short block at the next turn boundary. Snapshots support rollback by ID. The agent can also `await refine.run(...)`. Official README is careful: this does **not** replace packaging and reviewing new executable skills, and it does **not** retrain weights.

**Long-running extras Pi does not ship.** Background daemon (detach / reattach), Agents View, `/goal`, heartbeats, `prime-agent schedule`, `--autonomous` with shell gates and turn/token/wall-clock limits. Built for unattended research runs.

**Grok path.** Official [providers.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/providers.md): xAI is **`XAI_API_KEY`** (or `auth.json` key `xai`). Subscription `/login` list is Claude Pro/Max, ChatGPT Plus/Pro (Codex), GitHub Copilot. SuperGrok OAuth is **not** in that list. A community PR (`#1639`, discussion `#1640`) added `xai-oauth`; it was auto-closed by the vouched-author gate. Treat SuperGrok OAuth as **incomplete / ?** until it lands in official provider docs.

**Trust model.** README warning, quoted in spirit: model-generated Python and project commands run with your user permissions. Worker/kernel process isolation is for lifecycle recovery. It is **not** a security sandbox. Use a disposable clone or clean worktree.

```text
Pi / OMP loop          model → named tools → results → model
Prime loop             model → ipython(code) → kernel (files, shell, rlm(), harness) → model
```

Same TUI family. Different thing the model is allowed to say.

---

## 3. Feature matrix

Uncertain cells are **?**. Counts are from official READMEs on 2026-08-25 and will drift.

| Feature | Pi | OMP | Prime Agent |
|---------|----|-----|-------------|
| **What it is** | Minimal MIT coding harness | Coding-first Pi fork/rewrite | RLM + Continual Harness agent; Pi TUI/session fork |
| **Default loop** | 4 tools: `read` `write` `edit` `bash` | ~31 tools; hashline `edit` + LSP/DAP | 1 tool: persistent `ipython` |
| **Edit model** | Built-in `edit` / `write` (string-replace class) | **Hashline** (content-hash anchors; stale reject/recover). Also `ast_edit`, optional `apply_patch` / `replace` | Python file I/O in the kernel. No dedicated patch language |
| **Code intelligence** | None built-in (extensions) | LSP (14 ops) + DAP debugger (28 ops) | Whatever you import/run in Python (`jedi`, tests, …). No first-party LSP/DAP tool |
| **Subagents** | None built-in (tmux / package / extension) | `task` → isolated worktrees, typed yields, Agent Hub | `await rlm("…")` children; persistent; A2A in family |
| **Memory** | `AGENTS.md`; extensions for long-term memory | `retain` / `recall` / `reflect` / `learn`; backends local, Hindsight, Mnemopi (project-scoped default). Several memory tools off until configured | `rlm.harness` memories + `/refine`. Session-local by default; optional global |
| **Skills** | Agent Skills standard; on-demand `SKILL.md` | Skills + managed skills (`manage_skill` / `learn`); inherits Cursor/Claude/Codex/Cline rule files | Skills as **importable Python packages** plus `SKILL.md`; creator can write new ones |
| **MCP** | **No** (by design). Extension or CLI-tool READMEs instead | Yes. Discovered from `.claude`, `.cursor`, `.mcp.json`, etc. Exposed as `mcp__*` tools | Yes, but **not** extra tools. MCP is a Python module (`import linear`) after `/mcp login` |
| **Providers** | 15+; `/login` **or** API keys. Custom via `models.json` / extensions | 60+ listed; roles; fallback chains; custom `models.yml` | Catalog per release; `/login` **or** keys; `models.json` / extensions |
| **Grok / xAI** | xAI listed as API-key provider. OAuth exists in the Pi ecosystem (`/login xai`, `pi-xai-oauth` package). Built-in SuperGrok as a first-class sibling of Claude/Codex `/login` is less clearly documented than OMP's | **Both:** `XAI_API_KEY` (`xai`) and SuperGrok / X Premium+ OAuth (`xai-oauth`). `XAI_OAUTH_TOKEN` overrides key for OAuth. Default slug documented as `grok-4.6` | **`XAI_API_KEY` only** in official provider docs. SuperGrok OAuth **?** / incomplete (community PR not in the subscription list) |
| **Sandbox / permissions** | No permission popups. Run in a container, or build your own gates | Approval modes: `always-ask` / `write` / **`yolo` (default)**. Per-tool allow/deny/prompt. ACP routes writes through `session/request_permission`. Worktree isolation (`pi-iso`) for subagents. Not a kernel sandbox like Grok Build | **Not a security sandbox** (official). Disposable clone / worktree. `--autonomous` bounds *continuations*, not OS policy |
| **Surfaces** | TUI; `pi -p`; JSON; RPC; SDK | TUI; `omp -p`; JSON; RPC; **ACP** (Zed); SDK; `/collab` browser guest | TUI; `prime-agent -p`; JSON; RPC; SDK; **daemon** attach/detach; Agents View |
| **Headless / eval** | Print / JSON / RPC | Print / JSON / RPC; `--max-time`; `--yolo` | Print / JSON / RPC; `--autonomous` + gates; goals; heartbeats; schedules |
| **Windows** | Documented | First-class (no WSL required; in-process shell/grep) | Installer copy is macOS/Linux; separate Windows docs exist |
| **License** | MIT | MIT | MIT |
| **Maturity (qualitative)** | Influential, small core, extend-it-yourself | Large coding product; many tools, still moving fast | Newer (public launch ~2026-08); research-oriented; vouched contributions |
| **Command** | `pi` | `omp` | `prime-agent` (do not npm-install the inherited `pi` package as the product) |

---

## 4. Pros / cons

### OMP, as a user

**Pros.** You sit down in a repo and the IDE-shaped work is already there: rename through LSP, step a segfault in lldb, hashline edits that fail closed on stale anchors, subagents that do not dump their chain of thought into your window. SuperGrok OAuth works as a documented `/login` path, so a Grok-pinned day does not require minting `XAI_API_KEY` first. Windows is a real target. Headless `omp -p` and ACP mean the same engine can live in a script or in Zed.

**Cons.** It is a lot of harness. Thirty-one tools, ten model roles, magic keywords (`ultrathink`, `orchestrate`), advisor models, collab relays, desktop `computer` control. Default approval is `yolo`. You will spend time turning things *off* (`--tools`, `--no-lsp`, gated memory/github/browser) if you wanted Pi's quiet. Hashline is a new patch dialect the model must hit; when it misses, you are debugging the format, not the bug. First-party "benchmaxxed" tables are marketing until you reproduce them.

### OMP, as eval/research

**Pros.** The Pi → OMP delta is the only *clean* harness experiment in this family: same lineage, same class of loop, independent variable = tools + edit protocol + LSP/DAP. Both expose print/JSON/RPC, so Track A can be headless. Grok can be pinned on the same auth class if you choose `XAI_API_KEY` *or* SuperGrok OAuth on **both** Pi and OMP.

**Cons.** Uncontrolled, you measure hashline (and LSP) rather than "harness IQ." Default `yolo` vs Pi's no-popup-but-minimal-tools is still a permission confound if you do not pin `--approval-mode`. Role routing (`smol` subagents on a cheaper model) will leak if you only pin the parent `/model`. Do not quote OMP's Grok Code Fast 1 lift as a project result.

### Prime Agent, as a user

**Pros.** Long work stays on the machine: daemon, reattach, goals, heartbeats, retained children. Session history can live in Python variables instead of being re-`read` into the prompt. `/refine` is a bounded self-edit (immutable base prompt, rollback by ID), not a vague "the agent remembers." If the day is research, GPU-kernel iteration, or a multi-hour run with `--autonomous-gate "npm run check"`, this is the tool that exposes those knobs.

**Cons.** Daily file editing is Python with your user permissions. There is no hashline, no LSP rename, no DAP stepper as a first-class tool. SuperGrok OAuth is the path you probably wanted and do not officially have. The README's sandbox warning is not legal boilerplate. `/refine` will happily encode a cheat if the reward says so (Prime's own Factorio write-up). Contribution is vouched. The IPython dependency is a real install, not a TUI theme.

### Prime Agent, as eval/research

**Pros.** This is the interesting architecture paper: RLM (prompt-as-variable, programmatic subagents) plus Continual Harness CRUD. `--autonomous` with gates is closer to a protocol than "sit in the TUI until it looks done." Headless JSON/RPC exist. Comparing Prime to Pi *as loops* (REPL vs four-tool) is science. Their blog already treats Pi-mono as the control on some long-context tables.

**Cons.** It is a bad Track A cell. Three confounds at once: (1) different loop, (2) Grok via API key rather than SuperGrok OAuth, (3) still a Pi-family TUI, so a nine-row "Grok-native" table double-counts the skeleton. Vendor ARC-AGI-3 **95.5% RHAE Best@1** with Opus 5, and the long-context table vs Claude Code / Codex / Pi-mono, are **Prime Intellect's numbers** with mixed models. Do not import them into Wave 1. `/refine` during a scored run is an extra independent variable: freeze it or log it.

---

## 5. When you'd pick which

1. **Daily coding in a real repo** (rename, tests, a debugger, PRs as paths). **OMP.** Pi if you want to build that yourself. Prime if you enjoy driving an IPython session more than an edit tool.

2. **Grok-pinned harness eval (Track A).** **Pi and OMP**, same slug, same `auth_class` (`oauth-supergrok` *or* `xai-api-key`, not mixed). Prime only if you are willing to label the row `xai-api-key` and move it to Track C.

3. **Long unattended research / "keep going until the gate is green."** **Prime** (`--autonomous`, goals, heartbeats, daemon). OMP can `--max-time` and yolo, but it was not built as an eval runtime.

4. **Self-improving harness experiments** (does trajectory → small prompt/skill/memory edits help, with rollback?). **Prime** (`/refine`, `rlm.harness`). OMP's `learn` / `retain` is adjacent and worth a *different* study, not the same cell.

5. **Minimal control or embedding** (SDK, OpenClaw-style host, "I will add the one tool I need"). **Pi.** OMP is the opposite of a small schema. Prime's schema is small (`ipython`) but the runtime (kernel, daemon, children) is not.

6. **Semantic refactor or crash-debug where string replace is the failure mode.** **OMP** (LSP + DAP + hashline). Prime can *call* language servers from Python; you are writing that glue. Pi can grow it as a package.

---

## 6. Eval implication (Wave 1 Track A vs Track C)

Read [`waves/wave-1-adversarial-review.md`](../waves/wave-1-adversarial-review.md). No scores here either.

**Track A (Grok-native CLI, hold Grok roughly fixed).** Membership that can defend the thesis: **Grok Build × Pi × OMP**. Pi vs OMP is the clean delta: same loop class, different tooling and edit protocol. Pin `model_slug`, pin `auth_class`, pin `edit_format` (hashline vs Pi `edit`), run headless. If OMP is on SuperGrok `grok-4.6` and Pi is on `XAI_API_KEY` `grok-build-*`, you did not measure the fork.

**Track C (experimental / architectural).** **Prime Agent belongs here**, with FX and IDE-surface rows. The question is *kind of loop* (REPL/RLM + continual state vs four-tool vs Zig-minimal), not "Pi + more tools." A Prime vs Pi write-up should say that in the title. Putting Prime in a Grok-native Track A table adds a third Pi-family SUT while the set still undersamples Grok-capable non-Pi CLIs (OpenCode, Aider, Goose).

**Do not:**

- Publish a single Wave 1 leaderboard that includes both OMP and Prime.
- Treat Prime's vendor ARC-AGI-3 / OOLONG tables as Wave 1 cells.
- Treat OMP's hashline marketing lifts as Wave 1 cells.
- Mix SuperGrok OAuth and `XAI_API_KEY` inside Track A.

**Log if you run them anyway:** `binary_version`, `auth_class`, `model_slug`, `edit_format` (OMP) or `ipython` (Prime), whether `/refine` was on, sandbox/approval mode, argv for `-p` / `--autonomous`.

Publishable Track A remains three SUTs and three tasks. This pair's job is to keep OMP in that triangle and keep Prime in the architecture note.

---

## Sources (official, retrieved 2026-08-25)

- Pi: [pi.dev](https://pi.dev), [earendil-works/pi](https://github.com/earendil-works/pi), [coding-agent README](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md), [Earendil move](https://pi.dev/news/2026/5/7/pi-has-a-new-home)
- OMP: [omp.sh](https://omp.sh), [can1357/oh-my-pi README](https://github.com/can1357/oh-my-pi), [hashline README](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/README.md), [edit tool](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/edit.md), [CLI reference](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md), [approval mode](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [environment variables](https://github.com/can1357/oh-my-pi/blob/main/docs/environment-variables.md)
- Prime: [README](https://github.com/PrimeIntellect-ai/prime-agent), [coding-agent README](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/README.md), [providers.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/providers.md), [rlm.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/rlm.md), [blog](https://www.primeintellect.ai/blog/prime-agent), [xai-oauth discussion #1640](https://github.com/PrimeIntellect-ai/prime-agent/discussions/1640)
- This repo: [`waves/wave-1-adversarial-review.md`](../waves/wave-1-adversarial-review.md), [`landscape/agentic-tools-subscription-vs-byok.md`](../landscape/agentic-tools-subscription-vs-byok.md)

**Not verified here:** live binary versions on any evaluator machine; whether Prime `xai-oauth` has landed since this note; OMP hashline pass rates on a fixture this project owns.
