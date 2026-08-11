# Mem0 Auto-Cleanup Cron

**Problem it solves:** semantic memory stores (mem0) accumulate **noise,
duplicates, and leaked secrets** over time. Left alone, recall quality degrades
and the store fills with junk.

**Approach: conservative cleanup.** We only delete what is unambiguously junk —
never good facts:

- **Content-identical duplicates** (exact match).
- **Obvious noise** — raw chat fragments, cron artifacts, test prompts.
- **Leaked secrets** — API keys, credentials that accidentally landed in memory
  (must be removed immediately).

We **preserve** everything that looks like a real, useful fact about the user,
projects, or environment.

## How it runs

A daily cron (e.g. 04:00) runs a script that:
1. Queries the mem0 store.
2. Classifies each entry (keep / delete).
3. Deletes only the junk bucket.
4. Logs every deletion to an audit file for transparency.

```
[2026-08-11T17:39:26] total=25 deleted=6 failed=0
```

## Design decisions

- **Dedup is strong** — exact-match + 80% overlap detection.
- **Age-aware** — stale noise is dropped, but durable facts are kept.
- **Auditable** — every removal is logged, so nothing is destroyed silently.
- **Scheduled low traffic** — runs in the quiet hours.

## Companion

Pairs with the [`mem0-session-loader`](../hooks/mem0-session-loader/README.md)
hook: one injects memory, the other keeps that memory healthy. Together they
make a memory system that grows *and* stays clean.