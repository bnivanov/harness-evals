# Brief — LLM Harness Evaluation

**Status:** Active setup  
**Started:** 2026-08-24  
**Owner:** Bobby Ivanov (+ Harness Reviewer)  
**Publication:** Target `bnivanov/llm-harness-eval` (public), publish pending auth

## Goal

Evaluate **native LLM coding harness performance** — the orchestration layer around models (tool use, repo context, shell/edit loops, permissions, memory, subagents), not the models themselves.

Findings will be published openly on GitHub so others can reproduce, challenge, and extend the work.

## Scope (working)

**In scope**
- Terminal / CLI coding agents
- IDE-embedded agent modes used as primary coding loops
- Open-source and commercial harnesses with a runnable coding workflow
- Head-to-head comparison under controlled tasks (same prompts, same repos, same success criteria)

**Out of scope (for now)**
- Pure chat UIs with no agent loop
- App builders / vibe-coding product generators (Lovable, Bolt, v0) unless later expanded
- Ranking models in isolation (GPT vs Claude vs Gemini without harness)
- Reproducing community tier-list vibes as scientific truth

## Research questions

1. Holding the model fixed (or controlling for it), how much does harness choice change task success, cost, latency, and edit quality?
2. What harness mechanisms (sandbox, MCP, subagents, memory, instruction files, verifiers) correlate with better outcomes?
3. Which harnesses are fair “native” baselines for a given model family?

## Working definition: “harness”

A **coding harness** is software that wraps one or more LLMs with a control loop for repository work: reading files, editing, running commands, managing context/permissions, and deciding when a task is done.

A **runtime / gateway** (e.g. OpenClaw) may orchestrate multiple harnesses; we track those separately.

## Continuity files in this project

| File | Purpose |
|------|---------|
| `BRIEF.md` | Why this exists and what “done” means |
| `STATUS.md` | Current phase and next actions |
| `DECISIONS.md` | Architecture / methodology choices with rationale |
| `LEARNINGS.md` | Durable insights from research and evals |
| `possible-harnesses.md` | Master candidate list |
| `evaluation-log.md` | Running log of what we evaluate and when |
| `research/` | Notes, source dumps, scratch |
| `landscape/` | Ongoing tools map (subscription vs BYOK × surface) — start at `landscape/agentic-tools-subscription-vs-byok.md` |
| `waves/` | Per-wave SUT scope and reviews |
| `assets/` | Screenshots, charts, source images |

## Success for v0

1. Public repo with this structure and a clear README
2. Curated candidate list (image + broader research), with logos resolved or marked uncertain
3. Agreed evaluation protocol (tasks, metrics, controls)
4. At least one pilot eval recorded in `evaluation-log.md`
