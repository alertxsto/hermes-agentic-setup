# Memory Architecture

Long-lived agents need memory that survives across sessions. This covers the
three-layer memory system.

## The problem

A fresh agent session has a **frozen system prompt** — it can't remember work
from yesterday. You need durable memory, but it can't grow forever.

## The three layers

| Layer | What | Update | Cost |
|---|---|---|---|
| **System prompt memory** | compact `MEMORY.md` / `USER.md` | on session start | injected every turn |
| **Semantic store** | mem0 (PostgreSQL + pgvector) | on session start / as facts change | queried by relevance |
| **Skill library** | procedural knowledge | when a workflow is learned | loaded on demand |

### 1. System prompt memory (`MEMORY.md`)
- Compact, high-signal facts that must be present every turn.
- Kept well-formed (bare `§` separators) and **size-capped** — a nearly-full
  store rejects new facts.
- Rule: *if a fact will be stale in a week, it doesn't belong here.*

### 2. Semantic store (mem0)
- Durable facts that don't fit the compact prompt.
- **Injected on `session:start`** via a hook (see
  `hooks/mem0-session-loader`) — it writes a recall block into `MEMORY.md`
  before the session's system prompt is built.
- Vector search (pgvector) + dedup (exact + 80% overlap).

### 3. Skill library
- Procedural memory: *how to do X*, not *what user prefers*.
- See `patterns/skill-curation.md`.

## Keep it healthy

- **Conservative cleanup** (daily cron) — delete only exact duplicates, obvious
  noise, and leaked secrets. Never good facts.
- **Audit every removal** — log it; nothing destroyed silently.
- **Dedup is strong** — exact match + 80% overlap.

## Design rule

> Prefer storing durable user *preferences* and *environment facts* over
> procedural steps (those go in skills) or transient state (that goes nowhere).