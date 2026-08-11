# Memory Architecture

Long-lived agents need memory that survives across sessions. This covers the
three-layer memory system and the exact mechanism that injects it.

## The problem

A fresh agent session has a **frozen system prompt** — it literally cannot
remember work from yesterday. To be useful long-term, an agent needs durable
memory that gets into that frozen prompt. But the prompt can't grow forever.

## The three layers

| Layer | What lives here | Update | Cost |
|---|---|---|---|
| **System prompt memory** | compact `MEMORY.md` / `USER.md` | on session start | injected every turn |
| **Semantic store** | mem0 (PostgreSQL + pgvector) | on session start / as facts change | queried by relevance |
| **Skill library** | procedural knowledge (*how to do X*) | when a workflow is learned | loaded on demand |

### 1. System prompt memory (`MEMORY.md`)

- Compact, high-signal facts that must be present every turn.
- Kept well-formed (bare `§` separators) and **size-capped** — a nearly-full
  store rejects new facts.
- Rule: *if a fact will be stale in a week, it doesn't belong here.*

### 2. Semantic store (mem0)

- Durable facts that don't fit the compact prompt.
- Vector search (pgvector). Injected on `session:start` (below).

### 3. Skill library

- Procedural memory: *how to do X*, not *what the user prefers*.
- See `patterns/skill-curation.md`.

## The injection mechanism (mem0 loader)

`hooks/mem0-session-loader/handler.py` runs on `session:start`. In detail:

1. **Query** the semantic store for relevant memories (a broad query across
   topics, limit 8).
2. **Strip** any *old* recall block from `MEMORY.md` — idempotent, so repeated
   runs never accumulate duplicates.
3. **Write** a fresh recall block:
   - keeps the **top 6** items, each capped at **150 chars**;
   - if the file would exceed its budget (~3600 chars), trims to **top 3**.
4. Hermes' `MemoryStore.load_from_disk()` snapshots that block into the new
   session's system prompt.

The subtle constraint: the gateway **discards hook return values**, so the hook
can't hand memory back as data — it must **write to disk** (`MEMORY.md`) that
`load_from_disk()` will pick up. That's why it edits the file.

## Keep it healthy

- **Cleanup is conservative** — delete only exact duplicates, obvious noise, and
  leaked secrets. Never good facts.
- **Audit every removal** — log it; nothing destroyed silently.
- **Dedup is strong** — exact match + overlap detection.

## Design rules

- Durable **preferences** and **environment facts** belong in memory.
- **Procedural steps** belong in skills (not memory).
- **Transient state** belongs nowhere.
- **Idempotency** — any repeated write must not accumulate (strip first).