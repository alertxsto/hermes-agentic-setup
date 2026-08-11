# 🤖 Hermes Agentic Setup

> **A production-grade personal AI agent that keeps getting smarter.**  
> Architecture, hooks, and self-improving workflows for a long-lived coding/ops
> agent built on [Hermes Agent](https://hermes-agent.nousresearch.com/docs) by Nous Research.

This repo is a **curated showcase** of how a Hermes agent is configured for
real, long-term use: a defined personality, semantic memory that survives across
sessions, verification hooks that stop it from lying about "done", and a daily
briefing loop that actually patches its own skills.

> ⚠️ **No secrets here.** This is the *structure and lessons* — all API keys,
> config files, personal data, and session content are excluded. Everything is a
> documented pattern you can adapt, not the raw `.hermes/` directory.

---

## 🧩 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         HERMES GATEWAY                        │
│  Telegram ↔ Discord ↔ Webhook  ·  event bus for hooks        │
└───────────────┬───────────────────────────┬───────────────────┘
                │ session:start             │ agent:end
                ▼                           ▼
        ┌───────────────┐           ┌───────────────────┐
        │  MEM0 LOADER  │           │    AUTO-VERIFY    │
        │  semantic     │           │  (anti-overclaim) │
        │  memory →     │           │   checks git,     │
        │  system prompt│           │   services, logs  │
        └───────────────┘           └────────┬──────────┘
                                             │
        ┌───────────────┐           ┌────────▼──────────┐
        │ TASTE SUMMARY │           │  SELF-IMPROVING   │
        │  confidence + │  ─────►   │  DAILY BRIEFING   │
        │  taste rules  │           │  cron → patches   │
        └───────────────┘           │  own skills       │
                                    └───────────────────┘
```

**Core loop (agentic & self-improving):**

1. **Persist** — every session injects relevant semantic memories (mem0 + vector store).
2. **Act** — the agent does work using a curated skill library + a defined SOUL.
3. **Verify** — an auto-verify hook runs deterministic checks (repo clean? service
   up? recent errors?) whenever the agent claims a task is "done".
4. **Learn** — a daily-briefing cron reads the last 24h of real work, identifies
   gaps, and **patches its own skills** — the agent literally improves itself.

---

## 📁 Structure

```
hermes-agentic-setup/
├── soul/            # the agent's identity & operating principles (SOUL.md pattern)
├── hooks/           # event-driven extensions (auto-verify, mem0-loader, taste-summary)
├── cron/            # scheduled self-improving workflows (daily briefing, memory cleanup)
├── patterns/        # reusable recipes (skill curation, model routing)
├── skills/          # how the skill library is curated & organized
└── docs/            # architecture + lessons learned
```

---

## 🔥 Highlights

| Pattern | Why it matters |
|---|---|
| **Auto-verify hook** | Agent can't just *say* "done" — it's checked. Deterministic, cheap: `git status` + `curl` service + recent-error scan. Cooldown + dev-only filtering prevent noise. |
| **Mem0 session loader** | Semantic memory injected into the fresh session's system prompt → the agent "remembers" context it never saw. Survives across sessions. |
| **Self-improving briefing** | A daily cron reads real git log + sessions, proposes skill upgrades, and **patches skills autonomously**. |
| **Taste summary** | After each task, a compact taste + confidence line (like Command Code) keeps the human in the loop. |
| **Skill curation** | 163 overlapping skills → 146 curated umbrella skills (class-level, not one-off). |
| **Model routing** | One clean default provider + explicit fallback chain. No chaos, no wasted spend. |

---

## 🚀 Quick start

Each folder is self-documented. Start with:

- [`docs/architecture.md`](docs/architecture.md) — how the pieces fit
- [`soul/asep.md`](soul/asep.md) — an example agent identity
- [`hooks/auto-verify/`](hooks/auto-verify/) — a ready-to-adapt verification hook
- [`docs/lessons.md`](docs/lessons.md) — hard-won pitfalls

---

## 📜 License

[Apache-2.0](LICENSE) — open source, patent-safe, attribution-friendly.
