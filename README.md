# 🤖 Hermes Agentic Setup

> **A production-grade, self-improving AI agent** — a full 1:1 of a real,
> working Hermes Agent deployment. Not a toy, not a demo. This is the actual
> architecture: personality, memory, verification hooks, self-running cron, and
> a loop that makes the agent smarter every day.
>
> Built on [Hermes Agent](https://hermes-agent.nousresearch.com/docs) by
> Nous Research · [Apache-2.0](LICENSE)

---

## 🧭 What this is

A long-lived personal AI agent used daily for real work (coding, ops, research).
The whole point is **compounding**: every session inherits memory and skills from
every session before it, so the agent gets *measurably* better over time.

Concretely, this setup runs:

- **8 scheduled cron jobs** — including a self-improving daily briefing
- **7 MCP servers** — GitHub, chrome-devtools, postgres, firecrawl, memory,
  context7, sequential-thinking
- **3 event hooks** — memory loader, auto-verify, taste summary
- **~147 curated skills** — class-level, merged from 163 overlapping ones
- **1 clean model default + 2-tier fallback chain**
- **Semantic memory** via mem0 (PostgreSQL + pgvector)

---

## 🧩 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        HERMES GATEWAY                             │
│   Telegram · Discord · Webhook   —  event bus for hooks           │
└───────────────┬────────────────────────────┬──────────────────────┘
                │ session:start              │  agent:end
                ▼                            ▼
     ┌──────────────────┐          ┌──────────────────────┐
     │  MEM0 LOADER      │          │  AUTO-VERIFY         │
     │  semantic memory  │          │  (anti-overclaim)    │
     │  → MEMORY.md      │          │  git · services ·    │
     │  recall block     │          │  log scan            │
     └──────────────────┘          └──────────┬───────────┘
                                              │
     ┌──────────────────┐          ┌──────────▼───────────┐
     │  TASTE SUMMARY    │          │  SELF-IMPROVING      │
     │  (agent:end)      │  ─────►  │  DAILY BRIEFING      │
     │  taste+confidence │          │  cron 07:00          │
     └──────────────────┘          │  → patches skills    │
                                   └──────────────────────┘
```

**The core loop (act → record → review → improve):**

1. **Persist** — `session:start` fires the mem0 loader, which injects relevant
   semantic memories into the fresh session's system prompt.
2. **Act** — the agent works using its SOUL, ~147 skills, and 7 MCP servers.
3. **Verify** — on `agent:end`, the auto-verify hook runs deterministic checks
   (repo clean? service up? recent errors?) whenever the agent claims "done".
4. **Learn** — every morning the daily-briefing cron reads the last 24h of real
   work, finds gaps, and **patches its own skills**.

---

## ⚙️ Model Routing

One clean default, an explicit fallback chain, no chaos.

```
Primary:   cline-pass/deepseek-v4-flash   (via cline — free, doesn't burn quota)
Fallback1: cline-pass/glm-5.2             (stronger, same provider)
Fallback2: cline-pass/kimi-k2.7-code      (specialist, same provider)
```

- **DeepSeek V4 Flash 0731** is the daily driver — official release build, ~Opus
  4.6-level agentic benchmarks at flash prices (Terminal-Bench 82.7, DeepSWE
  +645% over preview).
- **One provider** (ClinePass) for the whole chain — no cross-provider fallback
  that adds cost/copies.
- **9Router stays as a manual pick** tool, cleanly synced (not the silent default).

> Full rationale + gotchas in [`patterns/model-routing.md`](patterns/model-routing.md).

---

## 🧠 Memory

Three layers, each with a job:

| Layer | What lives here | Filled by |
|---|---|---|
| `MEMORY.md` (system prompt) | compact, always-present facts | session start |
| **mem0** (pgvector) | durable semantic facts | session start + as needed |
| **skills/** | procedural knowledge | when a workflow is learned |

- `mem0-session-loader` hook writes a `# Mem0 Recall` block into `MEMORY.md` on
  `session:start`, so the fresh agent "remembers" what it never saw.
- `Mem0 Auto Cleanup` cron (04:00) keeps the store healthy — conservative
  dedup, noise removal, secret-leak scrubbing. Never deletes good facts.

> [`patterns/memory.md`](patterns/memory.md) · [`hooks/mem0-session-loader/`](hooks/mem0-session-loader/) · [`cron/scripts/mem0_auto_cleanup.py`](cron/scripts/mem0_auto_cleanup.py)

---

## 🪝 Hooks

| Hook | Event | What it does |
|---|---|---|
| `mem0-session-loader` | `session:start/reset` | inject semantic memory into the fresh prompt |
| `auto-verify` | `agent:end` | verify "done" claims: git clean, service up, log scan → Telegram verdict |
| `taste-summary` | `agent:end` | post taste + confidence (like Command Code) |

The **auto-verify** hook is the anti-overclaim guarantee. It fires only for real
tasks with a completion claim, respects a 5-min cooldown, and skips `# dev-only`
services (an Expo dev server isn't expected to run 24/7).

```
🧾 Auto-Verify · "gas beresin bug css site-checker"
✅ Repo bersih
✅ site-checker UP
⚠️ the-app down (dev-only, expected)
✅ Log bersih
**⚠️ ada yang perlu dicek**
```

> [`examples/hook-event-map.md`](examples/hook-event-map.md) · [`hooks/auto-verify/`](hooks/auto-verify/)

---

## ⏰ Cron Jobs (8)

| Job | Schedule | Deliver | Type |
|---|---|---|---|
| **Daily Briefing** | 07:00 daily | telegram | agent — **self-improving** |
| Memory Consolidation | every 6h | local | script |
| Session Archive | 02:00 daily | local | script |
| Git Sync Hermes Config | every 60m | local | script |
| OSS Good First Issue Hunter | 08:00 daily | telegram | script |
| Power & Cost Monitor | every 60m | local | script |
| Weekly Power Cost Summary | Mon 09:00 | telegram | script |
| Mem0 Auto Cleanup | 04:00 daily | local | script |

### The crown jewel: Daily Briefing (self-improving loop)

Every morning at 07:00 it:
1. Runs the telemetry collector (`cron/scripts/work_prep_collector.sh`) — real
   `git log` 24h per repo, dirty WIP, service status.
2. Reads recent sessions (session search).
3. Scans the skill library.
4. Produces a structured briefing with concrete suggestions.
5. **Patches its own skills** with the day's lessons.

This is a *verified, real* loop — the briefing has autonomously updated the cron
ops skill and deduplicated overlapping sections.

> [`cron/daily-briefing.md`](cron/daily-briefing.md) · [`cron/scripts/work_prep_collector.sh`](cron/scripts/work_prep_collector.sh) · [`patterns/self-improving.md`](patterns/self-improving.md)

---

## 🧩 Skills

- **~147 skills**, curated down from 163 by merging 11 overlapping groups into
  class-level umbrellas.
- **Rule:** skills are class-level, not one-off. A skill from a single whim is
  clutter and gets removed.
- Arranged by category (creativity, devops, github, mlops, security,
  software-development, taste, …).

> [`skills/index.md`](skills/index.md) · [`patterns/skill-curation.md`](patterns/skill-curation.md)

---

## 🔌 MCP Servers (7)

| Server | Purpose |
|---|---|
| `github` | repos, PRs, issues |
| `chrome-devtools` | browser automation |
| `postgres` | read-only SQL |
| `firecrawl` | web scraping/crawl/search |
| `memory` | knowledge graph |
| `context7` | up-to-date library docs |
| `sequential-thinking` | structured multi-step reasoning |

---

## 🧭 End-to-End Flow

See [`examples/task-flow.md`](examples/task-flow.md) for the full walkthrough.
Short version:

```
owner: "gas beresin bug css di site-checker"
  session:start ──► mem0 recall injected
  agent works ────► SOUL + skills + MCP
  agent:end ──────► auto-verify verdict + taste summary
  07:00 next day ─► briefing reads git log, patches skills
  next session ───► is smarter
```

---

## 🚀 Build your own

- [`docs/setup-guide.md`](docs/setup-guide.md) — step-by-step
- [`TEMPLATES/`](TEMPLATES/) — SOUL, HOOK, CRON starting points
- [`docs/lessons.md`](docs/lessons.md) — hard-won pitfalls

---

## 📜 License

[Apache-2.0](LICENSE) — open source, patent-safe, attribution-friendly.