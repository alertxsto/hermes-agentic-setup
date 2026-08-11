# End-to-End Task Flow

A concrete walkthrough of everything that happens when the owner sends a task.
This ties together SOUL, memory, hooks, and cron.

## Scenario: "gas beresin bug css di site-checker"

### 1. Session start (memory injection)
```
session:start ──► mem0-session-loader hook
                  └─► queries semantic store for relevant context
                  └─► writes "# Mem0 Recall" block into MEMORY.md
                  └─► new session's system prompt includes prior knowledge
```

### 2. Agent works (SOUL + skills)
```
owner: "gas beresin bug css di site-checker"
agent: message matches real-task signal (beresin)
  └─► loads relevant skills (e.g. frontend / site-checker)
  └─► follows SOUL: plan, verify, honest
  └─► edits code, runs build/tests
```

### 3. Agent replies "done" (verification)
```
agent: "oke udah gw fix dan beres, deploy sukses"
agent:end ──► auto-verify hook
  └─► message looks like task ✓
  └─► reply claims completion ✓
  └─► cooldown passed ✓
  └─► verify(): git clean? service up? recent errors?
  └─► posts verdict to Telegram
```

### 4. Taste summary (approach signal)
```
agent:end ──► taste-summary hook
  └─► reads taste rules
  └─► posts compact taste + confidence
```

### 5. Learning (later, in the scheduled review)
```
[scheduled] ──► review reads real git log: the css fix commit
  └─► session search: the work that was done
  └─► skill scan: a skill exists, could improve
  └─► proposes [P1] next task, [P2] skill gap, [P3] tooling fix
  └─► patches skills with today's lessons
```

## The full timeline

```
T0    session:start  → mem0 recall injected
T0+1  agent does work (SOUL + skills + tools)
T1    agent:end      → auto-verify verdict + taste summary
T2    (owner reads verdict, acts accordingly)
...
T+1d  07:00 daily briefing → learns, patches skills
T+1d  next session is smarter
```

## Key insight

Every step is **deterministic when it should be** (memory injection, verification)
and **autonomous when it should be** (skill patching). The human stays in the
loop at the decision points, not the mechanics.