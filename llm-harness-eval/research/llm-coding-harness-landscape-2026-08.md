# LLM Coding Harnesses / AI Coding Agents Landscape — August 2026

**Purpose:** Candidate inventory for a public GitHub research project evaluating **native harness performance** (tools people actually run to write/edit code with LLMs).  
**Date:** 2026-08-24 (Europe/Rome).  
**Method:** Multi-query web research + curated directories (awesome-cli-coding-agents, Terminal Trove, best-of-Agent-Harnesses, Tech Stackups, etc.).  
**Caveat:** Star counts and product status drift weekly; treat URLs as primary. Do not invent products — uncertain items are marked.

---

## Suggested evaluation scope: what “native harness” means

A **coding agent harness** is everything except the model: agent loop, tools (read/write/edit/bash), context management, system prompt, permissions, and UI/CLI surface. You describe a task; the agent plans, edits, runs tests, and iterates.

**Strong “native harness” eval candidates (recommended scope):**

| Include | Exclude or deprioritize |
| --- | --- |
| CLI/TUI agents that edit repos + run shell on a local (or sandboxed) machine | Pure autocomplete / chat-in-IDE without agent loop |
| IDE agents with multi-file edit + tool use (Composer, Cascade/Devin Local, Cline) | Generators that only scaffold UI in a browser (v0, Bolt, Lovable) unless you define a separate “vibe coding” track |
| Lab CLIs: Claude Code, Codex CLI, Gemini/Antigravity CLI, Grok Build | Personal always-on assistants (OpenClaw family) unless coding is the primary workload |
| Open-source BYOK harnesses: OpenCode, Aider, Pi, Goose, Crush, Reasonix, etc. | Meta-orchestrators that only wrap other CLIs (session multiplexers) — useful as infra, not as the unit under test |
| Autonomous cloud agents that still produce PRs (Devin, Jules, Copilot coding agent) — as a **separate autonomy track** | Generic multi-agent frameworks (LangChain/CrewAI) not marketed as coding products |

**Eval design notes:** Harness × model pairing dominates outcomes (see ofox.ai / Terminal-Bench commentary). Prefer headless/`--print`/CI modes, fixed tasks (SWE-bench / Terminal-Bench style), and same model where BYOK allows. Lab-locked harnesses (Claude-only, Gemini-only) must be reported as harness+model systems.

---

## Confirmed from image (named)

Format: **Name** — one-line what it is | homepage/GitHub | category | In image: **Yes**

### High-visibility / frequently compared

| Name | What it is | URL | Category |
| --- | --- | --- | --- |
| **Amp** | Sourcegraph-spun coding agent; multi-model via modes; CLI-first after early-2026 IDE pivot | https://sourcegraph.com/amp | CLI agent (closed) |
| **Cursor** | AI-native IDE + Composer / Background Agents / `cursor` CLI | https://cursor.com / https://cursor.com/cli | IDE + CLI |
| **Continue** | Open-source IDE/CLI coding assistant | https://github.com/continuedev/continue | IDE / CLI |
| **Droid** (Factory) | Factory’s multi-surface “Droids”; strong Terminal-Bench history; CLI/IDE/Slack/Linear | https://factory.ai / https://github.com/Factory-AI/factory | Autonomous / CLI (closed) |
| **GitHub Copilot** | IDE + Copilot CLI + cloud coding agent (issue→PR) | https://github.com/features/copilot / https://github.com/github/copilot-cli | IDE + CLI + cloud |
| **OpenCode** | Leading OSS terminal coding agent; 75+ providers; Anomaly | https://opencode.ai / https://github.com/anomalyco/opencode | CLI agent |
| **OpenHands** | OSS agentic SWE environment (ex-OpenDevin); CLI + web | https://github.com/All-Hands-AI/OpenHands | Autonomous / CLI |
| **Roo Code** | Multi-mode agent (architect/code/debug); Cline lineage; upstream archived mid-2026 per some reports — verify before eval | https://github.com/RooCodeInc/Roo-Code | IDE / CLI |
| **aider** | Mature git-native CLI pair programmer (Paul Gauthier) | https://github.com/Aider-AI/aider | CLI agent |
| **Warp** | Agentic terminal; can orchestrate other coding CLIs | https://www.warp.dev / https://github.com/warpdotdev/Warp | Terminal / agent |
| **SWE-agent** | Research harness for repo-issue solving / SWE-bench workflows | https://github.com/SWE-agent/SWE-agent | Research / autonomous |
| **Plandex** | Plan-first multi-file CLI agent | https://github.com/plandex-ai/plandex | CLI agent |
| **Codebuff** | Multi-agent coding assistant with CLI | https://github.com/CodebuffAI/codebuff | CLI agent |
| **Devon** | OSS pair programmer TUI (entropy-research) | https://github.com/entropy-research/Devon | CLI agent |
| **open-codex** | Lightweight Codex CLI fork with multi-provider support | https://github.com/ymichael/open-codex | CLI agent |
| **Claude Engineer** | Community Claude-oriented agentic CLI | https://github.com/Doriandarko/claude-engineer | CLI agent |
| **ForgeCode** | Pair-programming CLI; 300+ models (antinomyhq/forge) | https://github.com/antinomyhq/forge | CLI agent |
| **Auggie** | Augment Code’s agentic CLI + CI/`--print` | https://github.com/augmentcode/auggie | CLI agent (closed) |
| **Tabnine CLI** | Enterprise terminal agentic assistant (Docker distribution) | https://docs.tabnine.com/main/getting-started/tabnine-cli | CLI agent (closed) |
| **Groq Code CLI** | Lightweight OSS CLI on Groq inference | https://github.com/build-with-groq/groq-code-cli | CLI agent |
| **RA.Aid** | LangGraph research/plan/implement autonomous coder | https://github.com/ai-christianson/RA.Aid | Autonomous / framework |
| **Agentless** | Lightweight SWE approach without persistent agent loops | https://github.com/OpenAutoCoder/Agentless | Research / autonomous |
| **AutoBE** | Compiler-driven NestJS/Prisma backend generator (Wrtn Labs) | https://autobe.dev / https://github.com/wrtnlabs/autobe | Specialized autonomous |
| **cursor-agent** | Community Python agent approximating Cursor-style coding | https://github.com/civai-technologies/cursor-agent | CLI agent |

### Personal / always-on + coding-capable (image)

| Name | What it is | URL | Category |
| --- | --- | --- | --- |
| **Hermes Agent** | Nous Research self-improving agent; memory + skills; chat + coding | https://github.com/NousResearch/hermes-agent | Personal runtime / CLI |
| **OpenClaw** | Viral local personal AI assistant (ex-Clawdbot/Moltbot); multi-channel | https://github.com/openclaw/openclaw | Personal runtime |
| **Letta Code** | Memory-first coding CLI on Letta (ex-MemGPT) | https://github.com/letta-ai/letta-code | CLI agent |
| **LettaBot** | Multi-channel personal assistant on Letta | https://github.com/letta-ai/lettabot | Personal runtime |

### Mid-list CLI / niche (image — verified)

| Name | What it is | URL | Category |
| --- | --- | --- | --- |
| **Reasonix** | Go binary; long unattended runs; ACP + desktop/browser/CLI | https://github.com/esengine/DeepSeek-Reasonix | CLI agent |
| **Kilo Code CLI** | OSS agentic platform; VS Code/JetBrains/CLI; 500+ models | https://kilo.ai / https://github.com/Kilo-Org/kilocode | IDE + CLI |
| **Tau** | Hugging Face / Pi-inspired small readable Python coding agent | https://github.com/huggingface/tau | CLI agent |
| **CodeMachine** (CodeMachine-CLI) | Community multi-agent local “vibe” CLI | https://github.com/moazbuilds/CodeMachine-CLI | CLI agent |
| **Free Code** | Claude Code fork with telemetry/guardrails stripped | https://github.com/paoloanzn/free-code | CLI agent (fork) |
| **g3** | Rust coding agent; tools + skills + providers | https://github.com/dhanji/g3 | CLI agent |
| **QQCode** | Small Rust CLI; speed/determinism focus | https://github.com/qnguyen3/qqcode | CLI agent |
| **Neovate** (Neovate Code) | Ant Group CLI; plugins, MCP, headless | https://github.com/neovateai/neovate-code | CLI agent |
| **picocode** | Minimal Rust agent for CI/codemods | https://github.com/jondot/picocode | CLI agent |
| **Keen Code** | Go CLI; lean TurnMemory context strategy | https://github.com/mochow13/keen-code | CLI agent |
| **Mentat CLI** | Mentat/AbanteAI; historically CLI pair programmer; also cloud Mentat CLI docs | https://mentat.ai / AbanteAI/mentat (historic) | CLI / cloud |
| **Ante** | Antigma Labs Rust binary research-preview coding agent | https://github.com/AntigmaLabs/ante-preview | CLI agent (closed binary) |
| **Zap** | Rust TUI; AST-indexed skills-first agent | https://github.com/zap-coding-agent/zap-coding-agent | CLI agent |
| **Every Code** | Codex CLI fork; multi-provider + automation extras | https://github.com/just-every/code | CLI agent (fork) |
| **Octomind** | Rust model-agnostic agent runtime + tap registry | https://github.com/Muvon/octomind | CLI / runtime |
| **OpenSquilla** | Self-hostable microkernel agent + CLI | https://github.com/opensquilla/opensquilla | CLI / runtime |
| **nori-cli** | Multi-provider CLI built on Codex | https://github.com/tilework-tech/nori-cli | CLI agent |
| **Kode CLI** | ShareAI multi-model/subagent terminal agent | https://github.com/shareAI-lab/Kode-cli | CLI agent |
| **MiMo Code** | Xiaomi official terminal coding agent | https://github.com/XiaomiMiMo/MiMo-Code | CLI agent |
| **Trae Agent** | ByteDance research-friendly SWE CLI | https://github.com/bytedance/trae-agent | CLI / research |
| **Codel** | Docker + web UI autonomous terminal agent | https://github.com/semanser/codel | Autonomous |
| **Crush** | Charmbracelet glamorous multi-provider coding TUI | https://github.com/charmbracelet/crush | CLI agent |
| **Smelt** | Rust TUI; Normal/Plan/Apply/Yolo modes | https://github.com/leonardcser/smelt | CLI agent |
| **Clif Code** | Rust native editor + terminal agent (ClifPad/ClifCode) | market.dev / Clif-Code listings | IDE + CLI |
| **FetchCoder** | Fetch.ai / ASI1 terminal coding agent | https://github.com/fetchai/fetchcoder-releases | CLI agent (closed) |
| **Dexto** | Truffle AI coding + general harness; CLI/web/API | https://github.com/truffle-ai/dexto | CLI / framework |
| **VT Code** | OSS coding agent; shell safety + multi-provider | https://github.com/vinhnx/vtcode | CLI agent |

### Image names not confidently re-identified

| Name as listed | Status |
| --- | --- |
| **Soulforge** | No clear primary coding-harness product found in Aug 2026 search results — **uncertain / unverified** |
| **Aizen** | No clear primary coding-harness product found — **uncertain / unverified** |
| Generic “\*\*Claw\*\*” entries without names | Treat as **OpenClaw ecosystem** (see logo section) |

---

## Likely logo IDs (confidence labeled)

Community tier-list images often show logos without text. Matches below are **inferred**; confirm against the actual image before publishing.

| Visual cue (from query) | Likely product | Confidence | Notes |
| --- | --- | --- | --- |
| White **P** on dark | **Pi** (Earendil / Mario Zechner minimal harness) | **High** | Pi is a top-tier OSS harness; name/logo fit |
| White **K** on black | **Kilo Code** | **High** | Strong brand “K”; IDE+CLI platform |
| Hexagon cluster / geometric mosaic | **Uncertain** — candidates: Factory, Amp, Charm ecosystem, or a Claw variant | **Low** | Do not claim without screenshot match |
| Lobster / claw motif | **OpenClaw** and forks (**NemoClaw**, **NanoClaw**, **PicoClaw**, **IronClaw**, **ZeroClaw**, **NullClaw**, etc.) | **High** for family; **Medium** for which variant | Ecosystem exploded 2025–2026 |
| Anthropic-adjacent orange/black terminal brand | **Claude Code** | **Medium–High** if present but unnamed on some charts | Often missing from community “OSS” grids |
| OpenAI black/white terminal mark | **Codex CLI** | **Medium–High** | Same |
| Charm / bubble-tea aesthetic | **Crush** | **Medium** | Distinctive TUI branding |
| Cursor arrow / IDE mark | **Cursor** | **High** if present | Usually labeled |

**Tier-list chart sources (to help ID logos):** No single canonical “official” chart found. Useful inventories that often feed community graphics:

- https://github.com/bradAGI/awesome-cli-coding-agents (110+ CLIs; updated ~2026-08-17)
- https://terminaltrove.com/ai-coding-agents/
- https://ryanalberts.github.io/best-of-Agent-Harnesses/ (160 harnesses; broader than coding-only)
- https://techstackups.com/comparisons/coding-agent-harness-comparison-2026/
- https://www.developersdigest.tech/agent-compare

---

## Missing from image but important (prioritized)

### P0 — Must include for any credible “harness landscape / native eval” (Aug 2026)

| Name | What it is | URL | Category | Why missing hurts |
| --- | --- | --- | --- | --- |
| **Claude Code** | Anthropic’s dominant terminal agent; hooks, subagents, skills, MCP | https://github.com/anthropics/claude-code (docs/tracker) | CLI agent (proprietary) | Market usage leader in many 2026 surveys |
| **OpenAI Codex CLI** | Rust Apache-2.0 local coding agent; ChatGPT-plan auth; strong sandbox narrative | https://github.com/openai/codex | CLI agent | Core lab harness; Terminal-Bench contender |
| **Gemini CLI** → **Antigravity CLI** | Google terminal agent; Gemini CLI EOL folded into Antigravity (~Jun 18, 2026 per multiple reports) | https://github.com/google-gemini/gemini-cli ; Antigravity/`agy` | CLI / agentic IDE | Lab player; status is transitional — verify current binary |
| **Pi** | Minimal MIT harness; 4 tools; highly influential design | https://github.com/earendil-works/pi / https://pi.dev | CLI agent | Often logo-only on charts; huge influence |
| **Cline** | Model-agnostic VS Code/JetBrains + CLI; Plan/Act; parent of Roo/Kilo lineage | https://github.com/cline/cline | IDE + CLI | High token/volume harness in pairing studies |
| **Goose** | Block → Linux Foundation AAIF; MCP-extensible local agent | https://github.com/aaif-goose/goose | CLI / desktop | Foundation-governed neutrality story |
| **Devin** (+ **Devin Desktop** / ex-Windsurf) | Cognition autonomous cloud engineer; Windsurf→Devin Desktop (Jun 2026) | https://devin.ai | Autonomous + IDE | Category-defining autonomy product |
| **Grok Build** | xAI official coding agent / TUI | https://github.com/xai-org/grok-build | CLI agent | Lab entrant rising in mid-2026 rankings |
| **Cursor Background Agents** / Cursor CLI | Async/cloud-style agents inside Cursor + `agent` CLI | https://cursor.com/cli | IDE + CLI | Distinct surface from “chat in editor” |
| **Jules** | Google async cloud coding agent (+ Jules CLI) | https://jules.google | Autonomous / CLI | Async track counterpart to interactive CLIs |

### P1 — Strongly recommended

| Name | What it is | URL | Category |
| --- | --- | --- | --- |
| **Amazon Q Developer CLI** / **Kiro CLI** | AWS agentic terminal / Amazon coding agent surfaces | https://github.com/aws/amazon-q-developer-cli ; Kiro docs | CLI (vendor) |
| **Qwen Code** | Alibaba Qwen official CLI | https://github.com/QwenLM/qwen-code | CLI agent |
| **Kimi CLI** | Moonshot coding CLI + ACP | https://github.com/MoonshotAI/kimi-cli | CLI agent |
| **Mistral Vibe** | Mistral official CLI coding assistant | https://github.com/mistralai/mistral-vibe | CLI agent |
| **Command Code** | “Taste” personalization CLI (ex-Langbase); early product | https://github.com/CommandCodeAI/command-code | CLI agent |
| **Deep Agents Code** | LangChain Deep Agents terminal coding agent | https://github.com/langchain-ai/deepagents | CLI agent |
| **Junie CLI** | JetBrains LLM-agnostic CLI (EAP) | https://junie.jetbrains.com | CLI agent |
| **Open Interpreter** | Local “run code on my machine” agent | https://github.com/OpenInterpreter/open-interpreter | CLI agent |
| **Zed Agent** (ACP) | Editor-native agent driving Claude/Codex/OpenCode over ACP | Zed Industries | IDE agent |
| **Replit Agent** | In-browser full-stack build/deploy agent | https://replit.com | Autonomous / cloud IDE |
| **Bolt.new** / **Lovable** / **v0** | Browser “vibe coding” generators | bolt.new / lovable.dev / v0.dev | Generators (separate track) |

### P2 — Notable / niche / forks / ecosystem

| Name | Notes | Category |
| --- | --- | --- |
| **Claw Code** / **Claurst** / **claw-code-agent** | Clean-room Claude Code rewrites after 2026 source-leak lore | CLI forks |
| **NemoClaw** (NVIDIA) | Security-hardened OpenClaw stack | Personal + infra |
| **NanoClaw / PicoClaw / IronClaw / ZeroClaw / NullClaw** | OpenClaw-inspired variants | Personal runtimes |
| **Oh My OpenAgent** / **OH-MY-PI** | Meta-layers over OpenCode/Pi/Codex | Meta-harness |
| **Codewhale**, **jcode**, **Prime Agent**, **Nanocoder**, **fx (Vercel)** | Active mid-tier CLIs on Terminal Trove / awesome lists | CLI |
| **Poolside Agent CLI**, **IBM Bob**, **Rovo Dev CLI**, **Snowflake Cortex CLI**, **Qoder CLI** | Vendor/enterprise CLIs | CLI (vendor) |
| **Sourcegraph Cody** | Now **enterprise-only**; agentic focus moved to **Amp** — include only if enterprise track | IDE (legacy consumer) |
| **Symphony** (OpenAI) | Issue-tracker → autonomous Codex runs | Orchestrator |

### P3 — Orchestrators (usually **not** the unit under “native harness” eval)

Orca, Multica, herdr, vibe-kanban, cmux, agent-of-empires, Claude Squad, Omnigent, ralph-tui, Traycer, etc. — they **run** harnesses in parallel. Evaluate as infrastructure, or fix the underlying CLI as the SUT.

---

## Compact master checklist (image ∩ research)

**In image and verified:** Hermes Agent, Amp, OpenClaw, Reasonix, Kilo Code CLI, Droid, Cursor, Continue, Tau, CodeMachine, SWE-agent, Free Code, g3, QQCode, Neovate, picocode, Keen Code, Letta Code, Tabnine CLI, LettaBot, Mentat CLI, Ante, Zap, Every Code, Octomind, Plandex, OpenSquilla, nori-cli, Kode CLI, MiMo Code, Trae Agent, Codel, Crush, Smelt, Clif Code, FetchCoder, cursor-agent, GitHub Copilot, AutoBE, Agentless, RA.Aid, OpenCode, OpenHands, Groq Code CLI, Codebuff, open-codex, Devon, aider, Warp, Roo Code, Claude Engineer, ForgeCode, Auggie, Dexto, VT Code (+ Claw ecosystem).

**Unverified from image:** Soulforge, Aizen.

**Critical missing from image:** Claude Code, Codex CLI, Gemini CLI / Antigravity, Pi, Cline, Goose, Devin (+ Desktop), Grok Build, Jules, Amazon Q/Kiro, Qwen Code, Kimi CLI, Mistral Vibe, Command Code, Cursor Background Agents / Cursor CLI as named surfaces.

---

## Sources / URLs

### Curated inventories
- https://github.com/bradAGI/awesome-cli-coding-agents
- https://terminaltrove.com/ai-coding-agents/
- https://ryanalberts.github.io/best-of-Agent-Harnesses/ · https://github.com/RyanAlberts/best-of-Agent-Harnesses
- https://www.developersdigest.tech/agent-compare

### Comparisons / landscape articles (2026)
- https://techstackups.com/comparisons/coding-agent-harness-comparison-2026/
- https://ofox.ai/blog/best-ai-coding-agent-harness-model-pairing-2026/
- https://winder.ai/ai-agent-harness-comparison/
- https://blog.houseoffoss.com/post/best-open-source-cli-coding-agents-in-2026
- https://dreaming.press/posts/ai-coding-agent-ranking-2026.html
- https://mightybot.ai/blog/coding-ai-agents-for-accelerating-engineering-workflows/
- https://nimbalyst.com/blog/best-ai-coding-agents-2026/
- https://www.firecrawl.dev/blog/best-ai-coding-agents
- https://amux.io/blog/best-terminal-ai-coding-agents-2026/
- https://www.morphllm.com/ai-coding-agent
- https://dev.to/soulentheo/coding-clis-in-mid-2026-the-engineers-map-and-what-changed-in-30-days-23p4
- https://pinggy.io/blog/top_cli_based_ai_coding_agents/
- https://github.com/ianhxu/agentic-engineering-field-study/blob/main/07-tools-ecosystem.md

### Canonical product repos / homes (sample)
- Claude Code tracker: https://github.com/anthropics/claude-code
- Codex CLI: https://github.com/openai/codex
- Gemini CLI: https://github.com/google-gemini/gemini-cli
- OpenCode: https://github.com/anomalyco/opencode
- Pi: https://github.com/earendil-works/pi
- Aider: https://github.com/Aider-AI/aider
- Cline: https://github.com/cline/cline
- Goose: https://github.com/aaif-goose/goose
- Crush: https://github.com/charmbracelet/crush
- Kilo: https://kilo.ai · https://github.com/Kilo-Org/kilocode
- OpenClaw: https://github.com/openclaw/openclaw
- Hermes: https://github.com/NousResearch/hermes-agent
- Factory / Droid: https://factory.ai
- Amp: https://sourcegraph.com/amp
- Devin: https://devin.ai
- AutoBE: https://autobe.dev · https://github.com/wrtnlabs/autobe

---

## Practical next steps for the GitHub research project

1. **Freeze an inclusion rubric** (local CLI with file+shell tools; optional separate tracks: IDE, cloud-autonomous, vibe-generators, personal-agents).
2. **Seed v1 eval set (≈15–25):** Claude Code, Codex CLI, OpenCode, Pi, Aider, Cline, Goose, Crush, Reasonix, Kilo CLI, Amp, Factory Droid, Cursor (Composer + CLI), Gemini/Antigravity, Grok Build — plus 2–3 BYOK dark horses (Tau, Smelt, ForgeCode).
3. **Hold model constant** where possible; report lab-locked systems as (harness × default model).
4. **Use Terminal-Bench / SWE-bench-style tasks** rather than vibe rankings; community tier lists are discovery aids, not metrics.
5. **Re-verify EOL/rebrands** before publishing: Gemini→Antigravity, Windsurf→Devin Desktop, Roo upstream status, Cody consumer sunset, Amp CLI-only pivot.
