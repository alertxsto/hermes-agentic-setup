# The Self-Improving Loop

The distinguishing feature of a great agent: it **gets smarter over time**. This
is a closed loop of act → record → review → improve.

```
   ACT ──► RECORD ──► REVIEW ──► IMPROVE ──► (next ACT is smarter)
    │         │          │           │
 done real   sessions   a daily     patch skills /
  work       + git      cron reads  note gaps
                       the record
```

## Step 1 — ACT
The agent does real work: git commits, builds, research. This generates the raw
material (git history, session transcripts) that will be reviewed later.

## Step 2 — RECORD
- **Git** preserves what code changed.
- **Sessions** preserve the reasoning and decisions.

Both are ground truth, not imagination.

## Step 3 — REVIEW (the daily briefing cron)
Every morning a cron reads the last 24h:
1. Telemetry collector → `git log` per repo, dirty WIP, service status.
2. Session search → what was actually worked on.
3. Skill scan → what the library has and where it's thin.

Then it produces a structured briefing with **concrete, actionable suggestions**:

```
☀️ DAILY BRIEFING — Selasa, 11 Agu

**KEMAREN**      # real work rekap (git + sessions)
**HARI INI**     # concrete next actions
**SARAN (AGENTIC + SELF-IMPROVING)**
  [P1] concrete task — exact command, "tinggal bilang gas"
  [P2] skill/knowledge gap the agent should fill
  [P3] broken tooling to fix
```

## Step 4 — IMPROVE (the key part)
The briefing isn't just advisory — it's **allowed to act**. It can:
- **Patch skills** — add a lesson, fix a wrong command, merge overlapping
  sections (via the skill tools).
- **Update pattern docs** — encode today's lesson for tomorrow.
- **Fix tooling** — e.g. stale repo lists in the telemetry collector.

This is a **verified, real loop**: briefings have autonomously updated the cron
operations skill and deduplicated sections.

## Why it matters

> Most "agents" are stateless: every session starts from zero. The
> self-improving loop makes each session the *inheritor* of every previous one.
> That compounding is the difference between a tool and a partner.