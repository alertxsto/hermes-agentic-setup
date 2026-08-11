# End-to-End Task Flow

A concrete, line-by-line walkthrough of everything that happens when the owner
sends a task. Tie it to the actual hook sources — every step described here is a
real, deterministic mechanism.

## Scenario: `gas beresin bug css di site-checker`

### Step 1 — Memory injection (`session:start`)

A new session begins. Before its system prompt is built, the gateway fires
`session:start` → `mem0-session-loader`:

```
session:start → mem0-session-loader
  1. query semantic store (mem0) for relevant prior memories
  2. strip any OLD recall block from MEMORY.md  (idempotent — never duplicates)
  3. write a fresh "# Mem0 Recall (auto, session start)" block
       - keeps top 6 items, each ≤150 chars
       - if the file would exceed budget, trims to top 3
  4. Hermes' load_from_disk() snapshots that block into the new system prompt
```

**Net effect:** the fresh agent, which never saw yesterday, "remembers" it.

### Step 2 — The agent works (`SOUL` + skills + tools)

```
owner: "gas beresin bug css di site-checker"
agent: the message matches SOUL's "gas" = execute directive
  → scans & loads the relevant skill(s)
  → follows SOUL operating code: plan big work, verify before claiming, honest
  → edits code, runs build / tests
```

The SOUL's *working principles* govern the behavior here (`soul/asep.md`):
plan first, verify before claiming, honest on failure, specific kills only.

### Step 3 — "Done" gets verified (`agent:end` → auto-verify)

The agent replies `oke udah gw fix dan beres, deploy sukses`. The `agent:end`
event fires `auto-verify`. Its **four guards** must all pass:

```
guard 1  message looks like a real task?   TASK_RE: "beresin" ✓
guard 2  reply claims completion?          CLAIM_RE: "beres " ✓
guard 3  reply is long enough (≥80 chars)? ✓
guard 4  cooldown passed (≤1 per 5 min)?   ✓
```

If any guard fails → the hook does nothing (no spam, no noise). If all pass, it
runs `verify()` — three deterministic checks:

```
1. git clean?    git status --short on active repos
2. service up?   curl HTTP status on listed services
                 (dev-only services SKIPPED when down — expected)
3. log clean?    recent ERROR/CRITICAL in agent.log (last 2h, noise filtered)
```

Then it posts a verdict:

```txt
🧾 Auto-Verify · "gas beresin bug css di site-checker"
✅ Repo bersih
✅ site-checker UP
⚠️ the-app down (dev-only, expected)
✅ Log bersih
**⚠️ ada yang perlu dicek**
```

The key property: this is **architectural**, not a model's mood. It works the
same whether the model is strong or weak.

### Step 4 — Approach signal (`agent:end` → taste-summary)

In the same `agent:end`, `taste-summary` posts a compact taste + confidence
line, so the owner sees *how* the agent approached the task, not just that it
finished.

### Step 5 — Learning (`scheduled review`)

Later, a scheduled review runs (the self-improving loop):

```
[scheduled review]
  → reads real git log: sees the css-fix commit  (ground truth)
  → reads recent sessions: the work that was done
  → scans the skill library: a skill exists, could improve
  → proposes: [P1] next concrete task · [P2] skill gap · [P3] tooling fix
  → PATCHES skills with today's lessons
```

## Full timeline

```
T0      session:start    → mem0 recall injected into the fresh prompt
T0+1    agent does work  → SOUL + skills + MCP tools
T1      agent:end        → auto-verify verdict + taste-summary
T2      owner reads verdict, acts
...
T+N     scheduled review → reads real git log, patches skills
T+N+1   next session     → is smarter (inherits yesterday)
```

## Key insight

Every step is **deterministic when it should be** (memory injection,
verification, cooldown) and **autonomous when it should be** (skill patching).
The human stays in the loop at the decision points, not the mechanics.

## What CAN go wrong (and is caught)

| Failure mode | Where it's caught |
|---|---|
| agent claims "done" but repo is dirty | auto-verify → ⚠️ Repo dirty |
| agent says deployed but service is down | auto-verify → ⚠️ HTTP status |
| agent left a real error in the log | auto-verify → ⚠️ Recent ERROR |
| agent "forgets" last session | mem0 loader → recalls prior context |
| skill library grows stale | scheduled review → patches skills |