# The Complete Agent Flow

The full lifecycle of this agent — end to end, phase by phase, with concrete use
cases. Everything here maps to a real mechanism in this repo (read the hook
sources; none of this is invented).

```
┌───────────────────────────────  LIFECYCLE  ───────────────────────────────┐
│                                                                            │
│  session:start         agent works          agent:end          scheduled   │
│  ─────────────         ───────────          ─────────          ─────────   │
│  mem0 loader   ──►     SOUL +       ──►     auto-verify  ──►   review      │
│  (memory into           skills +            + taste-summary   patches      │
│   fresh prompt)         tools                                skills       │
│                                                                            │
│  ◄── remember ──────────► act ───────────► verify ─────────► improve ──┐  │
│                                                                            │
└──────────────────— every session starts smarter ──—───────────────────┘
```

---

## Phase 0 — Boot: `session:start`

**Trigger:** a new session begins (owner sends a message or schedules a job).

**What runs:** [`hooks/mem0-session-loader/handler.py`](hooks/mem0-session-loader/handler.py)

**Mechanism:**
1. Gateway fires `session:start` **before** the new session's system prompt is
   built.
2. The hook queries the semantic store (mem0, PostgreSQL + pgvector) for prior
   memories relevant to the current context.
3. It strips any old recall block, then **writes a fresh `# Mem0 Recall` block
   into `MEMORY.md`** (atomic — see below).
4. Hermes' `load_from_disk()` snapshots that block into the new session's system
   prompt.

**Why atomic:** `MEMORY.md` is also written by the built-in memory tool. The hook
uses Hermes' `atomic_write_text` (temp file → fsync → rename) so the two writers
never corrupt or lose each other's changes.

**Result:** the fresh agent — which never saw yesterday — *remembers* prior work.

### Use case A — continuing yesterday's work
```
Yesterday: fixed a bug in the checkout flow, committed.
Today:     owner opens a new session.
  ── session:start ──► mem0 recall includes: "checkout flow fixed, 3 files"
  ──► the agent already knows the context. It can pick up without re-asking.
```

### Use case B — context from a different session
```
The agent learned (in session 1) that the owner prefers bullet answers and
"gas" = execute. That preference is stored.
  ── session:start ──► mem0 recall injects: "user prefers concise bullets".
  ──► every session, even a fresh one, answers in the owner's preferred style.
```

---

## Phase 1 — Act: the agent works

**Driving data:** [`soul/asep.md`](soul/asep.md) (SOUL) + [`skills/`](skills/) +
MCP tools.

The SOUL governs *how* the agent behaves (who it is, communication style,
operating principles — plan big work, verify before claiming, honest on
failure, kill specific processes only). Skills give it *how to do things*.

### Use case C — a coding task with plan-first
```
owner: "gas refactor auth module"
  agent reads SOUL: "gas" = execute, but "plan big work first"
  ──► for a big refactor, it first writes a short plan and shows it
  ──► owner approves ("gas")
  ──► agent loads the relevant skill, edits, commits
```

### Use case D — a research task (tools)
```
owner: "coba riset provider X untuk model Y"
  agent loads research skills, uses web/MCP tools
  ──► gathers real sources (not guesses)
  ──► presents a cited, honest summary
```

---

## Phase 2 — Verify: `agent:end`

**Trigger:** the agent finishes a run.

**What runs:**
- [`hooks/auto-verify/handler.py`](hooks/auto-verify/handler.py) — the honesty gate
- [`hooks/taste-summary/`](hooks/taste-summary/) — the approach signal

### The four guards (auto-verify)

The hook only acts if ALL pass — otherwise it stays silent (no spam):

| Guard | Checks | Example pass |
|---|---|---|
| 1. Task detection | message is real work, not chat | `beresin`, `fix`, `deploy` |
| 2. Claim detection | reply says it's done | `ok`, `selesai`, `fixed` |
| 3. Length | reply is substantial (≥80 chars) | not a bare "ok" |
| 4. Cooldown | ≤1 check per 5 min | recent window clear |

### The three checks (when guards pass)

```
verify():
  1. git clean?     git status --short on active repos
  2. services up?   curl HTTP status (dev-only skipped when down — expected)
  3. log clean?     recent ERROR/CRITICAL in agent.log (last 2h, noise filtered)
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

### Use case E — the overclaim catch
```
agent: "oke udah gw fix, deploy sukses"
  auto-verify:
    guard 1 ✓ task   guard 2 ✓ "sukses"   guard 3 ✓   guard 4 ✓
    check 1 → ⚠️ Repo dirty: 3 files uncommitted
    check 2 → ✅ service UP
    check 3 → ✅ log clean
  verdict: ⚠️ ada yang perlu dicek  ("agent said done but repo dirty")
  ──► owner sees it immediately instead of discovering later.
```

### Use case F — taste summary (showing how it worked)
```
agent:end also fires taste-summary
  → posts the approach rules + confidence the agent operated under
  ──► owner sees not just "done" but *how* it approached it.
```

---

## Phase 3 — Improve: the scheduled review

**Trigger:** on a schedule (e.g. every morning).

**Pattern:** [`patterns/self-improving.md`](patterns/self-improving.md)

**Mechanism:**
1. **Act** — the agent did real work (git commits, sessions).
2. **Record** — git history + session transcripts preserve what happened.
3. **Review** — read the last 24h: real git log, recent sessions, skill scan.
4. **Improve** — **patch skills** with today's lessons.

### Use case G — the agent patches its own skill
```
The agent hit a problem (a skill had a wrong command). The review encodes:
  "lesson: command X must use flag Y".
  ──► the skill is patched; tomorrow it does it right the first time.
  ──► this is the self-improving loop: each session inherits the last.
```

### Use case H — dead-simple daily handoff
```
owner opens tomorrow's session.
  ──► mem0 recall (Phase 0) + patched skills (Phase 3)
  ──► the agent is measurably smarter than yesterday.
```

---

## Use case I — the full loop in one task

```
owner: "gas beresin bug css di site-checker"
  [Phase 0] session:start → mem0 recall: prior site-checker context
  [Phase 1] agent works  → SOUL + skill + tools, edits CSS
  [Phase 2] agent:end    → auto-verify: repo dirty? no. service up? yes.
                           log clean? yes.  → ✅ aman
                           + taste-summary: approach + confidence
  [Phase 3] (later)      → review reads the commit, patches any skill gap
  [next session]         → remembers + is smarter
```

---

## Phase 4 — Scheduled & background workflows

Beyond the interactive loop, the agent runs **8 scheduled jobs** that keep
memory, backups, and the environment healthy. All are `no-agent` script jobs
(cheap, deterministic stdout) except the daily briefing (agent-driven).

| # | Job | Schedule | Deliver | What it does |
|---|---|---|---|---|
| 1 | **Daily Briefing** | 07:00 daily | telegram | agent-driven self-improving review (see Phase 3) |
| 2 | **Memory Consolidation** | every 6h | local | `consolidate-then-export.sh` → run consolidation, export to GitHub |
| 3 | **Session Archive** | 02:00 daily | local | archive sessions >30 days, purge archives >90 days |
| 4 | **Git Sync Hermes Config** | every 60m | local | `hermes-backup-sync.sh` → sync `.hermes` config to the backup repo |
| 5 | **OSS Good First Issue Hunter** | 08:00 daily | telegram | `oss_issue_hunter.py` → find good-first-issues via GitHub API + web |
| 6 | **Power & Cost Monitor** | every 60m | local | `power_monitor.py` → power draw + PLN cost, log JSONL |
| 7 | **Weekly Power Cost Summary** | Mon 09:00 | telegram | `power_weekly_summary.py` → weekly avg + Telegram summary |
| 8 | **Mem0 Auto Cleanup** | 04:00 daily | local | `mem0_auto_cleanup.py` → conservative dedup / noise / secret scrub |

### Supporting scripts (not scheduled, run on demand)

| Script | Purpose |
|---|---|
| `work_prep_collector.sh` | ground-truth telemetry: git log 24h, dirty WIP, service status |
| `system-monitor.sh` | power/CPU/memory/disk/network report |
| `export-memory-to-md.sh` | export memory store to a snapshot dir in the backup repo |
| `fetch_yt_transcript.py` | pull a YouTube transcript and store it in mem0 |
| `mem0_client.py` | the mem0 client shared across scripts |

### Use case J — the memory health loop (jobs 2 + 8)
```
Memory Consolidation (6h)  → consolidate + export memory to GitHub backup
Mem0 Auto Cleanup (04:00)  → remove duplicates/noise/leaked secrets
  ──► memory stays fresh, deduped, and backed up — without manual work.
```

### Use case K — the environment health loop (jobs 6 + 7)
```
Power & Cost Monitor (60m) → continuous power/cost JSONL log
Weekly Power Summary (Mon) → human-readable weekly cost to Telegram
  ──► the owner sees cost trends and anomalies automatically.
```

### Use case L — OSS contribution hunting (job 5)
```
OSS Good First Issue Hunter (08:00) → curated good-first-issues sent to Telegram
  ──► the owner reviews over coffee and picks one to contribute to.
```

### Use case M — backup & archive discipline (jobs 3 + 4)
```
Git Sync Hermes Config (60m) → config always backed up to the git repo
Session Archive (02:00)      → old sessions archived, stale ones purged
  ──► nothing is lost, and the working store never bloats.
```

---

## What can go wrong (and where it's caught)

| Failure mode | Caught at |
|---|---|
| agent claims done, repo dirty | auto-verify → ⚠️ Repo dirty |
| agent says deployed, service down | auto-verify → ⚠️ HTTP status |
| agent left a real error in the log | auto-verify → ⚠️ Recent ERROR |
| agent "forgets" last session | mem0 loader → recall injected |
| skill library grows stale | scheduled review → patches skills |
| hook dies silently | hook logs failures (no bare except) |

---

## Reference map

| Phase | Docs | Source |
|---|---|---|
| 0. Boot | [`patterns/memory.md`](patterns/memory.md) | `hooks/mem0-session-loader/handler.py` |
| 1. Act | [`soul/asep.md`](soul/asep.md), [`skills/index.md`](skills/index.md) | SOUL + skills |
| 2. Verify | [`patterns/verification.md`](patterns/verification.md) | `hooks/auto-verify/handler.py` |
| 3. Improve | [`patterns/self-improving.md`](patterns/self-improving.md) | scheduled review |
| 4. Background | — | 8 cron jobs + scripts in `~/.hermes/scripts/` |

See also: [`examples/task-flow.md`](examples/task-flow.md),
[`examples/hook-event-map.md`](examples/hook-event-map.md),
[`docs/architecture.md`](docs/architecture.md).
