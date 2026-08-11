# 🤖 Hermes Agentic Setup

> **A production-grade, self-improving AI agent.**  
> Architecture, hooks, and self-improving workflows for a long-lived coding/ops
> agent built on [Hermes Agent](https://hermes-agent.nousresearch.com/docs) by Nous Research.

This repo is a **curated showcase** of how a production Hermes agent is
architected for real, long-term use: a defined operating system, semantic memory
that survives across sessions, verification hooks that enforce honest "done"
claims, and a daily briefing loop that patches its own skills.

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
├── README.md            # architecture + showcase overview
├── LICENSE              # Apache-2.0
├── .gitignore
├── soul/                # the agent's identity & operating principles
│   └── asep.md
├── hooks/               # event-driven extensions
│   ├── auto-verify/         # anti-overclaim verification (handler + docs)
│   ├── mem0-session-loader/ # semantic memory recall
│   └── taste-summary/       # taste + confidence summary
├── cron/                # scheduled self-improving workflows
│   ├── daily-briefing.md
│   ├── mem0-auto-cleanup.md
│   └── scripts/             # REAL, adaptable scripts
│       ├── work_prep_collector.sh
│       └── mem0_auto_cleanup.py
├── patterns/            # reusable recipes
│   ├── skill-curation.md
│   ├── model-routing.md
│   ├── memory.md
│   ├── verification.md
│   └── self-improving.md
├── examples/            # end-to-end walkthroughs
│   ├── task-flow.md
│   └── hook-event-map.md
├── skills/              # how the skill library is curated
│   └── index.md
├── docs/                # architecture + lessons + setup
│   ├── architecture.md
│   ├── lessons.md
│   └── setup-guide.md
└── TEMPLATES/           # starting points for your own setup
    ├── SOUL.TEMPLATE.md
    ├── HOOK.TEMPLATE.yaml
    └── CRON.TEMPLATE.md
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
- [`docs/setup-guide.md`](docs/setup-guide.md) — step-by-step to build your own
- [`examples/task-flow.md`](examples/task-flow.md) — what happens end-to-end
- [`soul/asep.md`](soul/asep.md) — an example agent identity
- [`hooks/auto-verify/`](hooks/auto-verify/) — a ready-to-adapt verification hook
- [`cron/scripts/`](cron/scripts/) — real, adaptable collector + cleanup scripts
- [`TEMPLATES/`](TEMPLATES/) — starting points (SOUL, HOOK, CRON)
- [`docs/lessons.md`](docs/lessons.md) — hard-won pitfalls

---

## 📜 License

[Apache-2.0](LICENSE) — open source, patent-safe, attribution-friendly.
