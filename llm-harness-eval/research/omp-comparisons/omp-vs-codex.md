# OMP versus Codex: a pairwise harness comparison

**Status:** research note (no scores; no runs claimed)
**Date:** 2026-08-25
**Audience:** Bobby, for *understanding* two SUTs before they share an eval table

This note compares **Oh My Pi (OMP)** with **OpenAI Codex as a family of surfaces around one harness**. It is not a comparison with the 2021 Codex *model*, with GPT as a weight file, or with Z.ai ZCode. The question is identity, which independent variables each product actually varies, and what a fair empirical cell would have to pin. It is not a leaderboard.

| Product | Site / repo |
|---------|-------------|
| **OMP (Oh My Pi)** | [omp.sh](https://omp.sh) · [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) · npm [`@oh-my-pi/pi-coding-agent`](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent) |
| **Codex (2025-2026 product)** | [openai/codex](https://github.com/openai/codex) · [developers.openai.com/codex](https://developers.openai.com/codex) · [Codex as a platform](https://developers.openai.com/blog/codex-as-a-platform) · [openai.com/codex](https://openai.com/codex/) |
| **Pi (OMP upstream)** | [pi.dev](https://pi.dev) · [earendil-works/pi](https://github.com/earendil-works/pi) |

Vendor numbers (OMP hashline lifts, OpenAI ARC-AGI-3 compaction, third-party SWE-bench tables) are first-party or secondary claims. They are not this project's results. Star counts are discovery noise.

---

## 1. Identity: family versus single CLI

**Codex is a family.** OpenAI's 2026 framing is explicit. Most people meet Codex through the ChatGPT desktop app, the CLI, or the IDE extension. Those are "only a few of the ways the same underlying system can be used." The reusable part is the **agent loop**: conversation state, tool use, sandbox and approval policy, streaming, and carry-forward across turns. That loop is exposed as `codex` (TUI), `codex exec` (non-interactive), Codex app-server, the official SDK, and Codex cloud at [chatgpt.com/codex](https://chatgpt.com/codex). The GitHub README opens four doors: local CLI, IDE (VS Code / Cursor / Windsurf), `codex app` / desktop, and Codex Web. Treating "Codex CLI" as the whole product is a category error. The CLI is the local, inspectable face of a lab harness that also runs in editors, on the desktop, and in vendor VMs.

The official command is widely installed as **`codex`**. Installers: `chatgpt.com/codex/install.sh`, npm `@openai/codex`, Homebrew cask `codex`, GitHub Releases. Public tags on 2026-08-24 include stable **`rust-v0.149.1`** and later `0.150.0-alpha.8`. An evaluator note that "Codex CLI ~0.149.x was installed on an evaluator box" is **plausible against that release stream**. This pass did not inspect that machine's binary.

**OMP is one coding CLI**, with wrappers. Public binary: `omp`. Package: `@oh-my-pi/pi-coding-agent`. Same engine, four entry points: interactive TUI, `omp -p`, Node SDK, `omp --mode rpc` / `omp acp`. ACP lets Zed drive the agent. `/collab` shares a live session. That is still CLI-first. There is no first-party OMP cloud VM, GitHub review bot, or Slack dispatcher comparable to Codex Web.

**Three collisions to refuse.**

1. **2021 Codex.** The original Codex *model* (code-davinci class, Copilot-era) is a weight lineage. The 2025-2026 product reused the name for an agent family.
2. **GPT the model.** Slugs such as `gpt-5.5`, `gpt-5.4-mini`, `gpt-5.3-codex-spark` are models (some Codex-tuned SKUs). The harness is the loop around them. OpenAI: "The open-source layer is the harness and integration surface; model access and managed services remain separate."
3. **Z.ai ZCode.** Zhipu's ZCode / GLM workstation is a different vendor. OMP lists Z.AI / GLM Coding Plan as a *provider*. That does not make either side of this pair into ZCode.

In this project's taxonomy ([`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md)), OMP is **Track A**: Grok-capable, Pi-lineage batteries. Codex is **Track B**: OpenAI-native baseline, **not** a Grok-native SUT. Pinning Grok is typically not the Codex product.

---

## 2. Method

GitHub and official docs first. Secondary blogs are discovery only. No invented scores. If a SWE-bench or Terminal-Bench figure appears in the wild, treat it as a **model + harness + protocol composite** unless the paper isolates the loop. Two first-party mechanism claims appear below (OMP edit-format lifts, OpenAI ARC-AGI-3 compaction) and are labeled as vendor claims.

---

## 3. Architecture and control loop

Both wrap a model with a coding loop: read the repo, edit, run commands, manage context and permissions, stop.

**OMP still speaks named tools.** It is a coding-first fork/rewrite of Mario Zechner's Pi. Pi's loop is four tools (`read`, `write`, `edit`, `bash`). OMP keeps that class of loop and inflates the schema. The README (2026-08-25) lists **31 built-in tools**, **14 LSP ops**, **28 DAP ops**, **60+ providers**, and about 80k lines of Rust core under a TypeScript agent. Persistent Python and Bun kernels can call back into agent tools. Stream rules can abort mid-token, inject a reminder, and retry. An optional advisor model watches each turn. Magic keywords and slash modes (`/plan`, `/vibe`) reshape a session. The model is still choosing tools, not writing a REPL.

**Codex's loop is the lab's.** OpenAI documents conversation state, streaming, tools, sandbox/approval, and carry-across-turns. The distinctive edit tool is **`apply_patch`**: a freeform, OpenAI-flavored patch language (`*** Begin Patch` ... `*** End Patch`). Can Bölük's [harness-problem post](https://blog.can.ac/2026/02/12/the-harness-problem/) argues that Codex-tuned GPT is likely gateway-biased toward that grammar and that other models fail it at high rates. That is a competitor hypothesis plus OMP's own benchmark, not a result this repo has reproduced. Codex also plans (`/plan`), reviews (`/review`), loads `AGENTS.md` before work, and can spawn subagents when asked. `codex exec` is headless. App-server is embeddable.

OpenAI's platform post reports that on ARC-AGI-3, retained reasoning and context compaction raised GPT-5.6 Sol's score from 13.3% to 38.3% while cutting output tokens sixfold. **Vendor-reported. Composite of model plus compaction policy. Not a Wave 1 number.**

The contrast is not smart versus dumb. It is an **open multi-provider tool schema with hash-anchored edits and IDE protocols** versus a **lab loop co-designed with OpenAI models, OS sandbox, and a family of surfaces**.

---

## 4. Tools and edit protocol

**Edit format is an independent variable.** Dumping it into one success% column crowns a harness for mechanical reasons ([adversarial review](../../waves/wave-1-adversarial-review.md) §2).

OMP's default `edit` is **hashline**: content-hash anchors from the latest `read` / `grep` / successful `edit`. Stale anchors reject or recover instead of writing a wrong hunk into a moved file. `write`, `ast_edit` / `ast_grep`, and optional `apply_patch` / `replace` exist (`PI_EDIT_VARIANT`). OMP's tables claim Grok Code Fast 1 6.7% to 68.3% pass when the format stopped eating the model, Gemini 3 Flash +5 pp over `str_replace`, Grok 4 Fast -61% output tokens, MiniMax 2.1x pass. **Same weights, same prompt, OMP fixture. Not this project's tasks.**

Codex's house format is `apply_patch`. The in-tree prompt tells the model to use that tool only. Safety code still sandboxes the patch when writes might escape writable roots. For GPT-family models gated into that grammar, this is a feature. For a Grok pin, it is a likely confound.

OMP puts IDE work in the box: `lsp` (including `workspace/willRenameFiles`), `debug` (DAP: lldb, dlv, debugpy), in-process grep/glob and embedded bash so Windows does not need WSL, `eval` kernels, `browser`, optional `computer`, `web_search`, GitHub-as-filesystem (`read pr://...`), `omp commit`. Setting-gated tools stay off until enabled. `security_scan` can drive **Codex Security cloud scans**. That is OMP calling a Codex-branded service, not OMP becoming Codex.

Codex's local tool surface is narrower: sandboxed shell, `apply_patch`, web search as a feature flag, MCP for the rest. The bet is that a small enforced set plus a model that already speaks the patch language beats a large schema. Testable. Not tested here.

---

## 5. Context, memory, skills

Codex treats `AGENTS.md` as an open-format README for agents. Discovery walks `~/.codex/AGENTS.md` then repo root down to cwd; closer files win; default cap 32 KiB. OMP **inherits** that file plus Cursor MDC, Cline `.clinerules`, Copilot `applyTo`, Claude, Gemini, Windsurf. No migration script.

Memory is off by default on both. Codex writes `~/.codex/memories/` from idle threads after an explicit enable (stricter in EEA/UK/CH). OMP backends: `local`, `hindsight`, `mnemopi`. Tools: `retain`, `recall`, `reflect`, `learn`. Freeze the backend if you ever score a run that uses it.

Both use `SKILL.md` with progressive disclosure. Codex adds **plugins** (skills + app connectors + MCP) that install across CLI, IDE, and desktop. OMP discovers skills from native dirs, Claude/Codex providers, and `omp plugin install`. Extensibility is not the differentiator. **Distribution across a surface family** is.

---

## 6. Auth and model-pinning

This axis decides whether a head-to-head can be a harness experiment.

**OMP is hybrid, BYOK-first, Grok-native.** Keys and OAuth: Anthropic, OpenAI, **OpenAI Codex oauth**, Gemini, **xAI / SuperGrok**, Copilot, Cursor, OpenRouter, Vercel AI Gateway, plus coding plans. Ten roles (`default`, `smol`, `slow`, `plan`, `advisor`, ...) pin different models to different jobs. You can run GPT *through* Codex auth **inside OMP's loop**. That cell is "OMP plus a Codex-routed model," not "Codex the harness."

**Codex is hybrid, OpenAI-first, not Grok-native.** Local surfaces accept ChatGPT sign-in **or** `codex login --with-api-key`. Cloud **requires** ChatGPT. API key gets local CLI/SDK/IDE at API rates and does **not** get GitHub review, Slack, or other cloud extras. Custom `model_providers` can point at Responses-compatible endpoints. Official docs still say ChatGPT sign-in works best with recommended GPT slugs (`gpt-5.5`, `gpt-5.4-mini`, Pro-only `gpt-5.3-codex-spark`). Cloud task model is not user-defaultable in the docs retrieved here.

**Pinning Grok in Codex is not the product.** Landscape row: Grok-capable? **No.** A custom provider would be a science project, would drop cloud, and would feed Grok an `apply_patch` dialect OMP argues Grok fails. Wave 1 already classified Codex as OpenAI-native. Do not Grok-wash it.

Mixing ChatGPT-plan quota with API-key billing inside one "harness effect" table is the same confound the landscape file already forbids for Claude and Grok Build.

---

## 7. Surfaces

| Surface | OMP | Codex |
|---------|-----|-------|
| CLI / TUI | `omp` (primary) | `codex` (primary local) |
| Headless | `omp -p`, JSON, RPC | `codex exec` |
| Embed | Node SDK; RPC | Official SDK; **app-server** |
| Editor | **ACP** (Zed) | First-party **IDE extension** |
| Desktop | `/collab` browser guest | **ChatGPT desktop app** |
| Cloud | None first-party | **Codex Web**: container, setup script, PR. GitHub review, Slack |
| Mobile | Not a product surface here | iOS / ChatGPT mobile (plan-dependent) |

Codex CLI, IDE, and app share `~/.codex/config.toml` and cached login. OMP is `~/.omp/agent/` plus project `.omp/`. OMP can *read* Codex MCP and `AGENTS.md`. Codex does not claim to ingest OMP config.

If the research question is "local CLI under a pinned model," CLI-versus-CLI is fair. If the question is "what a lab coding agent does in 2026," omitting cloud omits the product.

---

## 8. Extensibility, safety, multi-agent, license, billing

Both speak MCP. Codex: `[mcp_servers]` in `config.toml`, stdio and streamable HTTP with OAuth; the CLI can also *be* an MCP server. OMP discovers `.omp/mcp.json` **and** Claude, Codex, Gemini, OpenCode, Cursor, Windsurf, VS Code configs.

Codex's extra is **platformization**. App-server and SDK let other products own UI, tools, and approvals while Codex owns the loop. Plugins, enterprise RBAC, SAML/SSO, MFA for cloud, `forced_login_method`, access tokens, workload identity.

OMP's extra is **forkability**. MIT. TypeScript extensions use the same tool API as builtins. You can change the edit tool. That is the point of a harness not glued to one lab's model.

**Safety.** Codex: OS sandbox (`read-only` / `workspace-write` default / `danger-full-access`) plus approval (`untrusted` / `on-request` / `never`), reviewer `user` or `auto_review`. Seatbelt on macOS, bubblewrap on Linux/WSL2, native Windows sandbox. Spawned tests inherit the boundary. Cloud secrets are stripped before the agent phase. GPT-5.3-Codex is documented under a High cybersecurity Preparedness treatment; that is **model plus policy**, not the Apache-2.0 CLI alone.

OMP: application-layer approval, default **`yolo`**. Tiers `read` / `write` / `exec`. `bash` can prompt on destructive patterns, but in `yolo` a bare override is ignored unless policy is explicit. `eval` is `exec` and is **not** covered by `bash.patterns`. Subagent worktrees (`pi-iso`) isolate merges; they are not Seatbelt. Uncontrolled, OMP `yolo` versus Codex `workspace-write` + `on-request` is a **sandbox confound**.

**Multi-agent.** OMP `task` fans into isolated worktrees with schema-validated yields and Agent Hub. Codex subagents are **manual** (ask to spawn); docs warn against parallel write-heavy edits. Cloud parallelism is Codex-only.

**License.** OMP: MIT for the product. Codex: Apache-2.0 for the harness; models and managed cloud stay separate. Both harnesses are inspectable. Only OMP's license includes the right to retarget the loop at Grok without a lab's permission. That is why OMP can sit in Track A and Codex cannot.

**Billing.** Canonical map: [`landscape/agentic-tools-subscription-vs-byok.md`](../../landscape/agentic-tools-subscription-vs-byok.md). Codex: ChatGPT plan (local plus, plan-dependent, cloud) **or** API key (local only). OMP binary is free; you pay a provider. Pin `auth_class` per run. No dollar rates here.

**Reproducibility.** Headless exists on both (`omp -p`; `codex exec`). OMP is a BYOK SUT: pin slug, auth, `--tools`, `approvalMode`, edit variant, binary. Pi is the control. Codex is an OpenAI-native system: pin version (public 0.149.x stable family), model, sandbox, approval, ChatGPT versus API key, and **label cloud separately**. Wave 1 ([PR #1](https://github.com/bnivanov/llm-harness-eval/pull/1)) already listed Codex as a cross-lab baseline, not Grok-native. The adversarial review kept the install and killed the Grok-native billing. That still holds.

---

## Where OMP is better

**Grok-fixed harness experiments.** OMP documents SuperGrok OAuth and `XAI_API_KEY`. Roles and fallbacks are first-class. Codex's native path is ChatGPT or API GPT. A same-model pin to Grok is the OMP side of Track A. On Codex it is either impossible as a product or a custom-provider stunt that throws away cloud and `apply_patch` co-design.

**Edit protocol for models that are not OpenAI-gated.** Hashline gives a verifiable line id without reproducing whitespace. OMP's own fixture claims large lifts on Grok-class models that fail `apply_patch`. Even if those numbers do not transfer, the mechanism is the right independent variable for a Pi-versus-OMP cell, and it is a reason not to feed Grok to Codex and call it fair.

**A coding IDE in the terminal.** LSP renames that update barrels, DAP on a real debugger, persistent kernels with tool re-entry, PRs as paths, in-process grep/shell on Windows without WSL. Codex can approximate some of this via MCP and shell. OMP ships it.

**An open product you can retarget.** MIT, 60+ providers, inherit `AGENTS.md` and MCP files already on disk, consume Codex oauth as *one* backend. You are not waiting for a lab to bless a SKU.

**Track A science in this repo.** Pi vs OMP is a clean delta (four-tool versus about 31 tools plus hashline) under a pinned Grok slug. Codex cannot enter that triangle without changing the question.

---

## Where Codex is better

**A family, not a CLI.** One harness, four product doors, shared `config.toml` and login cache. IDE extension, desktop app, and cloud VM are not afterthoughts. OMP's ACP and `/collab` are real. They are not ChatGPT Codex on the web opening a PR from a container.

**A trust model for local autonomy.** OS-enforced sandbox, documented approval matrix, `auto_review`, writable roots, command rules, admin `requirements.toml`. Default is bounded, not `yolo`. Cloud secrets never reach the agent phase.

**A platform other software can embed.** App-server, official SDK, `codex exec`, CLI-as-MCP-server, enterprise tokens. OpenAI's post is selling this: keep your dashboard, own MCP tools and approvals, let Codex run the loop. OMP has a Node SDK and RPC. It is not that platform.

**An OpenAI-native coding stack.** `apply_patch` plus GPT/Codex-tuned models plus ChatGPT-plan credits is a co-designed system. For Track B ("what does a leading lab harness look like with its own model"), Codex is the honest OpenAI row. Skills and plugins that work the same in CLI, IDE, and app are the payoff of the family.

**Async and org workflow.** Cloud environments (`codex-universal`, setup scripts, internet policy), GitHub `@codex` review, Slack, MFA-gated cloud, RBAC. OMP has no equivalent first-party service. `security_scan` even *calls* Codex Security.

**Eval-shaped local automation on OpenAI's ledger.** `codex exec` with explicit sandbox/approval, JSON events, API-key or access-token CI. Pin `0.149.x` and you have a widely installed, versioned binary.

---

## Evidence table

Public pages on **2026-08-25**. Counts drift. Uncertain cells are **?**.

| Axis | OMP | Codex family |
|------|-----|----------------|
| **Identity** | Single CLI (`omp`) + SDK/RPC/ACP | Family: CLI `codex`, IDE, desktop, cloud/web |
| **Lineage** | Fork/rewrite of Pi (MIT) | Lab harness (Apache-2.0) around OpenAI models |
| **Default loop** | ~31 named tools; hashline `edit`; LSP/DAP | Sandboxed shell + `apply_patch`; MCP for extras |
| **Edit protocol** | Hashline (content-hash). Optional `apply_patch` | `apply_patch` (OpenAI-flavored freeform patch) |
| **Code intelligence** | First-party LSP (14) + DAP (28) | Shell/MCP; no first-party LSP/DAP in the CLI README |
| **Context** | Inherits 8 instruction formats including `AGENTS.md` | Layered `AGENTS.md`; 32 KiB default cap |
| **Memory** | Off by default; `local` / Hindsight / mnemopi | Off by default; `~/.codex/memories/` |
| **Skills / MCP** | `SKILL.md`; inherits Codex MCP among others | `SKILL.md`; plugins across surfaces; `[mcp_servers]`; CLI can be an MCP server |
| **Auth** | Keys + many OAuths (SuperGrok, Codex oauth, ...) | ChatGPT **or** API key locally; **ChatGPT required** for cloud |
| **Grok pin** | **Yes** (documented) | **No** as product; custom provider **?** |
| **Surfaces** | TUI, `-p`, RPC, ACP, `/collab` | CLI, exec, IDE, desktop, cloud, iOS (plan) |
| **Sandbox** | Approval modes; default **`yolo`** | OS sandbox; default **`workspace-write`** + `on-request` |
| **Multi-agent** | Built-in `task` / hub / schema yields | On-request subagents; cloud parallel tasks |
| **License** | MIT (whole product) | Apache-2.0 harness; proprietary models + cloud |
| **Billing** | BYOK-first hybrid | Subscription-bundled hybrid; cloud = sub only |
| **Headless** | `omp -p` / JSON / RPC | `codex exec` / SDK / app-server |
| **Public CLI (stable)** | Rolling GitHub/npm (not pinned here) | **0.149.1** tagged 2026-08-24; 0.150 alphas exist |
| **This project's track** | Track A with Pi + Grok Build | Track B baseline, not Grok-native |

---

## Unknowns

- Live `codex --version` on any evaluator laptop. Public tags make ~0.149.x credible. Not verified in this checkout.
- Whether a Codex `model_providers` entry can run a Grok slug with usable `apply_patch` success. Not documented as supported.
- OMP binary version and default model on the same evaluator box.
- Whether OMP's `openai-codex` oauth path matches ChatGPT-plan Codex *models* or only an auth tunnel. Log the slug if that cell is ever run.
- Head-to-head on this project's tasks: **none**. `evaluation-log.md` is empty.
- SWE-bench / Terminal-Bench roundups. Composites. Not imported.
- ACP-in-Zed versus the first-party Codex IDE extension. Not measured.
- Codex cloud versus local CLI as a *surface* experiment (same harness, different computer). Track B footnote, not this pair's main table.

---

## Fair empirical eval still needed

A publishable comparison is not "install both and vibe." Same-model pin **may be impossible**.

Do not put OMP and Codex in one Grok-native ranking. Codex is not Grok-native. OMP's science pair is Pi, not Codex.

**Track A (already specified):** Grok Build vs Pi vs OMP, pinned slug, pinned `auth_class`, three tasks, headless. Codex stays out.

**Track B (honest systems):** Codex as **(Codex harness × default GPT/Codex SKU × auth_class × sandbox_profile)**. Optional ceiling: Claude Code as the other lab. An "OMP on GPT" row measures OMP's loop on an OpenAI model, including hashline versus `apply_patch`. That is interesting. It is not "same model, vary only harness" unless you also run Codex on that exact slug, same reasoning effort, same web-search flag. Even then sandbox and tool schema still differ.

If you try the closest pin anyway, log `binary_version`, `model_slug`, `auth_class`, `edit_format`, `sandbox_profile` / `approvalMode`, surface (`cli-tui` | `exec`/`-p` | `ide` | `cloud`), whether MCP/skills/memory were on, and argv.

Refuse to pool cloud Codex with local `codex exec`. Refuse to pool OMP-yolo with Codex `workspace-write`. Refuse to quote OMP's Grok Code Fast 1 table or OpenAI's ARC-AGI-3 compaction table as this project's result.

The pairwise moral is dull and correct. **OMP is the better open, Grok-pinnable, IDE-wired CLI.** **Codex is the better lab family: sandbox, surfaces, cloud, and a loop co-designed with GPT.** Measuring which "wins at coding" without those labels is how you publish a tier list.

---

## Sources (official, retrieved 2026-08-25)

**OMP:** [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) · [omp.sh](https://omp.sh) · [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md) · [mcp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md) · [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md) · [memory.md](https://github.com/can1357/oh-my-pi/blob/main/docs/memory.md) · [The harness problem](https://blog.can.ac/2026/02/12/the-harness-problem/) (vendor edit-format claims)

**Codex:** [openai/codex](https://github.com/openai/codex) (`rust-v0.149.1`, 2026-08-24) · [developers.openai.com/codex](https://developers.openai.com/codex) · [Codex as a platform](https://developers.openai.com/blog/codex-as-a-platform) · [auth](https://developers.openai.com/codex/auth) · [sandboxing](https://developers.openai.com/codex/sandboxing) · [customization](https://developers.openai.com/codex/concepts/customization) · [AGENTS.md](https://developers.openai.com/codex/guides/agents-md) · [`codex exec`](https://developers.openai.com/codex/noninteractive) · [SDK](https://developers.openai.com/codex/sdk) · [openai.com/codex](https://openai.com/codex/) · in-tree `prompt_with_apply_patch_instructions.md`

**This repo:** [`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md) · [`landscape/agentic-tools-subscription-vs-byok.md`](../../landscape/agentic-tools-subscription-vs-byok.md) · [PR #1 wave doc](https://github.com/bnivanov/llm-harness-eval/blob/cursor/wave-1-grok-native-bb04/waves/wave-1-grok-native.md)

**Not verified here:** live evaluator binaries; Codex custom-provider plus Grok quality; any scored run.
