# OMP versus Muse Code: a pairwise harness comparison

**Status:** research note (no scores; no runs claimed)
**Date:** 2026-09-11
**Audience:** Bobby, for *understanding* two SUTs before they share an eval table

This note compares **Oh My Pi (OMP)** with **Meta Muse Code**, the `muse` CLI running Muse Spark. It is not a comparison with the Muse Image / Muse Video media products, with Muse Spark as a weight file, or with Muse Glimmer. The question is identity, which independent variables each product actually varies, and what a fair empirical cell would have to pin. It is not a leaderboard.

| Product | Site / repo |
|---------|-------------|
| **OMP (Oh My Pi)** | [omp.sh](https://omp.sh) · [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) · npm [`@oh-my-pi/pi-coding-agent`](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent) |
| **Muse Code (2026 product)** | [dev.meta.ai/docs/muse-code](https://dev.meta.ai/docs/muse-code) · [launch blog](https://developer.meta.com/ai/resources/blog/build-with-muse-code/) · [Meta Model API](https://dev.meta.ai/docs/overview) |
| **Pi (OMP upstream)** | [pi.dev](https://pi.dev) · [earendil-works/pi](https://github.com/earendil-works/pi) |

Vendor numbers (Meta's Terminal-Bench 2.1 / DeepSWE 1.1 / Meta Internal Coding Bench charts, kernel-optimization case study, OMP hashline lifts) are first-party or secondary claims. They are not this project's results. Star counts are discovery noise.

---

## 1. Identity: one lab CLI versus one open CLI

**Muse Code is one lab CLI.** Meta Superintelligence Labs released it in beta on 2026-08-05 ([research post](https://research.meta.ai/blog/introducing-muse-code-and-muse-spark-1-2)), with expanded access through September 2026. It is Meta's "coding agent for the terminal and CI, built on Muse Spark." The same binary runs two documented ways — interactive `muse` (TUI) and headless `muse exec` — plus machine-facing subcommands (`serve`, `schema`, `trace`, `export`). There is no first-party Muse Code IDE extension, desktop app, or cloud VM documented on [dev.meta.ai](https://dev.meta.ai/docs/muse-code) as of 2026-09-11 (?). The Model API docs point *other* harnesses (OpenCode, Codex, Claude Code) at the same model; they do not describe a Muse Code surface family.

**OMP is one coding CLI**, with wrappers. Public binary: `omp`. Package: `@oh-my-pi/pi-coding-agent`. Same engine, four entry points: interactive TUI, `omp -p`, Node SDK, `omp --mode rpc` / `omp acp`. ACP lets Zed drive the agent. `/collab` shares a live session. That is still CLI-first.

**Four collisions to refuse.**

1. **Muse Image / Muse Video.** A separate Muse-branded media generation line (July 2026). Not this CLI.
2. **Muse Spark the model.** `muse-spark-1.1` / `muse-spark-1.2` / `muse-spark-1.3` are models on Meta Model API. Muse Code is the harness around them. "Muse" alone in a header is a category error.
3. **Muse Glimmer.** Meta's open-weight, Apache-2.0 distilled model you self-host (vLLM / SGLang / llama.cpp / ExecuTorch). A model release, not this CLI. "Spark 1.2 open weights soon" is a vendor statement (?).
4. **Community bridges.** `muse-code-openrouter` (OpenRouter hack), a macOS-OpenAI gateway, `muse-codex`-style projects, AUR/Termux packaging, awesome-lists — none are first-party Meta artifacts.

In this project's taxonomy ([`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md)), OMP is **Track A**: Grok-capable, Pi-lineage batteries. Muse Code is **not in Wave 1**; it is a **Meta-native Track B candidate at most** — model-locked to Muse Spark by default, not Grok-native. Pinning Grok is not the Muse product.

---

## 2. Method

Official docs and the audited installer first ([dev.meta.ai/docs/muse-code](https://dev.meta.ai/docs/muse-code)). Secondary blogs are discovery only. No invented scores. If a Terminal-Bench or DeepSWE figure appears in the wild, treat it as a **model + harness + protocol composite** unless the paper isolates the loop. Vendor mechanism claims (co-training, self-improvement loop) are labeled as vendor claims below.

**Install evidence (this checkout, 2026-09-11).** Muse Code was installed on the evaluator macOS (arm64) box before this note was written, by audited download rather than the documented pipe:

- Installer: `https://dev.meta.ai/install.sh`, downloaded to a temp file and **read before running** (never piped to a shell). SHA-256: `5196d820127a241211c96cf38f0b2e30cff8506a82e9da9508cd5f826632a0ca`. The script audits clean: `set -euo pipefail`; installs the launcher to `${MUSE_INSTALL_DIR:-~/.local/bin}/muse`; fetches `https://api.meta.ai/muse-launcher.sh` with `--proto '=https'` and verifies an advertised `x-content-sha256` header; runs `bash -n` on the launcher before install; `chmod 0755`.
- Launcher (the script the installer executes): also downloaded and read. SHA-256: `21c66e550a71cac2e4af081cc33d10bec81993d0043ec492761fc449e6c440f6`. It honors `MUSE_NO_AUTO_UPDATE=1` — the flag skips both the missing-binary self-heal update and the interval-based update check — resolving the flag as **honored, verified in the audited launcher source**.
- Env flags used: `MUSE_NO_MODIFY_PATH=1` (audited: skips **all** rc-file edits — the installer would otherwise append to `~/.zshrc`, `~/.bashrc`, `~/.bash_profile`/`~/.bash_login`/`~/.profile`, and fish `conf.d`) and `MUSE_NO_AUTO_UPDATE=1` (per the playbook build rule above).
- Binary path: `~/.local/bin/muse` (a ~33 KB launcher shell script) wrapping `~/.local/bin/muse-bin-1.1.1-R2514.1` (Mach-O 64-bit arm64). Release channel `muse-stable`, state `public`. `~/.local/bin` was added to `PATH` per-shell with `export PATH="$HOME/.local/bin:$PATH"` — no rc file was modified.
- Verbatim `muse --version` (run twice; second run identical, no auto-update drift): `Muse Code 1.1.1 (1.1.1-R2514.1)`.
- `muse --help` and `muse exec --help` print full usage with **no auth prompt**. No Meta credential was configured (no sign-in, no `META_API_KEY`), and no `muse exec` / billed run occurred.
- Post-install check: no rc file contains an installer PATH line; the installer's `.muse-updater` / `.muse-install-lock` scratch entries were cleaned up.

---

## 3. Architecture and control loop

Both wrap a model with a coding loop: read the repo, edit, run commands, manage context and permissions, stop.

**Muse Code's loop is the lab's — and co-designed with the model.** Meta's research post states Muse Spark 1.2 was **co-trained with Muse Code**: rejection-sampled harness trajectories and recipe optimizations for goals, compaction, and subagents, plus the Muse Code toolset integrated "to maximize harness compatibility." A self-improvement loop used Muse Spark 1.1 to generate coding environments and instruction-following templates that graded candidate solutions. **Vendor claims about their own training pipeline.** The loop's distinctive structure: a main agent plus **persistent background observer agents** — memory recall, skill recall, goal tracking, and verification — on by default, each making its own model calls, each inserting advisories through a reconciler rather than answering for the main agent. Every run is an **append-only event log** (model calls, tool calls, approvals, edits); the runtime is replay-exact and restart-safe, and `/resume` rebuilds and continues an interrupted turn. `/goal` holds the agent to an objective across turns (progress nudges after ~10 silent model steps, requirement-by-requirement completion check). `/loop` schedules recurring prompts as cron jobs (7-day auto-expiry). `/fork`, `/side`, and a double-`Esc` [rewind](https://dev.meta.ai/docs/muse-code/rewind) branch conversation history without touching workspace files. A [workflows](https://dev.meta.ai/docs/muse-code/workflows) engine and [session messaging](https://dev.meta.ai/docs/muse-code/session-messaging) exist but are **rollout-gated** — and the docs state the current public `aarch64-apple-darwin` package does not include the workflow script engine, so workflows are unavailable on this evaluator's platform.

**OMP still speaks named tools.** It is a coding-first fork/rewrite of Mario Zechner's Pi. Pi's loop is four tools (`read`, `write`, `edit`, `bash`). OMP keeps that class of loop and inflates the schema. The README (2026-08-25) lists **31 built-in tools**, **14 LSP ops**, **28 DAP ops**, **60+ providers**, and about 80k lines of Rust core under a TypeScript agent. Persistent Python and Bun kernels can call back into agent tools. Stream rules can abort mid-token, inject a reminder, and retry. An optional advisor model watches each turn. Magic keywords and slash modes (`/plan`, `/vibe`) reshape a session. The model is still choosing tools, not writing a REPL.

The contrast is not smart versus dumb. It is an **open multi-provider tool schema with hash-anchored edits and IDE protocols** versus a **lab loop co-trained with its own model, event-sourced sessions, and always-on observer agents**.

---

## 4. Tools and edit protocol

**Edit format is an independent variable.** Dumping it into one success% column crowns a harness for mechanical reasons ([adversarial review](../../waves/wave-1-adversarial-review.md) §2).

**Muse Code's edit grammar is not public.** The docs name `write_file` and `edit_file` tools and stage-by-stage shell review, but the edit/patch grammar, tool schemas, and system prompt are closed-binary internals (?). Contrast OMP's default **hashline** `edit`: content-hash anchors from the latest `read` / `grep` / successful `edit`; stale anchors reject or recover instead of writing a wrong hunk into a moved file. OMP's tables claim Grok Code Fast 1 6.7% to 68.3% pass when the format stopped eating the model, Gemini 3 Flash +5 pp over `str_replace`, Grok 4 Fast -61% output tokens, MiniMax 2.1x pass. **Same weights, same prompt, OMP fixture. Not this project's tasks.** Whether a Muse-format-equivalent lift exists for Muse Spark cannot be checked from outside (?).

**What is public on the Muse side** is the configuration surface, not the tool internals: `--model`, `--reasoning-effort` (`none|minimal|low|medium|high|xhigh|max|ultra`, default `high`; the Meta provider rejects `none`), `--provider echo|meta`, `--preset native-basic|miniswe`, `--worktree off|create|existing`, compaction strategies (`summary-preserved-suffix/v1`, `prefix-extension-summary/v1`, `prefix-extension-inventory-summary/v1`) with soft/hard thresholds, `--max-model-steps`, `--max-tool-output-bytes`, `--parallel-tool-calls`, `--approval-mode`, `--approval-judge`, `--sandbox-network`. Skills, hooks, and MCP are first-class extension points (§8).

**Muse has no documented first-party LSP or DAP.** OMP puts IDE work in the box: `lsp` (including `workspace/willRenameFiles`), `debug` (DAP: lldb, dlv, debugpy), in-process grep/glob and embedded bash so Windows does not need WSL, `eval` kernels, `browser`, optional `computer`, `web_search`, GitHub-as-filesystem (`read pr://...`), `omp commit`. Setting-gated tools stay off until enabled. `security_scan` can drive **Codex Security cloud scans**. That is OMP calling a Codex-branded service, not OMP becoming Codex.

---

## 5. Context, memory, skills

**Instruction files.** Muse Code walks project instructions from the workspace root to the `.git` boundary, checking `AGENTS.md`, `CLAUDE.md`, `.agents/AGENTS.md`, and `.claude/CLAUDE.md` at each level; deeper files win; project rules load only after you **trust the workspace** (a first-run trust prompt gates project-local skills, rules, and hooks). OMP **inherits** that file plus Cursor MDC, Cline `.clinerules`, Copilot `applyTo`, Claude, Gemini, Windsurf — no migration script, and no trust gate on reading them.

**Memory.** Muse Code memory is Markdown: a `MEMORY.md` index plus topic files, in three scopes — personal-project (default), committed `<repo>/.agents/memory/` (shared with cloners), and machine-wide. The index injects up to 48 files; **committed memory loads even in untrusted workspaces**, which the docs themselves flag as an injection surface. Memory is on as part of the default observer set (the memory-recall observer). OMP's memory is off by default, backend-selectable (`local`, `hindsight`, `mnemopi`), with `retain` / `recall` / `reflect` / `learn` tools. Freeze the backend if you ever score a run that uses it — on either harness.

**Skills.** Both use `SKILL.md` with progressive disclosure. Muse Code loads skills from four sources: built-in, user (`$XDG_CONFIG_HOME/muse/skills`, `~/.agents/skills`, plus foreign roots `~/.claude/skills` and `$CODEX_HOME/skills` — fallback `~/.codex/skills` — disableable by preference and rollout gate), project (`<repo>/.agents/skills/`, also scanning repo-local `.codex/skills` and `.claude/skills`), and plugin bundles. `muse skills import --from claude|codex` migrates. Built-ins include `/plan` (approval-gated plan), `/grill` (stress-test), `/taste` (design gate). OMP discovers skills from native dirs, Claude/Codex providers, and `omp plugin install`. Extensibility breadth is comparable. The difference is **default-on behavior**: Muse runs four observers over memory and skills whether you asked or not; OMP runs nothing you did not configure.

---

## 6. Auth and model-pinning

This axis decides whether a head-to-head can be a harness experiment.

**OMP is hybrid, BYOK-first, Grok-native.** Keys and OAuth: Anthropic, OpenAI, **OpenAI Codex oauth**, Gemini, **xAI / SuperGrok**, Copilot, Cursor, OpenRouter, Vercel AI Gateway, plus coding plans. Ten roles (`default`, `smol`, `slow`, `plan`, `advisor`, ...) pin different models to different jobs. You can run GPT *through* Codex auth **inside OMP's loop**. That cell is "OMP plus a Codex-routed model," not "Codex the harness."

**Muse Code is hybrid, Meta-first, not Grok-native.** Auth is a Meta credential: browser sign-in **or** `META_API_KEY` (MMA accounts are key-only); key priority is env > stored > browser. `muse login` / `muse logout` / `muse auth set` manage it. Billing is usage-based per token **or** a flat subscription (§8). The default model is `muse-spark-1.2` ([overview](https://dev.meta.ai/docs/muse-code), retrieved 2026-09-11) even though `muse-spark-1.3` is now the Model API's recommended slug — the harness's default lags the API catalog.

**Pinning Grok in Muse Code is not the product.** Landscape row: Grok-capable? **No.** A community OpenRouter bridge exists; it is a science project, not the product. Muse Code's `--provider` accepts `echo|meta` only, and `--base-url` overrides the *Meta* provider base URL — there is no documented non-Meta provider path (?).

**The one-directional same-model fact.** Meta's own [coding-agents guide](https://dev.meta.ai/docs/coding-agents) documents wiring OpenAI-compatible harnesses to Model API at `https://api.meta.ai/v1` (Responses or Chat Completions; Anthropic-format agents via Messages). So a same-model cell **is possible in one direction**: OMP can run `muse-spark-1.2` as a BYOK provider, while Muse Code cannot host OMP's loop or a Grok pin. That cell measures OMP's loop on a Meta model; it is not "same model, vary only harness" unless Muse Code also runs that exact slug — which, on the default config, it does.

---

## 7. Surfaces

| Surface | OMP | Muse Code |
|---------|-----|-----------|
| CLI / TUI | `omp` (primary) | `muse` (primary local) |
| Headless | `omp -p`, JSON, RPC | `muse exec` (`--json`, `--prompt-file`, `--max-model-steps`, `--session-id`) |
| Embed | Node SDK; RPC | `muse serve` (MSP session host over stdio); `muse schema` (wire schema export); first-party SDK **?** |
| Editor | **ACP** (Zed) | None documented (?); community bridges exist, not first-party |
| Desktop | `/collab` browser guest | None documented (?) |
| Cloud | None first-party | None documented for Muse Code (?); Model API is the hosted inference plane, not an agent surface |
| Session tools | `/collab` | `muse export`, `muse trace`, `session-message`, `resume` |

Both are CLI-first. Neither claims the other's cloud apparatus. Muse Code's audit-shaped extras (`trace inspect`, versioned export) are local-surface features, not a surface family.

---

## 8. Extensibility, safety, multi-agent, license, billing

Both speak MCP. Muse Code: `mcp_servers` in `~/.config/muse/settings.json` (which requires `"schema_version": 1`), `transport` `stdio` or `streamable_http`, `mode` `required|optional` — a required server failing to start aborts the whole run. **MCP tools are not sandboxed**, per the docs' own warning. OMP discovers `.omp/mcp.json` **and** Claude, Codex, Gemini, OpenCode, Cursor, Windsurf, VS Code configs.

Muse Code's second escape surface is **hooks**: 13 lifecycle events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreLLMCall`, `PostLLMCall`, `PreCompact`, `PostCompact`, `SubagentStart`, `SubagentStop`, `Stop`, `SessionEnd`) from project `.muse/hooks.json`, user settings, or a `managed_hooks_path`. **Hooks run outside the sandbox** — the docs' warning again, hardened only by a cleared environment and a small allowlist. OMP's extra is **forkability**: MIT, TypeScript extensions using the same tool API as builtins. You can change the edit tool. That is the point of a harness not glued to one lab's model.

**Safety.** Muse Code: approval and sandbox **on by default**. Approval modes `on-request` (default) / `untrusted` / `never`, with an **LLM approval judge** reviewing prompt-bound calls automatically (on by default). Shell commands are reviewed **stage by stage** — a compound command is parsed into ordered stages and blocks on the first unapprovable one; `rm -rf`-class stages hold while read-only prefixes pass; rejecting one stage runs nothing. Trust scopes: allow-once / workspace-prefix rule / reject; deny overrides allow; interpreter prefixes (`python`, `bash`, `node`) cannot be broad allow rules. The sandbox is OS-enforced — **Seatbelt on macOS, a bundled bubblewrap helper on Linux** — with workspace + temp writable and `.git`, `.muse`, `.agents` read-only inside the workspace; it refuses to run when it cannot enforce the boundary (a Linux host without working bubblewrap fails every shell command). Network: `--sandbox-network proxy-only` (default; per-destination approval) / `restricted` / `enabled`. `--yolo` disables both layers and trusts the workspace; `--disable-approval` keeps the sandbox; `--disable-sandbox` also removes file-tool confinement and forces full egress. Git posture is conservative by default: no commit/push unless asked, incidental edits reverted. OMP: application-layer approval, default **`yolo`**. Tiers `read` / `write` / `exec`. `bash` can prompt on destructive patterns, but in `yolo` a bare override is ignored unless policy is explicit. `eval` is `exec` and is **not** covered by `bash.patterns`. Subagent worktrees (`pi-iso`) isolate merges; they are not Seatbelt. Uncontrolled, OMP `yolo` versus Muse `on-request` + sandbox is the same **sandbox confound** the Codex paper flags — label it, never silently equalize it.

**Multi-agent.** Muse Code: subagent trees with default execution capacity **8** (1–64 via `agents.execution_capacity`; an unconfigured `ultra` root uses 64), children sharing the lead's checkout **unless worktree isolation is requested per child** — and a rejected isolation request never silently falls back to shared placement. Cancellation is cooperative (a mid-write child finishes its write). Every spawn, status change, and control action is journaled. A child commits only when its task asks. On top of that: the four always-on observers, and the rollout-gated workflows engine (up to 1,000 child tasks per workflow lifetime, active children CPU-derived and capped at 16, saved JavaScript workflows in `.agents/workflows/`, `resumeFromRunId` recovery). OMP `task` fans into isolated worktrees with schema-validated yields and Agent Hub — delegation is opt-in per job, not ambient.

**License.** OMP: MIT for the product. Muse Code: proprietary, closed binary; **no public first-party source repository was found as of 2026-09-11** (GitHub search returned only community projects: `muse-code-openrouter`, an ACP plugin, a Codex gateway, AUR/Termux packaging, awesome-lists). Meta's docs do not state a license (?). Only OMP's license includes the right to retarget the loop at Grok without a lab's permission. That is why OMP can sit in Track A and Muse Code cannot.

**Billing.** Canonical map: [`landscape/agentic-tools-subscription-vs-byok.md`](../../landscape/agentic-tools-subscription-vs-byok.md). Muse Code: **Meta-only hybrid** — pay-as-you-go per token with a Meta Model API key, **or** a flat monthly subscription (tiers named Everyday Usage / High Usage / Power Usage on the [subscriptions page](https://dev.meta.ai/docs/muse-code/subscriptions); the subscription applies only to the CLI's auto-connected key; extra API keys bill pay-as-you-go). At the Model API level, Standard-tier models are priced normally and a discounted Contributor variant (`muse-spark-1.2-contributor`) trades lower price for permission to train on your prompts and completions — a **per-token tier distinction, not a subscription tier**. No dollar rates here, per repo law. OMP binary is free; you pay a provider. Pin `auth_class` per run; never mix Muse-subscription quota with `META_API_KEY` runs in one table.

**Reproducibility.** Headless exists on both (`omp -p`; `muse exec`). Muse Code's exit codes are documented with an important caveat: `0` means *the turn completed*, not that the work is correct — an agent can finish and report failing tests, exiting `0`. Gate on your own test command. `muse export --session <uuid> --out run.json` embeds the CLI version; `--no-session-log` forfeits resume, export, and peer messaging. OMP is a BYOK SUT: pin slug, auth, `--tools`, `approvalMode`, edit variant, binary. Muse Code is a Meta-native system: pin version (`1.1.1-R2514.1` on this box), model, approval mode, sandbox/network profile, auth class, and the rollout-gate state of workflows/session-messaging. Wave 1 has not listed Muse Code; this note adds no membership.

---

## Where OMP is better

**Grok-fixed harness experiments.** OMP documents SuperGrok OAuth and `XAI_API_KEY`. Roles and fallbacks are first-class. Muse Code's native path is a Meta credential only; `--provider echo|meta` is the whole menu. A same-model pin to Grok is the OMP side of Track A. On Muse Code it is not a product path at all.

**An edit protocol you can inspect and swap.** Hashline is a documented, controllable variable — OMP publishes the format, the variant switch (`PI_EDIT_VARIANT`), and per-model lift tables. Muse Code's edit grammar is closed-binary internals (?). You cannot hold "edit format" constant across the pair, or even name Muse's format.

**A coding IDE in the terminal.** LSP renames that update barrels, DAP on a real debugger, persistent kernels with tool re-entry, PRs as paths, in-process grep/shell on Windows without WSL. Muse Code has no documented first-party LSP/DAP (?); its shell tool is sandboxed and its extension surfaces are hooks/MCP.

**An open product you can retarget.** MIT, 60+ providers, inherit `AGENTS.md` and MCP files already on disk, consume Codex oauth as *one* backend. Muse Code's source is not published (?), so the loop cannot be read, forked, or re-pointed at another lab's model.

**The only direction a same-model pair exists.** OMP can run `muse-spark-1.2` via Model API BYOK. Muse Code cannot run Grok, or OMP's loop. Any "harness effect" claim between these two is one-directional by construction.

---

## Where Muse Code is better

**A lab co-design claim.** Meta states the model was co-trained with the harness — rejection-sampled trajectories, recipe optimizations for goals/compaction/subagents, the Muse Code toolset in the training loop. **Vendor claim about their pipeline.** If true even partly, the harness-model fit is not reproducible by bolting a model onto a generic loop, and it is the strongest argument for a Track B Meta-native cell.

**Safety-first defaults.** Approval + OS sandbox on from the first run, staged shell review, scoped trust with deny-overrides-allow, read-only `.git`/`.muse`/`.agents` inside the sandbox, network proxy-only with per-destination approval, conservative git posture. OMP's default is `yolo`. For a "what does a leading lab harness look like" row, Muse's default posture is the honest Meta answer.

**Multi-agent by default, with a verification observer.** Four background observers always on — including one whose only job is checking the agent ran the work it claims — plus journaled subagent trees with per-child worktree isolation that refuses to silently fall back. OMP's `task` is powerful but opt-in and unobserved.

**Auditable by construction.** Append-only event log of every model call, tool call, approval, and edit; replay-exact resume; `muse export` embedding the CLI version; `muse trace inspect`. A crashed run resumes precisely; a resumed destructive step is flagged unknown-outcome and the agent is told to verify state first.

**Skills interop as a product feature.** Discovers `~/.claude/skills` and `$CODEX_HOME/skills` by default and ships `muse skills import --from claude|codex`. OMP reads foreign MCP configs; Muse migrates foreign *skills*.

**CI-shaped headless with documented semantics.** `muse exec` with `--json` JSONL events, `--prompt-file`, `--max-model-steps` step caps, `--session-id` resume, documented exit-code meaning (turn-completion, not correctness — explicitly telling you to gate on your own tests), sandbox requirements stated for CI runners, and a refusal to run against a mismatched workspace without `--allow-workspace-switch`.

---

## Evidence table

Public pages on **2026-09-11**; live binary on the evaluator box same day. Counts drift. Uncertain cells are **?**.

| Axis | OMP | Muse Code |
|------|-----|-----------|
| **Identity** | Single CLI (`omp`) + SDK/RPC/ACP | One lab CLI: `muse` TUI + `muse exec` + machine subcommands |
| **Lineage** | Fork/rewrite of Pi (MIT) | Lab harness (Meta Superintelligence Labs; beta 2026-08-05) around Muse Spark |
| **Default loop** | ~31 named tools; hashline `edit`; LSP/DAP | Main agent + 4 always-on observers; event-sourced sessions; closed tool internals (?) |
| **Edit protocol** | Hashline (content-hash). Optional `apply_patch` | **?** — `write_file` / `edit_file` named; grammar closed |
| **Code intelligence** | First-party LSP (14) + DAP (28) | None documented first-party (?) |
| **Context** | Inherits 8 instruction formats including `AGENTS.md` | `AGENTS.md`/`CLAUDE.md` walk to `.git` boundary; trust-gated project rules |
| **Memory** | Off by default; `local` / Hindsight / mnemopi | Markdown memory, 3 scopes, 48-file index; memory-recall observer on by default |
| **Skills / MCP** | `SKILL.md`; plugin marketplace; discovers many MCP configs | `SKILL.md`; 4 sources incl. foreign roots + `import --from claude\|codex`; `mcp_servers` required/optional |
| **Auth** | Keys + many OAuths (SuperGrok, Codex oauth, ...) | Meta browser sign-in **or** `META_API_KEY` (MMA key-only) |
| **Grok pin** | **Yes** (documented) | **No** as product; community bridge **?** |
| **Surfaces** | TUI, `-p`, RPC, ACP, `/collab` | `muse`, `muse exec`, `serve`/`schema`/`trace`/`export`; no IDE/desktop/cloud documented (?) |
| **Sandbox** | Approval modes; default **`yolo`** | OS sandbox (Seatbelt / bubblewrap) + approval, **on by default**; staged shell review; network proxy-only |
| **Multi-agent** | Built-in `task` / hub / schema yields | Subagent trees (capacity 8 default), per-child worktree isolation, journaling, observers; workflows rollout-gated |
| **License** | MIT (whole product) | Proprietary; no first-party source repo found 2026-09-11 (?) |
| **Billing** | BYOK-first hybrid | Meta-only hybrid: usage-based key **or** subscription (Everyday/High/Power Usage) |
| **Headless** | `omp -p` / JSON / RPC | `muse exec` / JSONL / `--session-id` resume / versioned export |
| **Public CLI (installed here)** | Rolling GitHub/npm (not pinned here) | **Muse Code 1.1.1 (1.1.1-R2514.1)**, `muse-stable`, installed 2026-09-11 |
| **This project's track** | Track A with Pi + Grok Build | Not in Wave 1; **Track B candidate** (Meta-native), not Grok-native |

---

## Unknowns

- Muse Code edit/patch grammar, tool schemas, and system prompt. Closed binary; not documented.
- Whether a first-party Muse Code SDK, IDE extension, desktop app, or cloud surface exists beyond the CLI. Nothing on dev.meta.ai as of 2026-09-11 (?); secondary "SDK developer preview" claims unconfirmed (?).
- Whether Muse Code accepts any non-Meta provider. `--provider echo|meta` and a Meta-only `--base-url` override say no; no official statement found (?).
- Subscription terms beyond tier names (Everyday / High / Power Usage): regional availability, exact prompt allowances, overage behavior. Not verified here (?).
- Telemetry defaults and what the `.muse-update-checked-at` / release-manifest channel phones home. Not audited beyond the launcher script.
- Workflow and session-messaging availability on other builds/platforms — both are rollout-gated, and workflows are absent from the current `aarch64-apple-darwin` package this note installed.
- Muse Spark 1.3 in Muse Code: the Model API recommends 1.3, the harness default is 1.2. Whether/when the CLI default moves is unstated (?).
- "Spark 1.2 open weights soon": vendor statement (?).
- Head-to-head on this project's tasks: **none**. `evaluation-log.md` is untouched by this note.
- Versions on other evaluator boxes; this note records one arm64 macOS install on 2026-09-11.

---

## Fair empirical eval still needed

A publishable comparison is not "install both and vibe." Same-model pin **is possible in one direction only**.

Do not put OMP and Muse Code in one Grok-native ranking. Muse Code is not Grok-native. OMP's science pair is Pi, not Muse Code.

**Track A (already specified):** Grok Build vs Pi vs OMP, pinned slug, pinned `auth_class`, three tasks, headless. Muse Code stays out.

**Track B (honest systems), Meta-native cell:** Muse Code as **(Muse Code harness × `muse-spark-1.2` × auth_class × sandbox/approval profile)**. The one same-model pair available: **OMP on `muse-spark-1.2` via Model API BYOK** (`https://api.meta.ai/v1`, Responses surface for reasoning replay) versus **Muse-native on its default slug** — with `auth_class=META_API_KEY` usage-based on **both** sides. Never mix Muse-subscription quota with API-key runs. Never pool Contributor-tier (trains-on-your-data) with Standard-tier usage in one cell: that is a pricing *and* a data-usage variable, not just a discount.

Pin and log per run: `binary_version`, `model_slug`, `auth_class`, `edit_format` (`?` on the Muse side — report as harness-intrinsic, do not invent a name), `sandbox_profile` / approval mode (Muse default sandbox+approvals vs OMP `yolo` — label the confound, never silently equalize), surface (`cli-tui` | `exec`/`-p`), whether MCP/skills/memory/observers were on (Muse's four observers are on unless disabled — disabling them is itself a config you must log), and argv.

Refuse to pool `muse exec` exit 0 with task success — the docs say exit 0 means the turn completed, not that the work is correct. Refuse to quote Meta's Terminal-Bench 2.1 / DeepSWE 1.1 / kernel-optimization charts, or OMP's Grok Code Fast 1 table, as this project's result.

The pairwise moral is dull and correct. **OMP is the better open, Grok-pinnable, IDE-wired CLI — and the only side of this pair that can host the other's model.** **Muse Code is the better lab system: a loop co-trained with its model, safety-first defaults, ambient multi-agent with verification, and an audit trail you can replay.** Measuring which "wins at coding" without those labels is how you publish a tier list.

---

## Sources (official, retrieved 2026-09-11)

**Muse Code / Meta:** [Muse Code overview](https://dev.meta.ai/docs/muse-code) · [permissions and safety](https://dev.meta.ai/docs/muse-code/permissions) · [working with the agent](https://dev.meta.ai/docs/muse-code/interactive) · [rewind](https://dev.meta.ai/docs/muse-code/rewind) · [workflows](https://dev.meta.ai/docs/muse-code/workflows) · [session messaging](https://dev.meta.ai/docs/muse-code/session-messaging) · [subscriptions](https://dev.meta.ai/docs/muse-code/subscriptions) · [extending and automating](https://dev.meta.ai/docs/muse-code/extending) · [authentication and billing](https://dev.meta.ai/docs/muse-code/auth) · [configuration and context](https://dev.meta.ai/docs/muse-code/configuration) · [install script](https://dev.meta.ai/install.sh) (audited) · [launcher](https://api.meta.ai/muse-launcher.sh) (audited) · [Model API overview](https://dev.meta.ai/docs/overview) · [models](https://dev.meta.ai/docs/models) · [coding agents guide](https://dev.meta.ai/docs/coding-agents) · [launch blog](https://developer.meta.com/ai/resources/blog/build-with-muse-code/) · [research post](https://research.meta.ai/blog/introducing-muse-code-and-muse-spark-1-2) (vendor claims: co-training, self-improvement loop, benchmark charts)

**OMP:** [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) · [omp.sh](https://omp.sh) · [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md) · [mcp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md) · [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md) · [memory.md](https://github.com/can1357/oh-my-pi/blob/main/docs/memory.md) · [The harness problem](https://blog.can.ac/2026/02/12/the-harness-problem/) (vendor edit-format claims)

**This repo:** [`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md) · [`landscape/agentic-tools-subscription-vs-byok.md`](../../landscape/agentic-tools-subscription-vs-byok.md) · [`research/omp-comparisons/omp-vs-codex.md`](omp-vs-codex.md) (template for this note)

**Secondary, discovery only:** VentureBeat and SitePoint launch coverage (license claims conflict — official docs silent, no first-party repo found; treated as ?), third-party benchmark roundups quoting DeepSWE 59.3% for Muse Spark 1.2 (vendor number, not verified in the research post text, never a project result).

**Not verified here:** live billed runs of either harness; Muse Code on non-arm64 platforms; subscription checkout flow; any scored run.
