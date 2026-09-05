# Agentic coding tools — subscription vs BYOK × surface

**Status:** living reference (no scores, no dollar rates)  
**Last verified:** 2026-08-24  
**Audience:** Bobby’s agentic-coding tools map for current + future eval waves

This file answers two questions per tool:

1. **Who pays for inference?** subscription-bundled · BYOK / API-key · hybrid  
2. **Where does the agent loop run?** CLI harness · IDE harness · desktop app · cloud agent · runtime-gateway

It is the **billing/surface** map. Candidate inventory stays in [`possible-harnesses.md`](../possible-harnesses.md). Wave membership stays in [`waves/`](../waves/).

---

## 1. How to read this

### Billing model

| Label | Meaning |
|-------|---------|
| **Subscription-bundled** | Inference is included with a vendor plan (ChatGPT, Claude, Cursor, SuperGrok, Copilot, Devin, …). Usage draws from plan allowance / credits / quota. Overages, if any, are still *on that vendor’s meter* — not “bring your own key.” |
| **BYOK** | Bring your own API keys, OpenRouter, Vercel AI Gateway, or local models. The harness is typically free/OSS; the model provider bills you. |
| **Hybrid** | Both paths exist and are first-class. Example: `codex login` (ChatGPT plan) **or** `codex login --with-api-key` (API rates). |

**On-demand / credits** is *not* a third axis. It is how a subscription vendor meters extra usage after included quota (plan-included → on-demand on the same bill). Do not confuse that with BYOK.

**Do not treat OAuth availability as BYOK.** SuperGrok OAuth, Claude `/login`, and ChatGPT sign-in are **subscription paths**. `XAI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` are **BYOK / API-key** paths. They are different products even when the same CLI binary accepts both.

### Surface

| Surface | Meaning |
|---------|---------|
| **CLI harness** | Terminal / TUI control loop (`grok`, `pi`, `omp`, `codex`, `agent`, …). |
| **IDE harness** | Agent mode inside an editor (Cursor, Copilot Chat/Agent, Cline, Devin Desktop, Kiro, …). |
| **Desktop app** | Standalone app (Claude Desktop, ChatGPT desktop, Goose desktop, OpenCode desktop, …). |
| **Cloud agent** | Vendor-hosted VM / background run that continues after you disconnect (Cursor Cloud Agents, Codex cloud, Devin Cloud, Amp orbs, …). |
| **Runtime-gateway** | Always-on process that routes channels/models/tools; may *orchestrate* harnesses rather than *be* one. |

**Harness** = the agent control loop (tools, context, permissions, stop condition). IDE and CLI are *surfaces* for a harness, not different definitions of “harness.”

Uncertain cells are marked **?** — do not fill them with guesses.

### Two mental-model corrections

- **Devin is not classic BYOK.** Cognition meters Devin (and Devin Desktop) on a **plan quota + on-demand** (self-serve) or **ACU** (enterprise) bill. You do not generally drop an Anthropic/OpenAI/xAI key into Devin and pay the lab directly. See [Plans and Pricing](https://devin.ai/pricing) and [Desktop usage](https://docs.devin.ai/desktop/accounts/usage).
- **OpenClaw is not a pure coding harness.** It is a **self-hosted personal-assistant gateway/runtime** (channels → agent). It can *drive* coding tools; it is not the unit under a native-harness eval unless we explicitly test the gateway. See [docs.openclaw.ai](https://docs.openclaw.ai/) and [openclaw/openclaw](https://github.com/openclaw/openclaw).

---

## 2. Quick matrix

Legend — **Grok-capable?**  
**Yes** = documented Grok / xAI path (OAuth, API, or vendor Grok SKU). **Via BYOK** = model-agnostic; Grok only if you point keys at xAI / OpenRouter / a gateway that lists Grok. **No** = lab-locked away from Grok. **?** = not verified.

| Tool | Surfaces | Billing model | Typical auth | Grok-capable? | Notes |
|------|----------|---------------|--------------|---------------|-------|
| **Grok Build** | CLI (ACP too) | Hybrid | SuperGrok / X Premium+ OAuth (`grok login`) **or** `XAI_API_KEY` | **Yes** (native) | xAI coding CLI/TUI. Session token beats API key. [docs.x.ai/build](https://docs.x.ai/build/overview) |
| **Cursor** (IDE + CLI `agent` + cloud) | IDE · CLI · cloud · web | Hybrid (subscription-first) | Cursor account / plan | **Yes** (Cursor Grok SKU in Models pool) | Agent / CLI / cloud are plan-metered. IDE BYOK is **narrow** (not cloud/CLI). Grok in Cursor ≠ `grok-build` CLI. |
| **Grok Bot** (in Cursor) | IDE chat | Subscription-bundled | Cursor Pro+/Ultra/Teams **or** linked individual SuperGrok Plus/Heavy | **Yes** | Usage grant, not a coding harness. Distinct from Grok Build. [cursor.com/help/grok-bot/plans](https://cursor.com/help/grok-bot/plans) |
| **Claude Code** | CLI · IDE · desktop · cloud/web | Hybrid | Claude plan `/login` **or** `ANTHROPIC_API_KEY` (overrides plan) | No native; **via gateway** if you retarget | Plan usage shared with chat + Cowork. [Anthropic help](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) |
| **Claude Cowork** | Desktop · web/mobile (beta) | Subscription-bundled | Paid Claude plan | No | Knowledge-work agent, **not** a coding harness. Same engine family, different substrate. [anthropic.com/product/claude-cowork](https://www.anthropic.com/product/claude-cowork) |
| **Codex** (CLI / IDE / app / cloud) | CLI · IDE · desktop · cloud | Hybrid (cloud = sub only) | ChatGPT sign-in **or** API key (local surfaces) | No | Cloud requires ChatGPT login. CLI/IDE/app: both paths. [ChatGPT pricing / Codex](https://learn.chatgpt.com/docs/pricing) |
| **GitHub Copilot** | IDE · CLI · cloud | Hybrid | GitHub Copilot plan (AI Credits) **or** CLI BYOK / local | **Via BYOK** (CLI) | Plan path is subscription. CLI BYOK announced 2026-04. [changelog](https://github.blog/changelog/2026-04-07-copilot-cli-now-supports-byok-and-local-models/) |
| **Devin** (+ Desktop) | Cloud · IDE · CLI | Subscription-bundled (quota / ACU) | Cognition / Devin account | **?** / not BYOK | **Not classic BYOK.** Self-serve quota + on-demand; enterprise **ACUs**. Windsurf → Devin Desktop. |
| **Amp** | CLI · cloud (orbs) · web | Hybrid | Amp account; optional linked ChatGPT / SuperGrok; credits; BYOK on some models | **Yes** (linked SuperGrok) | Capability **dial**, not a model pin. [ampcode.com/pricing](https://ampcode.com/pricing) |
| **Antigravity** (`agy`) | CLI · IDE · cloud API | Hybrid | Google account OAuth **or** `GEMINI_API_KEY` (CLI docs) | No | Gemini CLI successor for personal users (~Jun 2026). [Antigravity CLI install](https://www.antigravity.google/docs/cli/install) |
| **Kiro** | IDE · web | Subscription-bundled (credits) | AWS Builder ID / social / IAM IC | No | Amazon path (Q Developer successor narrative). Credits + add-on credits. [kiro.dev/pricing](https://kiro.dev/pricing/) |
| **Pi** | CLI | Hybrid (BYOK-first) | Provider keys **and** lab OAuth (incl. xAI) | **Yes** | Minimal MIT harness; OMP upstream. [pi.dev](https://pi.dev) |
| **OMP / Oh My Pi** | CLI | Hybrid (BYOK-first) | Many API keys **and** OAuth (xAI, Claude, Codex, Copilot, …) | **Yes** | Pi fork + tools/edits. [omp.sh](https://omp.sh) |
| **Hermes Agent** | CLI (personal runtime) | Hybrid (BYOK-first) | SuperGrok OAuth **or** `XAI_API_KEY` (+ other providers) | **Yes** | Memory/skills agent; can **delegate to `grok`**. [Nous xAI OAuth guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/guides/xai-grok-oauth.md) |
| **Prime Agent** | CLI | Hybrid (BYOK-first) | `/login` subscription **or** API key | **Yes** via `XAI_API_KEY`; SuperGrok OAuth **?** | Pi-fork → RLM. Wave 1: Grok often needs API key. |
| **FX** | CLI | Hybrid (gateway) | `fx login` (Vercel) **or** `AI_GATEWAY_API_KEY` | **Via gateway** | Tiny Zig harness glued to Vercel AI Gateway. [fx.sh auth](https://fx.sh/docs/getting-started/authentication.md) |
| **OpenCode** | CLI · desktop · IDE | Hybrid (BYOK-first) | Provider keys **or** OpenCode Zen (pay-as-you-go gateway) | **Via BYOK** | OSS terminal agent. Zen is optional. [opencode.ai/docs](https://opencode.ai/docs) |
| **Cline** | IDE · CLI | Hybrid (BYOK-first) | Provider keys / gateways | **Via BYOK** | Plan/Act VS Code agent; parent of Roo/Kilo lineage. |
| **Roo Code** | IDE · CLI | BYOK (lineage) | Provider keys | **Via BYOK** | **?** product status — archived mid-2026 in several reports; Kilo is the live fork. |
| **Kilo Code** | IDE · CLI | Hybrid (BYOK-first) | Keys / Kilo Gateway; optional managed tier | **Via BYOK** | Cline→Roo→Kilo. |
| **Aider** | CLI | BYOK | Provider API keys | **Via BYOK** | Git-native pair programmer. |
| **Goose** | CLI · desktop | Hybrid (BYOK-first) | `goose configure` keys **or** ACP into Claude/ChatGPT/etc. | **Via BYOK** | AAIF / Linux Foundation. [aaif-goose/goose](https://github.com/aaif-goose/goose) |
| **Continue** | IDE · CLI | BYOK (historical) | Provider keys; Hub was hybrid | **Via BYOK** | **?** — reported Cursor acqui-hire / product wind-down mid-2026; Apache-2.0 code remains. |
| **OpenClaw** | **Runtime-gateway** · CLI/TUI/UI | Hybrid (BYOK-first) | Provider keys; subscription-backed models optional | **Via BYOK** | Personal assistant gateway, **not** a native coding harness. |
| **SWE-agent** | CLI (research) | BYOK | Provider keys | **Via BYOK** | Princeton research harness / SWE-bench. |
| **OpenHands** | CLI · web | BYOK | Provider keys (100+ reported) | **Via BYOK** | All Hands AI; self-hostable. |
| **OpenRouter** | Gateway | Hybrid (credits **or** BYOK keys) | OpenRouter key ± provider keys | **Yes** (catalog) | Inference router, not a harness. |
| **Vercel AI Gateway** | Gateway | Hybrid (Vercel credits **or** BYOK) | Vercel / `AI_GATEWAY_API_KEY` | **Yes** (catalog; xAI listed as partner) | Can rewire many harnesses in one command. |

---

## 3. Subscription-first

These products are sold as **plans**. Some also accept API keys (hybrid); the *default consumer path* is still the subscription.

### Claude Code + Claude Cowork

| | Claude Code | Claude Cowork |
|---|-------------|---------------|
| Job | Software engineering in a repo | Knowledge work (docs, sheets, research, connectors) |
| Surfaces | Terminal, IDE (VS Code / JetBrains), desktop app, web/mobile | Desktop app; web + mobile beta |
| Billing | Paid Claude plans (Pro / Max / Team / Enterprise). Usage **shared** with chat and Cowork. | Same paid plans. Agentic tasks consume the pool faster than chat. |
| API-key fork | If `ANTHROPIC_API_KEY` is set, Code bills **API rates** and **ignores** the plan. | Enterprise can run on Bedrock / Google Cloud / Microsoft Foundry. |

Cowork is **in this landscape so we do not confuse it with Code**. It is not a Wave 1 coding SUT.

Official: [Use Claude Code with Pro or Max](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan), [Claude Code costs](https://code.claude.com/docs/en/costs.md), [Claude Cowork](https://www.anthropic.com/product/claude-cowork).

### Codex — CLI / IDE / App / Cloud

One product family, **two ledgers**:

| Surface | ChatGPT-plan auth | API-key auth |
|---------|-------------------|--------------|
| **Codex CLI** | Yes — plan credits | Yes — API rates; no cloud extras |
| **IDE extension** | Yes | Yes |
| **ChatGPT desktop app** (local) | Yes | Yes (local extra chats) |
| **Codex cloud** (web, GitHub review, Slack, …) | **Required** | **No** |

Treat cloud Codex as subscription-bundled. Treat CLI as hybrid. Do not mix auth classes inside one eval cell.

Official: [ChatGPT / Codex pricing](https://learn.chatgpt.com/docs/pricing).

### Cursor — IDE + CLI (`agent`) + cloud agents

| Surface | Billing | BYOK? |
|---------|---------|-------|
| **IDE Agent** | Cursor plan included + on-demand | Narrow / incomplete. Custom Cursor models are plan-only. |
| **CLI** (`agent` from [cursor.com/docs/cli](https://cursor.com/docs/cli/overview)) | Same Cursor account meters | Staff: **not** BYOK (same reason as cloud). |
| **Cloud Agents** | Plan + VM compute on Cursor’s meter | **No.** Keys are not persisted server-side. [forum](https://forum.cursor.com/t/why-is-byok-not-available-on-cloud-agents/167358) |

**Cursor Grok** is a **Cursor × SpaceXAI SKU** in the Cursor Models pool ([docs](https://cursor.com/docs/models/grok-4-6)). It is not Grok Build, not SuperGrok chat, and not `XAI_API_KEY`.

**Grok Bot** is a Cursor chat teammate. Access: Cursor Pro+ / Ultra / Teams, *or* link **individual** SuperGrok Plus / Heavy ([plans](https://cursor.com/help/grok-bot/plans)). Linking SuperGrok is a **usage grant**, not a Cursor plan change — and not a coding-harness SUT.

This repo is also **operated through Cursor cloud agents** (`DECISIONS.md`). If Cursor is a SUT, declare the experimenter-entanglement.

### Grok Build / SuperGrok / Cursor Grok (do not collapse)

| Name | What it is | Pay path |
|------|------------|----------|
| **Grok Build** (`grok`) | xAI coding harness (TUI / `grok -p` / ACP) | SuperGrok or X Premium+ **OAuth**, or **`XAI_API_KEY`**. [overview](https://docs.x.ai/build/overview), [auth](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/02-authentication.md) |
| **SuperGrok** | Consumer Grok subscription (grok.com / X) | Powers OAuth coding CLIs. **Does not** automatically fund `console.x.ai` API credit. |
| **Cursor Grok** | Grok SKU inside Cursor | Cursor plan pool (and on-demand). |
| **xAI API** | `api.x.ai` pay-per-token | Prepaid console credit. Separate ledger from SuperGrok. |

Grok Build also allows **custom models** via `~/.grok/config.toml` (BYOK-shaped), but the product’s native path is xAI OAuth or `XAI_API_KEY`.

### GitHub Copilot

- **Plan path:** Copilot Free / Pro / Pro+ / Max / Business / Enterprise. Agent, CLI, and cloud agent draw **GitHub AI Credits**. Completions are typically unlimited on paid plans. [plans](https://github.com/features/copilot/plans), [CLI](https://github.com/features/copilot/cli/)
- **BYOK path (CLI):** Own provider or local models; GitHub auth optional. GitHub-native extras (`/delegate`, Code Search, GitHub MCP) need GitHub login. [changelog 2026-04-07](https://github.blog/changelog/2026-04-07-copilot-cli-now-supports-byok-and-local-models/)

### Devin (+ Devin Desktop)

**Subscription / metered product — not BYOK.**

- Self-serve: Free / Pro / Max / Teams with **included quota**; extra usage is **on-demand** (vendor’s API-priced meter), not your lab key. [devin.ai/pricing](https://devin.ai/pricing), [Cognition self-serve note](https://cognition.com/blog/new-self-serve-plans-for-devin)
- Enterprise: **Agent Compute Units (ACUs)** — inference + (for cloud) VM/infra. [Desktop usage](https://docs.devin.ai/desktop/accounts/usage)

Surfaces: Devin Cloud (autonomous engineer), **Devin Desktop** (ex-Windsurf IDE), Devin CLI / local Cascade-class agents — all on the Cognition meter.

### Amp

Hybrid, but **not** “pin Grok and compare harnesses”:

- Amp **subscription** (included agent usage + orb hours) and/or **credits** / unconstrained API-priced usage. [pricing](https://ampcode.com/pricing)
- Link **ChatGPT** or **𝕏 Premium+ / SuperGrok** so those tokens ride the linked plan (Amp says no extra per-token fee for linked-sub usage).
- **BYOK** exists for some models (manual documents Claude Fable BYOK).
- The **Dial** (low / medium / high / ultra) is a **capability preset** that **swaps models**. Linking ChatGPT steers low/medium/high onto OpenAI models; ultra stays on Amp credits. Do not log Amp as Grok-fixed.

### Antigravity / Gemini path

- **Gemini CLI** for personal Google AI Pro/Ultra/free accounts: reported **EOL ~2026-06-18**; remaining path is **Antigravity** (`agy`) plus, for some orgs, Gemini CLI via **API key / enterprise license**.
- Antigravity CLI official install: Google **OAuth** *or* `modelProvider=gemini` + **`GEMINI_API_KEY`**. [install](https://www.antigravity.google/docs/cli/install)
- Gemini **Interactions API** also exposes an Antigravity agent (API-key, pay-as-you-go). [ai.google.dev](https://ai.google.dev/gemini-api/docs/antigravity-agent)

Status is transitional — re-verify the binary before an eval cell. **Not Grok-native.**

### Kiro / Amazon path

- Spec-driven IDE (Amazon Q Developer successor narrative).
- **Credit-metered subscription** (Free credit allotment; paid tiers; add-on credits). [kiro.dev/pricing](https://kiro.dev/pricing/)
- Models routed via **Amazon / Bedrock-class** catalog — **not** a drop-in xAI key. Enterprise billing through AWS is a vendor path, not BYOK.

---

## 4. BYOK / open harnesses

These are **harness-first**. You (or a gateway) supply the model. Several also accept **lab OAuth** (Claude, ChatGPT, SuperGrok, Copilot) — that makes them **hybrid in practice**, BYOK-first in design.

### Pi

Minimal coding agent ([pi.dev](https://pi.dev), [earendil-works/pi](https://github.com/earendil-works/pi)). Four-tool-class loop. Auth: provider keys and lab OAuth (including xAI). **OMP upstream / Track A control.** First-party Vercel AI Gateway provider.

### OMP / Oh My Pi

[omp.sh](https://omp.sh) / [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi). Explicit Pi fork with more tools, hash-anchored edits, LSP/DAP, subagents. Long provider list: API keys **and** OAuth (Anthropic, Codex, xAI/SuperGrok, Copilot, Cursor, Antigravity, …) plus OpenRouter and Vercel AI Gateway. **Track A delta vs Pi — only if model+auth are pinned to Pi.**

### Hermes Agent

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). Personal / self-improving runtime that *also* codes. SuperGrok OAuth (`xai-oauth`, default model documented as `grok-4.6`) **or** `XAI_API_KEY`. **Hermes xAI OAuth and `grok login` (`~/.grok/auth.json`) are separate tokens.** Optional skill: delegate coding to **Grok Build** — nested SUT if left on.

### Prime Agent

[primeintellect-ai/prime-agent](https://github.com/primeintellect-ai/prime-agent). RLM / persistent IPython loop; began as a `pi-mono` fork. `/login` chooses subscription or API-key provider. Wave 1 operating note: **Grok often needs `XAI_API_KEY`**; SuperGrok OAuth may be incomplete. Architecture study, not a third Pi-vs-OMP cell.

### OpenCode

[opencode.ai](https://opencode.ai) — CLI + desktop + IDE. Default: **configure provider API keys**. Optional **OpenCode Zen** = curated pay-as-you-go gateway (not required). Can also consume ChatGPT / Copilot-class backends per community writeups — treat as hybrid if that path is used. Landscape P0 Grok-capable BYOK; Wave 1 “optional next” / Track A waitlist.

### Cline / Roo / Kilo

| | Cline | Roo Code | Kilo Code |
|---|-------|----------|-----------|
| Lineage | Parent | Cline fork | Roo fork / live platform |
| Surfaces | VS Code / JetBrains + CLI | IDE + CLI | VS Code / JetBrains / CLI |
| Billing | BYOK (Teams = governance, still keys in typical reports) | BYOK | BYOK + zero-markup gateway + optional managed |
| Status | Active | **?** archived mid-2026 in multiple reports | Active ([kilo.ai](https://kilo.ai)) |

### Aider

[Aider-AI/aider](https://github.com/Aider-AI/aider). Git-native CLI. **BYOK** (Anthropic / OpenAI / OpenAI-compatible / local). No vendor coding subscription.

### Goose

[aaif-goose/goose](https://github.com/aaif-goose/goose). AAIF (Linux Foundation) local agent: desktop + CLI. **BYOK** across many providers **or** ACP into existing Claude / ChatGPT / Gemini subscriptions. Local models via Ollama.

### FX

[fx.sh](https://fx.sh) / [vercel-labs/fx](https://github.com/vercel-labs/fx). Tiny Zig CLI. Auth is **Vercel session or AI Gateway key** — a gateway client, not a SuperGrok client. Marketing: local models / gateways / direct APIs / subscriptions. Default catalog is whatever the **Vercel team’s AI Gateway** offers (Wave 1 review: in-tree default was not Grok). **Track C**, not Grok-native.

### OpenClaw (runtime / gateway)

[openclaw.ai](https://openclaw.ai) / [docs](https://docs.openclaw.ai/). Self-hosted **Gateway**: messaging channels, tools, companion apps, optional coding-agent backends. MIT, operator-owned. Bring hosted, subscription-backed, gateway, or local models. **Classify as runtime-gateway.** Out of Wave 1 coding-harness scope (and Claw-family forks stay out until a specific fork is justified).

### SWE-agent / OpenHands

Research / autonomous SWE environments. **BYOK.** Useful as eval baselines, not subscription products. [SWE-agent](https://github.com/SWE-agent/SWE-agent), [OpenHands](https://github.com/All-Hands-AI/OpenHands).

---

## 5. Hybrid / special cases

### Pattern: one binary, two ledgers

| Tool | Subscription ledger | API / key ledger |
|------|---------------------|------------------|
| Claude Code | claude.ai plan | `ANTHROPIC_API_KEY` / Console credits |
| Codex CLI/IDE/app | ChatGPT plan credits | `codex login --with-api-key` |
| Grok Build / Hermes / Pi / OMP | SuperGrok / X Premium+ OAuth | `XAI_API_KEY` |
| Copilot CLI | GitHub AI Credits | `COPILOT_PROVIDER_*` / local |
| Amp | Amp plan + linked ChatGPT/SuperGrok | Amp credits / BYOK |
| OpenCode | (optional Zen balance) | Direct provider keys |
| Cursor IDE | Cursor plan | Narrow provider keys (not Agent/cloud/CLI) |

**Eval rule:** pin `auth_class` per run. Mixing OAuth quota with API-key billing inside one “harness effect” table is a confound (see Wave 1 adversarial review).

### Gateways (not harnesses)

| Gateway | Role | How coding tools attach |
|---------|------|-------------------------|
| **OpenRouter** | Multi-provider OpenAI-compatible router | Credits **or** BYOK provider keys. [BYOK docs](https://openrouter.ai/docs/guides/overview/auth/byok) |
| **Vercel AI Gateway** | Router + budgets + coding-agent setup | `vercel ai-gateway coding-agents setup` writes Claude Code, Codex, OpenCode, Pi, Cline, Cursor, Hermes, Kilo, OpenClaw configs. [docs](https://vercel.com/docs/ai-gateway/coding-agents) |

If a SUT is “FX” or “Pi via Gateway,” the **system under test includes the gateway**. Log it.

### Continue

Historically the textbook **IDE BYOK** extension. Mid-2026 reports: **Cursor acqui-hire**, Hub billing disabled, GitHub read-only, community Apache-2.0 leftover. **Do not schedule evals until product status is re-verified.** Pointers: continue.dev homepage/FAQ (primary); secondary news writeups.

---

## 6. Wave 1 mapping

This landscape does **not** claim what is installed on any evaluator machine. It maps **rows → wave docs**.

Wave 1 setup (SUT list, install *concepts*, no scores): [`waves/wave-1-grok-native.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/wave-1-grok-native-bb04/waves/wave-1-grok-native.md) on [PR #1](https://github.com/bnivanov/llm-harness-eval/pull/1) (not necessarily on `main` yet).

Adversarial split (Track A / B / C): [`waves/wave-1-adversarial-review.md`](../waves/wave-1-adversarial-review.md) (merged).

| Landscape row | In PR #1 Wave 1 list? | Adversarial track | Billing takeaway for a Grok-fixed claim |
|---------------|----------------------|-------------------|----------------------------------------|
| **Grok Build** | Yes — Grok-native cluster | **A — keep** | Hybrid auth; pin OAuth *or* API key; label SKU (`grok-build-*` vs `grok-4.6`) |
| **Pi** | Yes — OMP upstream | **A — keep** | BYOK-first; pin same Grok slug+auth as OMP |
| **OMP** | Yes | **A — keep** | Same pin as Pi or the pair is not an experiment |
| **Hermes Agent** | Yes | **C / cut** unless Grok pinned and `grok` delegation **off** | SuperGrok OAuth ≠ “coding harness inclusion” |
| **Prime Agent** | Yes (try) | **C** | API-key Grok; RLM architecture |
| **Cursor Grok** | Yes — IDE | **C-surface** | Cursor plan SKU; different surface; eval-factory conflict |
| **Amp** | Yes — matrix expansion | **B later or cut** | Will not hold Grok (dial + linked ChatGPT) |
| **FX** | Yes — matrix expansion | **C** | Vercel Gateway, not SuperGrok |
| **Codex CLI** | Yes — cross-lab baseline | **B baseline** | OpenAI-native hybrid; **not** Grok-native |
| **OpenCode** | Optional next only | **A waitlist** (ahead of FX/Amp) | BYOK Grok-capable |
| **Claude Code** | Out of Wave 1 | **B ceiling** if Track B is funded | Subscription/API hybrid; never Track A |
| **Cursor CLI `agent`** | Missing (IDE was chosen) | Better-controlled Cursor surface if Cursor must appear | Same Cursor plan as IDE/cloud |
| **OpenClaw** | Out of scope | Stay out | Gateway, not harness |
| **Devin** | Not in Wave 1 | Autonomy track later | Subscription/ACU, not BYOK |

**Publishable Track A (review):** Grok Build × Pi × OMP — pinned slug, pinned `auth_class`, three tasks, headless. Everything else is a different paper.

---

## 7. Maintenance

### How to update this file

1. Change **one row** in the matrix and the matching section bullet. Do not leave them inconsistent.
2. Prefer **official docs language** (linked). Secondary blogs are discovery only.
3. If a cell is not in an official page, mark **?** rather than inferring.
4. Never add personal spend, invoices, or usage screenshots (project law: `DECISIONS.md`).
5. Never add exact dollar rates here. Category only: plan-included / on-demand / BYOK.
6. When Wave membership changes, update **§6** and the wave files — not the other way around.
7. Brand churn to re-check on each pass: Gemini CLI → Antigravity; Windsurf → Devin Desktop; Roo archive; Continue wind-down; Amazon Q → Kiro; Amp dial + linked subs.

### Stamp

| Field | Value |
|-------|--------|
| **Date stamp** | 2026-08-24 |
| **Last verified** | 2026-08-24 (web + official docs listed in §§3–5) |
| **Not verified** | Live binary versions on any personal machine; Roo/Continue current GitHub state beyond secondary reports; Prime Agent SuperGrok OAuth completeness; Copilot IDE BYOK vs CLI-only BYOK |

### Related files

| File | Role vs this map |
|------|------------------|
| [`possible-harnesses.md`](../possible-harnesses.md) | Name inventory + kind tags |
| [`research/llm-coding-harness-landscape-2026-08.md`](../research/llm-coding-harness-landscape-2026-08.md) | Broader 2026 inventory memo |
| [`waves/wave-1-grok-native.md`](https://github.com/bnivanov/llm-harness-eval/blob/cursor/wave-1-grok-native-bb04/waves/wave-1-grok-native.md) | Wave 1 SUT list (PR #1) |
| [`waves/wave-1-adversarial-review.md`](../waves/wave-1-adversarial-review.md) | Track A/B/C split |
| [`DECISIONS.md`](../DECISIONS.md) | Methodology (harness vs model vs runtime) |
