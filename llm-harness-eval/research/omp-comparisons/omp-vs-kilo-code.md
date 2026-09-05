# OMP vs Kilo Code

**Status:** research note (no scores; no runs claimed)
**Date:** 2026-08-25
**Audience:** Bobby, for a pairwise understanding of two OSS coding agents that share almost no runtime DNA
**Method:** GitHub-first. Claims below are cited to files, commits, or first-party docs retrieved on this date. Star counts and community tier lists are ignored.

This is not a leaderboard. Oh My Pi and Kilo Code are both open-source coding agents with large model catalogs and a CLI. That is where the resemblance ends. OMP is a Pi-lineage terminal agent that wired an IDE into the loop. Kilo is a multi-surface product whose *current* engine is an OpenCode fork, whose *product habits* still come from Cline via Roo, and whose *commercial layer* (gateway, cloud, Agent Manager) is original. Treating Kilo as "Cline with a new name" is the mistake this note exists to prevent.

Official homes, used below:

| Product | Site / repo |
|---------|-------------|
| **Pi** (OMP upstream) | [pi.dev](https://pi.dev) · [earendil-works/pi](https://github.com/earendil-works/pi) (was `badlogic/pi-mono`) |
| **OMP (Oh My Pi)** | [omp.sh](https://omp.sh) · [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) |
| **Kilo Code** | [kilo.ai](https://kilo.ai) · [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) |
| **OpenCode** (Kilo CLI upstream) | [anomalyco/opencode](https://github.com/anomalyco/opencode) |
| **kilocode-legacy** (old VS Code tree) | [Kilo-Org/kilocode-legacy](https://github.com/Kilo-Org/kilocode-legacy) |

Vendor-reported numbers (OMP hashline lifts, Kilo "500+ models", "3M+ Kilo Coders", "40T+ tokens") are first-party claims. They are not this project's results.

---

## 1. Identity

**OMP.** Binary `omp`, package `@oh-my-pi/pi-coding-agent` (`18.0.4` in this clone). Stencil Labs / Can Bölük; LICENSE also names Mario Zechner. MIT. TypeScript loop on Bun plus a Rust/N-API core. Surfaces: TUI, `omp -p` / JSON, RPC, ACP (Zed), SDK (`createAgentSession`). No first-party VS Code extension. Editor attachment is ACP.

**Kilo Code.** Binaries `kilo` / `kilocode` (`@kilocode/cli` `7.4.23`). VS Code id `kilocode.Kilo-Code`. JetBrains plugin in-tree (EAP). MIT, copyright Kilo Code 2026 and opencode 2025. Clients talk to `kilo serve` (Hono HTTP + SSE). Cloud agents, hosted review, KiloClaw, and the mobile app are *not* in this git tree.

The fair unit is **OMP CLI vs Kilo's OpenCode-based engine plus the clients that share it**, not vs 2025 Kilo-the-Roo-fork (`kilocode-legacy`).

---

## 2. Lineage (forked vs original)

Two fork stories, stacked on different ancestors. Do not collapse them.

### OMP is a coding-first fork/rewrite of Pi

The README is explicit: "Fork of Pi by @mariozechner," "omp adds everything you're missing," later "rewritten as a coding-first surface." Packages still wear `@oh-my-pi/pi-*`. `docs/porting-from-pi-mono.md` marks last documented pi-mono sync as `b21b42d...` (2026-03-22) and maps `@mariozechner/*` / `@earendil-works/*` onto `@oh-my-pi/*`.

**Inherited:** loop shape, TUI, session JSONL, extension hooks, interactive / print / RPC / SDK. **OMP-original vs minimal Pi:** hashline, LSP/DAP tools, ~31 named tools, `task` worktrees, SuperGrok OAuth, ACP, collab, memory backends, in-process natives. Same *class* of loop. The independent variable is how much IDE was welded in.

### Kilo is not "Cline, renamed"

Kilo's own 2025 blog, [Roo or Cline? We're building a superset](https://blog.kilo.ai/p/roo-or-cline-were-building-a-superset) (2025-04-10), says they forked Roo Code about a month earlier, and Roo itself was a Cline fork. Day-one feature set was Roo's. They then ported Cline-only bits and kept merging Roo. That is the **product DNA**: modes (architect/code/debug/ask), VS Code habits, Roo migration.

That DNA is **not** the 2026 control loop.

Kilo's README FAQ: "Kilo CLI is a fork of OpenCode." `.opencode-version` pins `v1.18.13`. `script/upstream/` merges `anomalyco/opencode` and requires `kilocode_change` markers on patches in shared files. `packages/kilo-vscode/docs/opencode-migration-plan.md` states the current VS Code extension is a **ground-up rebuild** on Kilo CLI, not a port of the old in-process loop. Rebuild GA is first-party dated 2026-04-02. The Roo-derived tree is `kilocode-legacy`. The 2026-04-22 migration guide says a legacy v5.x extension still ships that codebase (Orchestrator, old Memory Bank).

Roo's shutdown is Kilo-reported, not re-cloned here: announcement 2026-04-21, archive dated 2026-05-15, pivot to Roomote.

Cline residue in *this* tree is thin. Roo session import and secret migration exist. `.roorules` / `.clinerules` are **not** ingested. `edit.ts` cites Cline diff-eval papers (bibliography, not `Task.ts`). Delegation is OpenCode's `task` tool. There is **no** Cline `Task.ts` loop in this clone.

**Original Kilo** (upstream-merge config): `kilo-gateway`, `kilo-telemetry`, `kilo-memory`, `kilo-indexing`, `kilo-sandbox`, `kilo-vscode`, `kilo-jetbrains`, `packages/opencode/src/kilocode/**`, Agent Manager UI.

```text
Cline  →  Roo Code  →  2025 Kilo VS Code   →  kilocode-legacy (archive)
                                              ↘ product DNA (modes, Roo import)

anomalyco/opencode  →  2026 Kilo CLI/server  →  kilo serve ← VS Code / JetBrains / CLI / cloud
                     (current control loop)
```

A paper that scores "Kilo vs Cline" is a different paper. This one scores **Kilo as shipped in `Kilo-Org/kilocode` main**.

---

## 3. Architecture and control loop

**OMP.** `cli.ts` → `createAgentSession` → `AgentSession` → `@oh-my-pi/pi-agent-core` `agentLoop`. Inner loop: model call, tools, steering, stop on error/abort/length. Compaction sits in-process. TUI, print/JSON, RPC, and ACP share one session object. No separate server product. Headless is `omp -p`.

**Kilo.** Every surface is a client of `packages/opencode/`. VS Code's `ServerManager` spawns `kilo serve --port 0`. `kilo run` is non-interactive; `--auto` disables permission prompts. The processor stops on deleted session, blocked permissions, errors, abort, and step budget. Kilo patches OpenCode agents: `build` → `code`; `plan` / `ask` / `debug` first-class; `orchestrator` **deprecated**. README "Review" is a `/review` command, not a native agent.

The architectural fork is therefore:

```text
OMP     model → named tools (incl. lsp/debug/task) → results → model
        one process, optional ACP into an editor

Kilo    client → kilo serve → OpenCode session/processor → tools
        same engine in VS Code, JetBrains, CLI; cloud is hosted
```

If you eval both as "a CLI that edits a repo," you can hold the surface fixed (`omp -p` vs `kilo run`). If you eval Kilo as users actually buy it, you are measuring IDE chrome, Agent Manager, and gateway routing on top of that loop.

---

## 4. Tools and edit protocol

**OMP tools.** `BUILTIN_TOOL_NAMES` has 30 factories; `generate_image` and `tts` register when enabled. README "31 built-in tools" matches that user-facing set. Hidden: `yield`, `goal`, `think`. MCP is `mcp__*`. `--tools` pins the namespace.

The interesting part is not the count. Default `edit` consumes [hashline](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/README.md): `[PATH#TAG]` where `TAG` is a four-hex content hash from the latest read. Stale tags are refused or recovered against a snapshot. `lsp` has 14 ops; `debug` has 28 DAP ops. Grep and bash run in-process via Rust. `eval` is persistent Python and JS that can call back into agent tools. It is one tool among many, not the loop. OMP's edit-format lift table is **vendor-reported**.

**Kilo tools.** OpenCode registry plus Kilo extras. Core: `bash`, `read`, `glob`, `grep`, `edit`, `write`, `task`, `webfetch`, `apply_patch`, `skill`. Kilo adds `semantic_search`, `kilo_memory_*`, VS Code `agent_manager`. `lsp` is behind `experimentalLspTool`. No first-party DAP `debug` tool in the registry reviewed here. Edit is search/replace; GPT-family models prefer `apply_patch` (`KiloToolRegistry.usePatch()`). Prompts ask for parallel independent tool calls.

---

## 5. Context, memory, extensibility

**OMP.** Discovers `AGENTS.md`, sticky `RULES.md`, and Cursor/Cline/Codex/Copilot/Gemini/Windsurf files in native shape. Memory backends are mutually exclusive (`off` default, `local`, `hindsight`, `mnemopi`). Extensions are TypeScript factories. MCP comes from the same foreign config dirs. Skills, slash commands, a plugin marketplace, and the SDK are first-class.

**Kilo.** `.kilocoderules` and `.kilocode/rules/**` inject into OpenCode `instructions` without rewriting project files. `AGENTS.md` / `CLAUDE.md` load natively. `.roorules` / `.clinerules` are **not** migrated. `@kilocode/kilo-memory` and `@kilocode/kilo-indexing` sit behind `kilo_memory_*` and `semantic_search` when enabled. The rebuilt VS Code parity plan still lists indexing as incomplete vs legacy. MCP Hub UI and marketplace toolbar are partial/stubs.

OMP inherits instruction files and adds IDE protocols. Kilo ships Kilo-shaped rules plus a vector index, shared across IDE and CLI. They store different objects.

---

## 6. Auth and the "500+ models" claim

Kilo's README, VS Code `package.json`, `AGENTS.md`, and [kilo.ai](https://kilo.ai) all say **500+ models**, mid-task switching, zero markup, no API keys required to start. The last clause is Gateway (`packages/kilo-gateway/`: device OAuth, credits). BYOK is also real (`model: "provider/model"`).

**Verification, 2026-08-25.** Unauthenticated `GET https://api.kilo.ai/api/openrouter/models` returned **369** unique ids (300 with `tools` in `supported_parameters`). Auto-router slugs: `kilo-auto/frontier`, `balanced`, `efficient`, `free`, `small`. A test fixture lists 346 under the `kilo` provider key and thousands more in a BYOK-style map.

**Verdict.** "500+" is **not verified** from the public Gateway catalog (369 < 500). It might hold if you union authenticated org lists and BYOK providers. It is not an eval pin. `kilo-auto/*` is **routing**; the routed id is `kilocode.routedModelID`. Sticky Models pin a model *per agent*. Use a concrete slug and log that field.

**OMP.** README "60+ providers" is conservative: **69** `CATALOG_PROVIDERS`, **4515** bundled `"id"` fields. A bundled spec is not an available model. Roles pin `provider/model-id`. xAI is two providers: `xai` (`XAI_API_KEY`, default `grok-4.6`) and `xai-oauth` (`XAI_OAUTH_TOKEN`). That is the Track A pin.

Kilo ships `xai` in BYOK fixtures. A dedicated SuperGrok OAuth provider analogous to `xai-oauth` was **not** found. Grok-fixed Kilo is BYOK or whatever the Gateway lists that day. Leave Auto Model on and the pin is gone. OMP's "a thousand models" line is also marketing. Same caution, different direction.

---

## 7. Surfaces, safety, multi-agent, OSS

**Surfaces.** OMP: TUI, print, RPC, ACP, `/collab`, Windows-native binaries. Kilo: VS Code, JetBrains, CLI, hosted cloud/review/claw/app (marketing). Slack packaging is skipped in the merge config. Autocomplete is an IDE feature OMP does not attempt.

**Safety.** OMP: `always-ask` / `write` / **`yolo` (default)**; per-tool allow/deny/prompt; ACP permission prompts; worktree isolation. Not a kernel sandbox. Kilo: allow/ask/deny rulesets plus `@kilocode/sandbox` (Seatbelt / bubblewrap). `kilo run --auto` is CI yolo. Pin the policy or you measure the policy.

**Multi-agent.** OMP `task` → isolated worktrees, typed `yield`, Agent Hub. Kilo `task` → OpenCode children (`explore`, `general`). Agent Manager is VS Code-only (parallel chats, git worktrees, one `kilo serve`). Orchestrator-as-mode is deprecated; legacy v5 still has old Roo Orchestrator.

**OSS, telemetry, eval.** Both MIT. OMP telemetry is opt-in OTLP. Kilo ships a **hardcoded PostHog key** in `kilo-telemetry/src/client.ts`, gated by `enabled` / `KILO_TELEMETRY_LEVEL`. OMP has JSONL, RPC, `pi-metaharness`, an in-repo edit benchmark. Kilo has `kilo run --auto` and HTTP-recorder fixtures. Record CLI version, Kilo `.opencode-version`, `routedModelID`, OMP `modelRoles`, approval mode, and edit format, or the run is not reproducible.

---

## 8. Evidence table

Uncertain cells are **?**. Counts are from clones and HTTP fetches on 2026-08-25 and will drift.

| Axis | OMP (`can1357/oh-my-pi`) | Kilo Code (`Kilo-Org/kilocode`) |
|------|--------------------------|----------------------------------|
| **What it is** | Coding-first Pi fork/rewrite; CLI/TUI | Multi-surface agent platform; OpenCode-fork engine + Kilo clients |
| **Command / packages** | `omp`; `@oh-my-pi/pi-coding-agent` 18.0.4 | `kilo` / `kilocode`; `@kilocode/cli` 7.4.23; VS Code `kilocode.Kilo-Code` |
| **License (this tree)** | MIT (Zechner, Bölük, Stencil Labs) | MIT (Kilo Code 2026, opencode 2025). Marketing pages that still say Apache-2.0 for "the extension" refer to **legacy** / Roo-era packaging; current `kilo-vscode/package.json` is MIT |
| **Control loop** | In-process `agentLoop`; named tools | `kilo serve` + OpenCode `processor`; clients over HTTP/SSE |
| **Default tools** | 31 user-facing names; LSP 14; DAP 28 | OpenCode core + Kilo extras; LSP **experimental**; no DAP tool found |
| **Edit protocol** | Hashline (content-hash anchors; stale reject/recover). Also `ast_edit` | `edit` search/replace; `apply_patch` for GPT-family |
| **Model catalog claim** | 60+ providers (69 descriptors; 4515 bundled ids) | "500+ models" **unverified** on public Gateway (369 ids this fetch) |
| **Pinning** | `modelRoles.default: provider/model-id`; role split (`smol`, `advisor`, ...) | Config slug **or** `kilo-auto/*` routing (`routedModelID`). Sticky Models per agent |
| **Grok / xAI** | `xai` + `xai-oauth`; default slug `grok-4.6` | BYOK `xai` in fixtures; Gateway catalog varies. SuperGrok OAuth as OMP-style provider **?** |
| **Memory** | `off` / local / Hindsight / Mnemopi | `kilo-memory` + optional `kilo-indexing` / `semantic_search` |
| **Instruction files** | Native + Cursor/Cline/Codex/Copilot/Gemini/Windsurf | `.kilocoderules` / `.kilocode/rules`; `AGENTS.md`/`CLAUDE.md`. Not `.roorules`/`.clinerules` |
| **Subagents** | `task` → worktrees, typed yield, Agent Hub | `task` → OpenCode children; Agent Manager (VS Code); `orchestrator` deprecated |
| **Sandbox / permissions** | Approval modes; **yolo default**; ACP prompts; worktree iso. Not kernel sandbox | Permission rulesets; `@kilocode/sandbox` Seatbelt/bubblewrap; `kilo run --auto` |
| **Surfaces** | TUI, `-p`/JSON, RPC, ACP, collab web | VS Code, JetBrains, CLI, hosted cloud/review/claw/app |
| **Headless / eval** | `-p`, JSON, RPC, pi-metaharness, edit benchmark | `kilo run --auto`, HTTP fixtures. No first-party Harbor-style bench package found |
| **Telemetry** | Opt-in OTLP | PostHog client in-tree; gated by `enabled` / `KILO_TELEMETRY_LEVEL` |
| **Lineage** | Pi (`pi-mono` / Earendil) | Product DNA: Cline→Roo→legacy Kilo. Runtime: OpenCode fork. Original: gateway, sandbox, memory, indexing, IDE rebuilds |

---

## 9. Where OMP is better

**Edit reliability as an independent variable.** Hashline is a designed patch language with a grammar, a snapshot store, and a stale-anchor reject path. Kilo's `edit` is the industry-default search/replace (plus `apply_patch` for GPT). If your failure mode is "the model applied a hunk to the wrong whitespace," OMP is the only one of the two that made that the product thesis. You still have to log the format. You do not get to import the blog's 6.7% → 68.3% as ours.

**IDE protocols inside the CLI.** Fourteen LSP ops and twenty-eight DAP ops are tools, not a hidden experimental flag. Rename goes through `workspace/willRenameFiles`. A segfault is lldb, not another `console.log`. Kilo's `lsp` is experimental; DAP was not in the registry. For semantic refactor and crash-debug tasks, that gap is the whole story.

**A pin you can write down.** Roles take `provider/model-id`. SuperGrok OAuth is a real provider id (`xai-oauth`) next to `XAI_API_KEY`. Kilo's headline catalog is a Gateway plus Auto Model. For Track A (hold Grok roughly fixed), OMP is the product that documents the pin this project's protocol needs.

**Eval-shaped headless.** JSON event streams, RPC, a metaharness that bind-mounts source into Harbor trials and keeps auth on the host, an in-repo TypeScript edit benchmark. Kilo's `kilo run --auto` is enough to *start* an eval. OMP already built the scaffolding you would otherwise write.

**Quiet telemetry default.** Opt-in OTLP vs an in-tree PostHog key. For a public research log that is supposed to keep personal spend and account noise out of GitHub, OMP's default is the less embarrassing one.

**Windows-native CLI without WSL.** In-process bash/grep and `install.ps1`. Kilo ships Windows zips; the IDE story still wants VS Code or JetBrains.

**One process you can read.** Still not minimal, but it is one TypeScript agent plus Rust natives, not an OpenCode merge plus Solid webview plus Kotlin plugin plus gateway.

---

## 10. Where Kilo Code is better

**The same engine in the editor you already live in.** VS Code and JetBrains are not ACP afterthoughts. They spawn `kilo serve` and share sessions with the CLI. Autocomplete, Agent Manager, inline diffs, and "sticky" per-agent models are why people install Kilo. OMP's honest answer to "I want this in IntelliJ" is "use ACP if your editor speaks it," which JetBrains does not, out of the box.

**A permission model that looks like a product.** Allow/ask/deny rules with globs, plus an OS sandbox package (Seatbelt, bubblewrap) rather than "yolo unless you change it." Plan and Ask agents are permission-hardened in `kilocode/agent/index.ts` (plan may only mutate plan files; ask is no-edit). OMP can do strict modes. It does not ship them as the default personality of the binary.

**Indexing and project memory as packages.** `semantic_search` over LanceDB/Qdrant and `kilo-memory` are engineered for "the agent knows this repo." OMP's memory is real (Hindsight, Mnemopi) but optional and off by default. For large-repo questions where grep is the wrong first tool, Kilo has the named tool.

**Team and hosted surfaces.** Gateway (start without minting lab keys, zero-markup pitch), org policy (Kilo's 2026-08-24 blog on sub-org model choice), cloud agents, PR review product, mobile app. Those are out of scope for a native-CLI harness cell and in scope for anyone comparing "can this org actually adopt it." OMP's `/collab` is a session share, not a company portal.

**Subagents as an IDE control plane.** Agent Manager with worktrees and a shared backend is a different artifact from OMP's `task` cards. Parallel isolated chats that a human can steer from the sidebar is the Roo-migration promise Kilo actually rebuilt for. Deprecated `orchestrator` shows they know the old mode does not map 1:1 onto OpenCode. The replacement is the Manager, not a prompt.

**Living upstream.** Merge automation absorbs `anomalyco/opencode` tags. OMP's pi-mono porting guide is a checklist, not a factory. Kilo has a company, a gateway, and an upstream that is not one person's Pi.

**CI one-liner.** `kilo run --auto "run tests and fix any failures"` is documented. OMP can `--yolo` and `-p`; Kilo named the CI use case in the README.

---

## 11. Unknowns

1. Authenticated Gateway catalog size (369 is public only). Org lists might clear 500.
2. SuperGrok OAuth on Kilo as a first-class login vs BYOK / Gateway SKU. Not demonstrated.
3. `kilocode-legacy` release cadence. Referenced as archive and pin-able v5.x.
4. Roo GitHub archive bit. Cited from Kilo's guide; `RooCodeInc/Roo-Code` not cloned.
5. Rebuilt VS Code parity. Migration plan still lists stubs. Same engine ≠ feature-complete vs legacy.
6. OMP live selectable model count after credentials. 4515 is a catalog.
7. Cloud / Slack / mobile internals. Not in the clone.
8. Head-to-head task success. Neither binary was run. `evaluation-log.md` is empty.
9. Clean-install default slugs. OMP xAI descriptors say `grok-4.6`. Kilo Auto Model is a router. Live `kilo` first-run slug not captured here.
10. JetBrains EAP vs VS Code Agent Manager completeness.

---

## 12. Fair empirical eval still needed

Nothing here is a score. A fair cell would hold the *loop* as the independent variable and freeze everything the Wave 1 adversarial review already named as confounds ([`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md)).

**Do not** put OMP and Kilo in one "Grok-native CLI" table without pins. They are different loop families (Pi-named-tools vs OpenCode-server), different auth economies (OMP roles / SuperGrok OAuth vs Kilo Gateway / Auto Model), and different surfaces (TUI vs IDE+CLI). A single success% column would measure all of that at once.

**Minimum protocol if you run them anyway:**

1. Surface: headless CLI only (`omp -p` / `--mode json` vs `kilo run`). No Agent Manager, no VS Code webview, no cloud.
2. Model: concrete `provider/model-id` on both. **Disable** `kilo-auto/*`. Log Kilo `routedModelID`. On OMP, pin `modelRoles.default` *and* `smol`/`task` so subagents do not silently cheapen.
3. Auth class: same ledger if claiming Grok-fixed (both `XAI_API_KEY`, or both SuperGrok OAuth). Gateway credits vs SuperGrok OAuth is not the same product.
4. Edit format: log `hashline` vs `edit`/`apply_patch`. A patch-failure is not "harness IQ."
5. Permissions: pin OMP `--approval-mode` (do not leave `yolo` implicit) and Kilo sandbox/ruleset (do not leave `--auto` implicit unless that is the condition).
6. Versions: OMP package/git SHA; Kilo `@kilocode/cli` version **and** `.opencode-version`.
7. Telemetry: off, or logged as on.
8. Tasks: the same three pre-declared fixtures, same repo snapshot, same success criteria. No vendor benches.

**Suggested placement.** OMP stays Track A with Pi and Grok Build (same lineage class, pin slug and auth). Kilo is a **Track B / multi-surface OSS platform** row, or a later "OpenCode-family" cluster with OpenCode itself as the control. Scoring Kilo against Cline is a third experiment. Scoring Kilo against OMP as if they were two Pi forks is a category error.

Publishable claim this note supports: **the products are not substitutes.** OMP is the batteries-included Pi coding loop. Kilo is an OpenCode-based platform with Cline/Roo product memory and a company gateway. Pick the independent variable before you spend tokens.

---

## Sources (official, retrieved 2026-08-25)

- OMP clone `can1357/oh-my-pi`: README, `LICENSE`, `builtin-names.ts`, `docs/approval-mode.md`, `docs/providers.md`, `docs/porting-from-pi-mono.md`, `packages/hashline/README.md`, `descriptors.ts`, `models.json` (4515 ids, 69 providers), `packages/coding-agent/package.json` (`18.0.4`)
- Kilo clone `Kilo-Org/kilocode` (HEAD `534b6a1`): README, `LICENSE`, `.opencode-version` (`v1.18.13`), `AGENTS.md`, `@kilocode/cli` `7.4.23`, `opencode-migration-plan.md`, `tool/registry.ts`, `kilocode/tool/registry.ts`, `kilocode/agent/index.ts`, `routed-model.ts`, `rules-migration.md`, `kilo-telemetry/src/client.ts`, `script/upstream/README.md`
- Live catalog: `GET https://api.kilo.ai/api/openrouter/models` → 369 ids
- Kilo first-party: [kilo.ai](https://kilo.ai), [superset blog](https://blog.kilo.ai/p/roo-or-cline-were-building-a-superset) (2025-04-10), [rebuild GA](https://blog.kilo.ai/p/new-kilo-for-vs-code-is-live) (2026-04-02), [Thank you, Roo!](https://blog.kilo.ai/p/thank-you-roo) (2026-04-21), [migration guide](https://kilo.ai/articles/roo-to-kilo-migration-guide) (2026-04-22)
- This repo: [`waves/wave-1-adversarial-review.md`](../../waves/wave-1-adversarial-review.md), [`landscape/agentic-tools-subscription-vs-byok.md`](../../landscape/agentic-tools-subscription-vs-byok.md)

**Not verified here:** live binaries on an evaluator machine; authenticated Gateway catalog; Roo archive bit; any task success, latency, or cost.
