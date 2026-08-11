# The Complete Agent Flow

How this Hermes agent actually works — end to end, from the real setup. Every
number here is measured from the live installation (skills, MCP servers, hooks,
scripts), not invented.

```
┌──────────────────────────────  LIFECYCLE  ──────────────────────────────┐
│                                                                          │
│  session:start          agent works        agent:end          scheduled  │
│  ─────────────          ───────────        ─────────          ────────   │
│  mem0 loader    ──►     SOUL + 147   ──►   auto-verify  ──►  memory      │
│  (recall into            skills + 7        + taste-summary  consolidation│
│   fresh prompt)          MCP tools                              + sync    │
│                                                                          │
│  ◄──── remember ────────► act ──────────► verify ─────────► learn ────┐  │
│                                                                          │
└────────────────── every session starts smarter ────────────────────────┘
```

---

## The stack (measured, not invented)

| Layer | What it really is |
|---|---|
| **Skills** | **147 skills** across 16 directories (root + 15 categories), incl. 6 security skills, design/taste suite, orchestration, mem0 |
| **Memory** | mem0 (PostgreSQL + pgvector, port 5433) + built-in `MEMORY.md`/`USER.md` |
| **MCP servers** | **7 enabled**: `github`, `chrome-devtools`, `postgres`, `firecrawl`, `memory`, `context7`, `sequential-thinking` |
| **Hooks** | `mem0-session-loader` (session:start), `auto-verify` + `taste-summary` (agent:end) |
| **Self-improvement** | memory consolidation + skill curation (native curator) |

---

## Phase 0 — Recall: `session:start`

**What runs:** [`hooks/mem0-session-loader/handler.py`](hooks/mem0-session-loader/handler.py)

The gateway fires `session:start` **before** the new session's prompt is built.
The hook:
1. Queries mem0 (broad query across topics) for relevant prior memories.
2. Strips any old recall block, then **writes a fresh `# Mem0 Recall` block into
   `MEMORY.md`** — idempotent (never accumulates), size-capped (trims to top 3
   past ~3600 chars).
3. Hermes' `load_from_disk()` snapshots that block into the fresh system prompt.

**Why it must write to disk:** the gateway discards hook return values, so the
hook can't hand memory back as data — it writes `MEMORY.md` that
`load_from_disk()` picks up. It uses Hermes' atomic writer so it never races the
built-in memory tool on the same file.

**Result:** the fresh agent *remembers* prior work it never saw.

---

## Phase 1 — Act: the agent works

**Driving data:** [`soul/asep.md`](soul/asep.md) (SOUL) + **147 skills** + **7 MCP tools**.

The SOUL defines *who* the agent is and *how* it works (plan big work first,
verify before claiming, honest on failure, kill specific processes only, respect
running services). Skills give it *how to do things*; MCP tools give it *hands*.

### The tool & skill surface

- **7 MCP servers** extend it: GitHub (repos/PRs), chrome-devtools (browser),
  postgres (SQL), firecrawl (web scrape/search), memory (knowledge graph),
  context7 (up-to-date docs), sequential-thinking (structured reasoning).
- **147 skills** are loaded on demand when relevant — the agent scans them before
  acting and loads the matching one.

### Example — orchestrated coding (agy)
One real workflow the agent runs: coordinate Agy agents
(`autonomous-ai-agents/agy-coordinator`):
```
PLAN (orchestrator --print → plan.md) → user ACC → EXECUTE → verify mandiri
```

### Example — AI website judging
`software-development/ai-website-judge` + `devops/skillarena-judge-ops`: a
Playwright crawler + vision-LLM judges websites automatically. This is a
full multi-stage pipeline (SPA discovery, per-page crawl, post-auth sweep,
mobile routes, budget).

---

## Phase 2 — Verify: `agent:end`

**What runs:** [`hooks/auto-verify/handler.py`](hooks/auto-verify/handler.py) +
[`hooks/taste-summary/`](hooks/taste-summary/).

The auto-verify hook is **adaptive**: it auto-discovers projects (git repos on
disk + the collector's services), detects which project(s) the task message
references, and verifies only those — plus a concise overall (repo clean,
service up, recent-error scan). It only fires when **four guards** pass —
otherwise silent:

| Guard | Checks |
|---|---|
| 1. Task detection | message is real work (`beresin`, `fix`, `deploy`) |
| 2. Claim detection | reply claims done (`ok`, `selesai`, `fixed`) |
| 3. Length | reply ≥80 chars |
| 4. Cooldown | ≤1 check per 5 min |

Then, **per detected project**: repo clean? (`git status`) + service up?
(`curl` HTTP). Plus a concise overall (recent-error log scan, noise-filtered).
Backed by **real behavior tests** (offline, deterministic — see
[`tests/`](tests/)).

```txt
🧾 Auto-Verify · "gas beresin bug css di site-checker"
✅ Repo bersih
✅ site-checker UP
⚠️ the-app down (dev-only, expected)
✅ Log bersih
**⚠️ ada yang perlu dicek**
```

`taste-summary` posts the approach + confidence. Together they enforce honesty
architecturally, regardless of which model is running.

---

## Phase 3 — Learn: memory consolidation & skill curation

### Memory consolidation
The `consolidate-memory.py` machinery (see `mem0-integration` skill) extracts
durable facts from sessions and syncs them to mem0 — with **strict noise
filtering**: it must NOT store raw chat, image descriptions, background-process
artifacts, API keys, model-switch notes, or prompt-test dumps. A daily
`mem0_auto_cleanup.py` backstop sweeps duplicates and leaks.

Documented pollution classes (all real, all cleaned): image descriptions,
background-process artifacts, raw casual chat, stale status facts, duplicate
snapshots, leaked API keys, model-switch notes, prompt-test artifacts,
tool-iteration errors, paste-dumps.

### Skill curation (native curator)
Hermes ships a native **curator** that tracks skill usage, marks idle skills
stale, archives stale ones (never deletes), and backs them up. The user's own
curation rule: **skills must be class-level** (a recurring pattern), never a
one-off whim — a skill born from a single task is deleted.

---

## Use cases

### A — pick up yesterday's work
```
Yesterday: fixed checkout bug, committed.
Today: new session → mem0 recall includes "checkout fixed, 3 files".
  Agent already has context; picks up without re-asking.
```

### B — orchestrated multi-agent build
```
owner: "kirim ke agy orchestrator untuk refactor"
  PLAN → user ACC → parallel EXECUTE → verify
  (autonomous-ai-agents/agy-coordinator)
```

### C — web research with tools
```
owner: "coba riset topik X"
  loads firecrawl + research skills, gathers real sources,
  returns a cited, honest summary.
```

### D — the overclaim catch
```
agent: "oke udah fix, deploy sukses"
  auto-verify → ⚠️ Repo dirty (3 files uncommitted)
  owner sees it immediately instead of discovering later.
```

### E — agent patches its own memory
```
The agent learns a durable fact → consolidation extracts it to mem0.
  Next session recalls it (Phase 0). Memory survives across sessions.
```

---

## What can go wrong (and where it's caught)

| Failure mode | Caught at |
|---|---|
| agent claims done, repo dirty | auto-verify → ⚠️ Repo dirty |
| agent says deployed, service down | auto-verify → ⚠️ HTTP status |
| agent left a real error in the log | auto-verify → ⚠️ Recent ERROR |
| agent "forgets" last session | mem0 loader → recall injected |
| mem0 polluted with noise/secrets | consolidation filters + auto-cleanup sweeps |
| skill library grows stale | native curator archives stale skills |

---

## Reference map

| Phase | Docs | Source |
|---|---|---|
| 0. Recall | [`patterns/memory.md`](patterns/memory.md) | `hooks/mem0-session-loader/handler.py` |
| 1. Act | [`soul/asep.md`](soul/asep.md), [`skills/index.md`](skills/index.md) | SOUL + skills + MCP |
| 2. Verify | [`patterns/verification.md`](patterns/verification.md) | `hooks/auto-verify/handler.py` |
| 3. Learn | `mem0-integration` skill, curator | `consolidate-memory.py`, curator |

See also: [`examples/task-flow.md`](examples/task-flow.md),
[`examples/hook-event-map.md`](examples/hook-event-map.md),
[`docs/architecture.md`](docs/architecture.md).