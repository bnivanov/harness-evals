# Wave 1 adversarial review — harness selection

**Status:** review (no scores; no runs claimed)  
**Date:** 2026-08-24  
**Target:** [PR #1](https://github.com/bnivanov/llm-harness-eval/pull/1) (`cursor/wave-1-grok-native-bb04`) and `waves/wave-1-grok-native.md`  
**Reviewed against:** `BRIEF.md`, `DECISIONS.md`, `STATUS.md`, `LEARNINGS.md`, `evaluation-log.md`, `possible-harnesses.md`, `research/llm-coding-harness-landscape-2026-08.md`

This is an attack on the **SUT set and implied causal story**, not on install notes or the (correct) refusal to invent scores. Wave 1 is still `setup`. That is the only thing currently honest about it.

---

## Verdict (read this first)

**Split the wave. Do not publish a nine-row “Grok-native harness” table.**

The original thesis — *hold Grok roughly fixed, vary harness, measure harness effect* — is still the only claim this project can defend (`BRIEF.md` research question 1; `DECISIONS.md` “Wave 1 is a Grok-model-driven harness comparison”). The current SUT list does not test that claim. It tests “which loud 2026 agents did Bobby install,” then papers over the mismatch with a subtitle (“plus matrix expansion”) and a filename that still says `grok-native`.

| Track | Question | Wave 1 membership |
|-------|----------|-------------------|
| **A — Grok-native CLI** | Same Grok family, different coding loop | **Keep:** Grok Build, Pi, OMP. **Maybe:** Hermes *only* as a coding loop with Grok pinned and Grok-Build delegation **disabled**. |
| **B — Cross-lab native stacks** | Lab-locked harness × default model (honest systems, not harness-only) | **Keep as baseline, not Grok-native:** Codex CLI. **Add if Track B is real:** Claude Code (ceiling, not Grok). Amp belongs here *or nowhere*. |
| **C — Experimental / architectural** | Different *kind* of loop (minimal Zig, RLM/REPL, IDE surface) | **Demote from Wave 1 core:** FX, Prime Agent, Cursor Grok. |

**Cut from any table titled Grok-native:** Amp, FX, Codex. They are already labeled “not Grok-only” in `waves/wave-1-grok-native.md`. Keeping them in Wave 1 anyway is how kitchen-sink sets get published.

**Do not run scored Wave 1 until a protocol exists.** The wave doc’s own checklist is empty. Nine SUTs × zero tasks is a blog ranking with extra YAML.

---

## 1. Thesis mismatch

### What the project said it was doing

- `BRIEF.md`: evaluate **harness** performance, not models. RQ1: *“Holding the model fixed (or controlling for it), how much does harness choice change…”*
- `DECISIONS.md` (2026-08-24): *“Wave 1 is a Grok-model-driven harness comparison”* — Grok held roughly fixed; Amp / FX / Codex added because installs were requested; *“claiming they are Grok-fixed would confound the original control.”*
- `waves/wave-1-grok-native.md`: *“The original Wave 1 question remains: same Grok, different harness — what changes?”*

### What the set actually is

Nine SUTs, three auth economies, at least four model identities, two surfaces (IDE vs CLI), three products that are **Pi-lineage forks of the same skeleton**, one personal runtime that can **wrap another SUT**, one capability-dial product that **refuses to pin a model**, one Zig research binary whose tree defaults off Grok, and one OpenAI-native lab CLI.

That is not a Grok-native harness comparison. It is a 2026 agent zoo with a Grok-colored subtitle.

The PR title itself records the drift: it was renamed from *“Wave 1: Grok-native harness evaluation (setup, no results)”* to *“Wave 1: Grok-native harness eval + Amp/FX/Codex matrix (setup)”*. The wave filename did not get renamed. Readers who stop at `waves/wave-1-grok-native.md` will treat Amp/FX/Codex as part of the Grok-fixed contrast. The prose says “do not collapse expansion SUTs into the Grok-fixed contrast.” The **set membership** already did.

Calling the extra three a “matrix expansion” does not save the thesis. A matrix is `harness × model` with cells you can actually fill. This is a union of incompatible designs stuffed into one wave header in `evaluation-log.md`.

### The self-contradiction in DECISIONS

Same day, same file:

1. **Separate harness vs model vs runtime** — do not mix “which model,” “which loop,” and “which multi-agent bus.”
2. **Wave 1 includes** Hermes (Nous personal runtime / self-improving agent; landscape memo tags it *Personal runtime / CLI*), Amp (a **routing product**; modes are capability presets, not model pins), FX (Vercel AI Gateway as the real inference path), Codex (lab-locked model), Cursor Grok (IDE + Cursor-trained Grok SKU), Prime Agent (RLM / continual harness; “not a security sandbox”).

Decision (1) is correct. Decision (2) violates it in four places at once.

`LEARNINGS.md` already knew this before Wave 1 froze: *“serious coding setups often compose harnesses… rather than pick a single winner”* and *“Hermes as learning / memory-oriented; Amp as distributed/remote operator.”* Then Wave 1 put both in the same scored-wave header as Grok Build.

---

## 2. Confounds — what breaks a causal “harness effect” claim

If Wave 1 publishes one ranking, every row below is an alternative explanation for the “winner.”

| Confound | Where it hits | Why it kills the claim |
|----------|---------------|------------------------|
| **Model identity** | Grok Build vs everyone else vs Cursor vs Amp/FX/Codex | Grok Build is widely described as routing agent work through **`grok-build-0.1`** (coding-tuned, smaller context). Pi / Hermes xAI OAuth default **`grok-4.6`**. Cursor “Grok” is **not** that: Cursor documents Grok 4.5 as a **joint Cursor × SpaceXAI** SKU with continued training on Cursor data, and currently steers users toward Grok 4.6. Amp modes swap **GPT-5.6 Sol / Claude Fable / GLM** by subscription. FX’s gateway builtins default **`zai/glm-5.2`**. Codex is OpenAI-native. “Hold Grok roughly fixed” is already false **inside the Grok-native cluster**, before Amp/FX/Codex are added. |
| **Auth path** | Prime Agent, Hermes, Grok Build, Pi/OMP, FX, Codex, Amp | SuperGrok / X Premium+ **OAuth** vs **`XAI_API_KEY`** vs Vercel **AI Gateway** vs Amp account vs ChatGPT-plan Codex. Quota, rate limits, tool entitlement (`x_search`, Grok-native tools), and available SKUs differ by path. Wave 1 already admits Prime “often needs `XAI_API_KEY`” and “SuperGrok OAuth may be incomplete.” That is not a footnote; it is a different product. Hermes docs: Hermes xAI OAuth and `grok login` (`~/.grok/auth.json`) are **separate tokens**. |
| **IDE vs CLI vs cloud** | Cursor Grok vs all CLIs | Different tool surface, permission UX, context construction, and (for this repo) **Cursor cloud agents are also the development path** (`DECISIONS.md`). Evaluating “Cursor Grok” as a SUT while Cursor cloud agents write the eval is experimenter entanglement. At minimum it is a **surface** comparison, not a harness-with-model-fixed comparison. |
| **Sandbox / permission policy** | Grok Build, Codex, Amp, Prime, FX | Grok Build ships kernel-enforced sandbox profiles (Landlock/Seatbelt narratives). Codex’s whole brand is sandbox + `apply_patch`. Prime Agent’s own README: **not a security sandbox** — use disposable clones. Amp has `--dangerously-allow-all` and workspace-write sandbox flags. Permission friction changes “did the agent finish” independently of loop quality. Uncontrolled = confounded. |
| **Edit format** | OMP vs Codex vs Grok Build vs Pi | OMP markets **hash-anchored / hashline** edits as the reliability bet. Codex is an **`apply_patch`** culture. Pi is the **four-tool** minimal loop (read / write / edit / bash class). Grok Build has its own tool crate. If patches fail, you are measuring **edit protocol**, not “harness IQ.” That is worth measuring — but only if you log the format and do not dump it into a single success% column. |
| **Tool richness / loop architecture** | Pi vs OMP vs Prime vs Hermes vs Grok Build | Pi ≈ 4 tools. OMP ≈ 32 tools + LSP + DAP + subagents + persistent kernels. Prime Agent inverts the schema: **one tool** (persistent IPython), subagents as `rlm()` calls, continual self-edits to harness state. Hermes is memory/skills/self-improvement, and can **delegate to `grok`**. Grok Build bets on **parallel subagents / arena**. These are different independent variables. You cannot attribute a delta to “harness” without saying *which mechanism* moved. |
| **Nested SUT** | Hermes vs Grok Build | Hermes user-guide skill: *delegate coding to Grok Build CLI*. If a Hermes run shells out to `grok -p`, Wave 1 is scoring Grok Build twice and calling one of them Hermes. Ban that configuration or drop Hermes from Track A. |
| **Gateway / router** | FX, Amp, optional Vercel path on Pi/OMP/Prime | FX is a harness **and** a Vercel AI Gateway client. Gateway retries, model catalog, and billing are part of the system. Amp’s “dial” is **explicitly** not a model selector. Recording “native routing” in the eval log (as the wave doc asks) is necessary and **insufficient** if the published table still has one column named “harness.” |
| **Default-model gravity** | Every SUT without a pin | Interactive `/model` pickers plus “install requested 2026-08-24” is how you get whatever the binary defaulted to that week. Wave 1 has **no pin**. |

`research/llm-coding-harness-landscape-2026-08.md` already warned: *“Harness × model pairing dominates outcomes… Lab-locked harnesses must be reported as harness+model systems.”* Wave 1 quoted the Grok-fixed half of that sentence and then added three lab/gateway systems without splitting the report.

---

## 3. Redundancy — which pairs are science, which are spend

### Pi vs OMP — **informative (Track A core)**

This is the only pair in the set that looks like an actual experiment.

- Same lineage: OMP is an explicit **fork of Mario Zechner’s Pi** (“originally built on Pi, omp adds everything you’re missing”).
- Independent variable is *tooling and edit reliability*, not brand: ~4 tools vs ~32, hash-anchored edits, LSP/DAP, subagents.
- Wave 1 is right to refuse treating OMP as “the Pi lineage” (`waves/wave-1-grok-native.md`, `LEARNINGS.md`).

**It is wasteful unless you pin the same Grok slug and the same auth class.** If OMP rides SuperGrok OAuth `grok-4.6` and Pi rides `XAI_API_KEY` `grok-build`, you did not measure the fork.

### Prime Agent vs Pi / OMP — **mostly wasteful in Wave 1; keep as Track C**

Prime Agent **began as a hard fork of `pi-mono`** (its coding-agent README still carries `@earendil-works/pi-*` identifiers). Then it changed the *loop*: RLM + persistent IPython + continual harness, not “Pi + more tools.”

So the set currently has **three Pi-family SUTs** (Pi, OMP, Prime) and only **one xAI-native CLI** (Grok Build). That is overweighting a single OSS skeleton while under-sampling Grok-capable non-Pi harnesses (OpenCode, Aider, Goose, Cline/Kilo — all in the landscape P0/P1 list).

Prime vs Pi is interesting **as architecture** (REPL/RLM vs four-tool). It is not a Grok-native Wave 1 cell, especially with the API-key vs OAuth caveat the wave doc already recorded.

### Hermes vs Grok Build — **wasteful unless tightly constrained**

Two different products that the internet will happily conflate because both say “Grok”:

| | Grok Build | Hermes Agent |
|---|------------|----------------|
| Job | xAI coding CLI/TUI | Nous personal / self-improving agent that *also* codes |
| Default coding model (typical) | `grok-build-0.1` | `grok-4.6` via `xai-oauth` |
| Auth | `grok login` → `~/.grok/auth.json` | Separate Hermes OAuth; can import Grok CLI creds |
| Failure mode | Bad coding loop | Memory/skills/runtime + optional **delegation to `grok`** |

Landscape memo put Hermes in *Personal / always-on*, not in the P0 coding-harness seed. Wave 1 promoted it to first-class SUT because “docs report SuperGrok / xAI OAuth.” **OAuth availability is not a coding-harness inclusion criterion.** By that rule, anything with `/login xai` is Wave 1.

Keep Hermes only if: (1) Grok slug pinned to the Track A pin, (2) `grok` CLI skill off, (3) you are willing to label the row “personal-runtime coding loop,” not “Grok-native harness.” Otherwise **cut from Wave 1**.

### Cursor Grok vs Grok Build — **informative as surface, wasteful as harness-effect**

Different surface (IDE agent vs terminal TUI), different SKU (Cursor-pooled Grok vs xAI `grok-build-0.1` / subscription Grok), different sandbox and edit UX, and this research repo is **operated through Cursor cloud agents**. That last fact is in `DECISIONS.md`. You do not get to treat Cursor as a neutral instrument and a SUT without declaring the conflict.

A defensible write-up is: *“IDE Grok-in-Cursor vs xAI Grok Build CLI, models not matched.”* A fraudulent write-up is putting both in a Grok-fixed harness table.

**Cursor CLI / `cursor-agent` is missing** if the point is Cursor-the-harness rather than Cursor-the-IDE. `possible-harnesses.md` already lists `cursor-agent` as distinct from the CURSOR row. Wave 1 picked the worse-controlled surface.

### Amp vs Codex vs Grok Build — **not a harness comparison**

Three native stacks. Fine as Track B systems. Fatal as “harness effect under Grok.” Amp will not hold Grok fixed; its own docs say modes are capability presets and will swap models when you link a ChatGPT subscription. Codex is OpenAI. Stop putting them in the Grok-native header.

### FX vs Pi — **Track C, not Wave 1 core**

Both are “minimal harness” stories. Pi is the influential MIT/minimal control Wave 1 already has. FX is a 7.8 MiB Zig research binary glued to Vercel AI Gateway (default model in-tree: `zai/glm-5.2`). That is a **minimal-harness architecture** study, not a Grok study. Landscape memo filed `fx (Vercel)` under P2 mid-tier CLIs. Wave 1 promoted it because an install script existed the same afternoon.

---

## 4. Cuts, demotions, missing must-haves

### Cut from Wave 1 Grok-native (or never let them share a ranking table)

| SUT | Action | Why |
|-----|--------|-----|
| **Amp** | **Cut from Wave 1** or Track B-only, later | Cannot pin Grok; routing *is* the product. Landscape: distributed/remote operator. Loud ≠ in-scope. |
| **FX** | **Demote to Track C / optional next** | Gateway-default is not Grok; minimal-Zig is a different question than Grok-harness effect. Pi already covers “minimal.” |
| **Codex CLI** | **Track B baseline only** — keep the install, kill the Grok-native billing | Honest OpenAI-native comparator. Not a Grok SUT. Wave 1 already says this; membership does not. |
| **Prime Agent** | **Track C / Wave 2** | RLM + Pi-fork + API-key Grok. Architecture paper, not Wave 1 cell. |
| **Hermes Agent** | **Demote** unless constrained as above | Personal runtime; nested-Grok-Build risk; OAuth ≠ inclusion. |
| **Cursor Grok** | **Track C-surface or a separate IDE note** | Model SKU + IDE + operator conflict. |

### Keep (Track A)

| SUT | Why it earns a slot |
|-----|---------------------|
| **Grok Build** | The actual xAI-native coding harness. Lab control. |
| **Pi** | Minimal BYOK control; Grok OAuth/API documented; OMP’s upstream. |
| **OMP** | The batteries-included delta on Pi. This pair *is* Wave 1 science. |

That is a three-SUT wave. It is enough. It is more publishable than nine.

### Overweights

- **Pi family (Pi + OMP + Prime)** = 3/9 of Wave 1. One skeleton is not a landscape.
- **Install-list gravity:** Amp, FX, Codex entered because *“install requested 2026-08-24”* (`waves/wave-1-grok-native.md`). Inclusion-by-curl is not a rubric. `possible-harnesses.md` §D still has a *different* “core CLI shortlist draft” (Claude Code, OpenCode, Aider, Cline, …). Wave 1 did not reconcile with it.
- **Hermes first-class** because Grok OAuth exists, while **OpenCode** — landscape P0, 75+ providers, actually Grok-capable BYOK — is “optional next.” That is inverted.

### Missing for a *defensible Grok-performance matrix*

Must-add **before** claiming “we measured Grok harnesses”:

1. **A written model pin** — one slug for BYOK Track A (recommendation: `grok-4.6` *or* `grok-build-0.1`, not “Grok”). Grok Build, if lab-locked to `grok-build-0.1`, is reported as **(Grok Build × grok-build-0.1)** and is *not* pooled with `grok-4.6` BYOK rows without a label.
2. **A written auth pin** — SuperGrok OAuth *or* `XAI_API_KEY`, not mixed inside Track A.
3. **OpenCode** as Track A candidate **ahead of FX and Amp**. It is the obvious Grok-capable OSS terminal agent the landscape memo already ranked P0. Optional-next is cowardice relative to shipping Vercel Zig in Wave 1.
4. **Headless / non-interactive flags** per SUT (`grok -p`, `amp -x`, `codex` non-interactive, Pi JSON/RPC) — landscape memo §eval design. Interactive TUI-only runs are not reproducible.

Nice-to-add, not Wave 1 blockers:

- **Aider** — git-native control (landscape seed). Different edit/commit philosophy than OMP hashline.
- **Cursor CLI** if Cursor must appear; better controlled than IDE Grok.
- **Goose** — foundation-governed BYOK; only if Track A expands past three.

### Claude Code — baseline only, and only if Track B exists

Wave 1 correctly kept Claude Code **out** of a Grok-native claim (`waves/wave-1-grok-native.md` out-of-scope; `DECISIONS.md`). Do not sneak it into Track A.

The **asymmetric** part: Codex was added as “cross-lab baseline” and Claude Code was not. If Track B is “what does a leading lab-native harness look like,” **Claude Code is the missing ceiling**, not Codex-alone. Codex-without-Claude is “we installed OpenAI because the curl was in the same batch.” If Track B is deferred, **Codex should be deferred with it.** One OpenAI CLI is not a baseline set.

Claude Code is relevant as *“this is the market-leader terminal harness; here is the gap to Grok-native Track A.”* It is not a Grok SUT.

---

## 5. Protocol risks — this set invites narrative ranking

### What is missing (the wave doc already listed it and then stopped)

`waves/wave-1-grok-native.md` Tasks section is an empty checklist: no task ids, no success criteria, no fixture repos, no prompt text, no time budget, no tool/network policy, no model pin, no artifact policy. `STATUS.md` (PR #1): *“Wave 1 tasks/protocol not yet specified.”* `evaluation-log.md`: Wave 1 header, **runs: none**. Metrics table is placeholders.

That is fine for a setup PR. It is lethal if the nine-SUT membership is treated as “the eval.” A large unlabeled set plus empty protocol is how you get a Twitter tier list with citations.

### Failure modes to assume

- **Default-model tourism.** Each CLI’s `/model` picker + subscription entitlements → incomparable SKUs, reported as harness winners.
- **Auth-path tourism.** OAuth quota vs API-key billing vs gateway credits vs Amp dial. Latency and “partial” failures become billing artifacts. (`DECISIONS.md` correctly keeps personal spend out of the repo; that does **not** license ignoring *which meter* the run hit.)
- **Interactive operator skill.** Cursor cloud agents / Bobby driving TUIs. Harness effect confounded with human mid-course correction. Headless or log the steering.
- **Nested agents.** Hermes→Grok Build, Amp oracle, Prime `rlm()` children, Grok Build parallel arena. Count one system, or you double-count.
- **Unreproducible fixtures.** “Try it on this repo I’m working on” is not a task id.
- **One-column success.** Pass/fail without edit-format and sandbox notes will crown OMP or Codex for mechanical reasons and call it intelligence.
- **Wave-header gravity.** `evaluation-log.md` already lists nine SUTs under one control sentence. Future runs will get dumped there. **Split the header now.**

### Minimum protocol to make Wave 1 publishable

Not a full SWE-bench. The smallest thing that is not an anecdote:

1. **Freeze the question in one sentence** at the top of the wave doc. Either *“Track A: harness effect under pinned Grok”* or *“Track B: native-stack bake-off.”* Not both in one table.
2. **Track A SUT freeze:** Grok Build, Pi, OMP. Everything else is a different file (`waves/wave-1-track-b.md` / `track-c.md`) or “optional next.”
3. **Pin:** `model_slug`, `auth_class` (`oauth-supergrok` | `xai-api-key`), `binary_version`, `sandbox_profile`, `edit_format`. Refuse to log a run that lacks them. Grok Build if un-pinnable to the BYOK slug is a **labeled system row**, not pooled.
4. **Tasks (n = 3, pre-declared):**  
   - **T1 repair** — known failing test, fixture commit, pass = tests green.  
   - **T2 feature** — add a function + test, pass = tests green + no extra files beyond allowlist.  
   - **T3 refactor** — extract + keep tests green; fail on behavior change.  
   Shared prompt text. Shared fixture SHAs. Time budget (e.g. 15 min wall) and stop condition. No network except model API unless the task says so.
5. **Headless only** for the scored CLI table. Record the exact argv.
6. **Ban list:** Hermes `grok` CLI skill; mixing OAuth and API-key in Track A; publishing Amp/FX/Codex in the Track A table; ranking before all Track A cells are filled (3 tasks × 3 SUTs = 9 runs — smaller than the current *unevaluated* set).
7. **Metrics:** pass/fail/partial against the pre-declared criterion; wall time; retry/tool-error counts if logs allow; **no** invented tokens from private billing UIs (already project law). Qualitative notes are allowed; they are not ranks.
8. **Report shape:** Track A table *and* (optional) Track B system rows *and* Track C architecture notes. Never a single “Wave 1 leaderboard.”

Until (1)–(4) exist, Wave 1 remains setup. Expanding SUTs further is how you guarantee it never ships.

---

## 6. Operating constraint (does not excuse the zoo)

`DECISIONS.md`: heavy work via **Cursor cloud agents**; Grok Bot steers to save Bot quota. Fine as repo operations. It is a **problem** for SUT design:

- Cursor is in the SUT set.
- Cursor is the factory producing the eval.
- Cloud-agent quota pressure favors *documenting installs* over *specifying tasks*. That is visible: PR #1 has a nine-row SUT table and an empty protocol checklist.

Quota is not a methodology. A three-SUT Track A with three tasks is cheaper *and* more scientific than nine installs with zero tasks.

---

## 7. Verdict table (keep / cut / split)

| SUT | Keep in Track A (Grok-native CLI)? | Else | Harsh one-liner |
|-----|------------------------------------|------|-----------------|
| **Grok Build** | **Keep** (lab control) | — | The only xAI-native coding harness; still must label the SKU. |
| **Pi** | **Keep** (minimal control) | — | The actual experimental control for OMP. |
| **OMP** | **Keep** (Pi + tools/edits) | — | Informative *iff* model+auth pinned to Pi. |
| **Hermes Agent** | No, unless constrained | Track C / cut | Personal runtime with a Grok login is not a coding-harness cell. |
| **Prime Agent** | No | Track C | Pi-fork + RLM + API-key Grok = three confounds. |
| **Cursor Grok** | No | Track C-surface | Different SKU, different surface, same vendor as the eval factory. |
| **Amp** | No | Track B later or **cut** | Capability dial; will not hold Grok. |
| **FX** | No | Track C / optional next | Zig+Gateway; default is not Grok; Pi already covers minimal. |
| **Codex CLI** | No | Track B baseline | Valid OpenAI system; fraudulent Grok-native row. |
| **OpenCode** (not in Wave 1) | **Add to Track A waitlist**, ahead of FX/Amp | — | Landscape P0; Grok-capable BYOK; currently inverted under FX. |
| **Claude Code** (out of scope) | Never Track A | Track B ceiling **if** Track B is funded | Market-leader baseline; do not Grok-wash it. Codex-without-Claude is a half baseline. |

**Publishable Wave 1** is Track A: **Grok Build × Pi × OMP**, pinned slug, pinned auth, three tasks, headless, no ranking until the 3×3 is filled.

**Everything else is a different paper.** Putting them in `wave-1-grok-native.md` does not make them Grok-native. It makes the filename a lie.

---

## Citations (repo)

- `waves/wave-1-grok-native.md` (PR #1) — SUT table, “matrix expansion,” empty protocol checklist, Claude Code out of scope, Amp/FX/Codex “not Grok-only.”
- `DECISIONS.md` — harness vs model vs runtime; Wave 1 Grok-driven comparison; matrix expansion not Grok-only; Cursor-cloud-agent operating model; personal spend out of tree.
- `BRIEF.md` — RQ1 hold-model-fixed; success criterion “agreed evaluation protocol” still unmet.
- `STATUS.md` — Wave 1 setup; protocol open; installs in progress; no scored runs.
- `LEARNINGS.md` — compose-harnesses; Hermes/Amp characterizations; Pi as OMP upstream; Prime API-key caveat.
- `evaluation-log.md` — one Wave 1 header, nine SUTs, zero runs.
- `possible-harnesses.md` — Wave 1 shortlist vs a *different* core CLI draft; Claude Code still P0 in section C; `cursor-agent` distinct from Cursor IDE.
- `research/llm-coding-harness-landscape-2026-08.md` — native-harness definition; P0 seed (Claude Code, Codex, OpenCode, Pi, …); Hermes as personal runtime; lab-locked systems as harness×model; FX/Prime as P2; eval design (headless, fixed tasks, same model).
- [PR #1](https://github.com/bnivanov/llm-harness-eval/pull/1) — title rename adding Amp/FX/Codex matrix; no scored claims (good); membership still wrong for the remaining title token “Grok-native.”
