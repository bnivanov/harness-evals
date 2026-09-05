# Decisions

Format: date · decision · why · revisit when

## 2026-08-24 · Ignore community tier ranking as truth

**Decision:** Use the provided tier-list image as a **discovery source for names only**. Do not treat S+++…F− placement as evaluation signal.

**Why:** Community vibes ≠ controlled native-harness performance. Our publishable claim needs reproducible tasks and metrics.

**Revisit:** Never as ranking evidence; always fine as a candidate-discovery artifact.

## 2026-08-24 · Separate harness vs model vs runtime

**Decision:** Tag each candidate as `harness`, `runtime/gateway`, or `ambiguous`. Evaluate harnesses first; track runtimes (e.g. OpenClaw) as orchestrators.

**Why:** Mixing “which model” with “which loop” and “which multi-agent bus” muddies native harness claims.

**Revisit:** After first pilot if taxonomy fails in practice.

## 2026-08-24 · Continuity lives in project files + later GitHub

**Decision:** Keep `BRIEF` / `STATUS` / `DECISIONS` / `LEARNINGS` / harness list / eval log as the source of continuity; mirror to GitHub once the public repo exists.

**Why:** Research continuity must survive chat resets; public repo is the long-term archive.

**Revisit:** When repo is created — switch “source of truth” note here.

## 2026-08-24 · Personal spend stays out of the public repo

**Decision:** Keep all personal token / billing spend data **out of** the public GitHub tree. Do not commit `TOKEN-SPEND.md`, usage-dashboard screenshots, or usage CSVs. Track spend only in private/local project copies.

**Why:** Public research repo should not expose account billing UI or private usage exports.

**Revisit:** Never for raw spend artifacts.

## 2026-08-24 · Canonical billing/surface map lives in landscape/

**Decision:** Maintain `landscape/agentic-tools-subscription-vs-byok.md` as the ongoing reference for **subscription vs BYOK vs hybrid × surface**. Name inventory stays in `possible-harnesses.md`; wave membership stays in `waves/`.

**Why:** Wave 1 already mixed auth economies. A two-axis map (who pays × where the loop runs) is cheaper than rediscovering Devin-as-BYOK or OpenClaw-as-harness every pass.

**Revisit:** When a vendor ships a new auth path (or sunsets one); stamp `Last verified` in that file.

## 2026-08-24 · Heavy repo work via Cursor cloud agents

**Decision:** All non-trivial development on `bnivanov/llm-harness-eval` is done by **Cursor cloud agents**. Harness Reviewer (Grok Bot) steers, scopes, dispatches, reviews results, and keeps light continuity files — it does not burn Bot quota on heavy coding.

**Why:** Conserve Grok Bot included usage; cloud agents are the stronger coding path for the repo.

**Revisit:** Only if Bobby explicitly wants Bot-side edits for a small continuity tweak.

## 2026-09-05 · Standardize harness evaluation on HarnessRouter (UHP) over Herdr/ad-hoc scripts

**Decision:** Standardize all programmatic harness evaluation on **HarnessRouter** (implementing the Unified Harness Protocol) rather than Herdr or ad-hoc subshell scripts. Reserve Herdr for interactive human-in-the-loop terminal supervision.

**Why:** Herdr operates strictly at the terminal (PTY) emulation layer—it cannot manage desktop GUI apps, relies on fragile screen buffer scraping/ANSI parsing, and lacks structured token/cost accounting and model-fixed proxy controls. HarnessRouter standardizes harnesses (Codex, Claude Code, Pi, OMP, OpenCode) behind a headless HTTP `/turn` API, provides normalized event streaming (`tool_call`, `tool_result`, `text_delta`), enables model-fixed routing, and enforces 64+ UHP conformance tests.

**Revisit:** If a harness cannot be run in headless/containerized mode and strictly requires an interactive PTY that cannot be automated via UHP.
