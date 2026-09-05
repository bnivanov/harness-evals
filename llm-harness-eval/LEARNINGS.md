# Learnings

## 2026-08-24 — Landscape snapshot (pre-eval)

- By mid-2026, serious coding setups often **compose** harnesses (e.g. Claude Code or Codex as engines) rather than pick a single winner.
- “Harness” language is mainstream: control loop, tools, sandbox, MCP, instruction files (`CLAUDE.md` / `AGENTS.md`), subagents.
- Notable brand churn (sources mid-2026): Gemini CLI → Antigravity CLI; Windsurf → Devin Desktop; Continue acquired by Cursor (reported); Amazon Q path toward Kiro.
- OpenClaw is frequently framed as a **gateway/runtime**, not a pure coding harness — keep taxonomy clean in the candidate list.
- Pi is repeatedly cited as a **minimal extensible** harness; Hermes as **learning / memory-oriented**; Amp as **distributed/remote** operator; Claude Code & Codex as leading terminal coding harnesses.

## 2026-08-24 — Wave 1 SUT set does not match the Grok-fixed thesis

Pointer: [`waves/wave-1-adversarial-review.md`](waves/wave-1-adversarial-review.md) (review of PR #1 / `waves/wave-1-grok-native.md`; no scores).

- “Hold Grok fixed, vary harness” is already false **inside** the Grok-native cluster: Grok Build typically `grok-build-0.1`, Pi/Hermes OAuth default `grok-4.6`, Cursor Grok is a Cursor-pooled / jointly trained SKU.
- Amp / FX / Codex were added as a “matrix expansion” but still live in the Wave 1 Grok-native header. Amp will not pin Grok (capability dial). FX gateway default is not Grok. Codex is OpenAI-native.
- Pi vs OMP is the only clean experiment (minimal vs batteries, same lineage). Prime Agent is a third Pi-family row (hard fork → RLM) and overweights one skeleton.
- Hermes can delegate to Grok Build; nested SUT. Cursor is both SUT and the cloud-agent factory for this repo.
- Publishable Wave 1 is Track A: **Grok Build × Pi × OMP**, pinned slug/auth, three tasks, headless. Everything else is Track B (lab stacks) or Track C (experimental / IDE / RLM). OpenCode belongs on the Grok BYOK waitlist ahead of FX/Amp.

## 2026-08-24 — Subscription vs BYOK is a second axis (not a quality ranking)

Pointer: [`landscape/agentic-tools-subscription-vs-byok.md`](landscape/agentic-tools-subscription-vs-byok.md).

- Devin is plan-quota / on-demand / enterprise **ACU** — not classic BYOK.
- OpenClaw is a **runtime-gateway**, not a native coding harness.
- SuperGrok OAuth and `XAI_API_KEY` are different ledgers; same for Claude `/login` vs `ANTHROPIC_API_KEY` and ChatGPT Codex vs API key.
- Cursor Grok (plan SKU) ≠ Grok Build CLI ≠ Grok Bot.

## 2026-09-05 — Herdr agent management and evaluation boundaries

- **Herdr architecture**: A terminal multiplexer and workspace daemon (`Session` → `Workspace` → `Tab` → `Pane`) purpose-built for AI coding agents. Operates on POSIX pseudoterminals (PTYs), detects lifecycle states (`idle`, `working`, `blocked`, `done`, `unknown`) via screen buffer inspection and agent hook scripts (`~/.claude/hooks`, `~/.omp/...`, `~/.codex/`).
- **Herdr scope & limits**: Supports CLI/TUI agents natively (`codex`, `claude`, `pi`, `omp`, `hermes`, `opencode`), but **cannot** host, embed, or inspect desktop/GUI apps (such as the ChatGPT desktop app or Codex/Cursor IDE window). GUI applications run detached from the PTY and require OS-level accessibility/screen automation.
- **Benchmarking methodology**: Herdr is ideal for interactive multi-agent orchestration and live TUI inspection, but unsuitable for scientific harness benchmarking due to ANSI/alternate-screen parsing fragility, absence of provider-level token/cache accounting, and lack of model-fixed proxy controls. Use HarnessRouter (UHP) as the formal headless evaluation engine.

*(Pilot eval learnings go below this line.)*
