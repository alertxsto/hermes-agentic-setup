# Mem0 Session Loader

**Problem it solves:** an agent's frozen system prompt can't grow forever — but
long-lived agents need to *remember* context across sessions. Semantic memory
must be injected into each fresh session.

**When it fires:** on `session:start` / `session:reset` — *before* the new
session's system prompt is built.

**What it does:**
1. Queries a **mem0 vector store** (PostgreSQL + pgvector) for memories relevant
   to the current context.
2. **Writes a recall block into `MEMORY.md`** on session start.
3. Hermes' `MemoryStore.load_from_disk()` then snapshots that block into the
   fresh session's system prompt — so the new agent "remembers" what it never
   actually saw.
4. Keeps `MEMORY.md` well-formed (bare `§` separators) and size-capped so the
   memory tool keeps round-tripping cleanly.

**Key mechanism (verified against Hermes source):** the hook's return value is
discarded by the gateway (`emit()` swallows results), so injection *must* happen
by writing state to disk that `load_from_disk()` picks up — not by returning
data. This is the subtle bit that makes the pattern work.

**Atomic write (race-safety):** `MEMORY.md` is *also* written by Hermes' built-in
memory tool, so this hook reuses Hermes' own `atomic_write_text` (temp file +
fsync + atomic rename) instead of a bare `write_text`. That prevents a
lost-update / partial-write race when both writers hit the file near-simultaneously.

## Outcome

Each session starts with a `# Mem0 Recall (auto, session start)` section already
in context — the agent has working knowledge of past work without manual note
hand-off.

## Note: native Hermes memory

Hermes ships built-in memory providers (`hermes memory`: mem0, byterover, …) and
an auto-curator for skills. **Prefer the native path where it fits.** This hook
exists for the specific case of *injecting a semantic recall block into
`MEMORY.md` at `session:start`*; if your Hermes version already auto-injects
provider memory into the system prompt, use that and drop this hook to avoid
duplicate writes. Check `hermes memory status` for what your version does.

## Companion: mem0 auto-cleanup

Memory stores accumulate noise and duplicates over time. Run a **conservative**
cleanup on a schedule (content-identical dedup, obvious noise, leaked secrets)
while preserving good facts. Durable facts are never deleted.