# Taste Summary Hook

**Problem it solves:** after real work, the human wants a quick, consistent
signal of *how the agent approached it* (its "taste") and *how confident it is* —
like Command Code's taste display. Keeps the human in the loop without reading
long replies.

**When it fires:** on `agent:end`, only for **real tasks** (same task-detection
as auto-verify) with a sufficiently long response.

**What it does:**
1. Reads the agent's **taste rules** (a shared taste file).
2. On task completion, posts a compact summary:
   - the top N taste rules triggered (with confidence),
   - a clipped snippet of what the agent did.

```
*Taste:*
• Prefer small, reviewable diffs — confidence 0.9
• Never over-engineer — confidence 0.8
▸ refactored auth module into 3 files
```

**Design notes:**
- Shared taste file → taste stays consistent even when the underlying model
  changes or another agent (e.g. a coding CLI) learns new preferences.
- Confidence shown per-rule so the human knows how sure the agent is.

## Why these three hooks together

`mem0-session-loader` (remember) → `auto-verify` (don't lie about done) →
`taste-summary` (show your work). Together they make an agent both **smarter**
and **honest** — the two things that matter most for a long-lived assistant.