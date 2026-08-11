# Architecture

How a production Hermes agent is wired for long-lived, honest, self-improving
use. This is the actual mechanism — read it alongside the hook sources.

## Component stack

| Layer | What | Why |
|---|---|---|
| **Gateway** | Hermes gateway (Telegram/Discord/webhook) | single event bus; fires hooks at session/agent lifecycle points |
| **Identity** | `SOUL.md` | stable personality + operating code across every session |
| **Skill library** | ~180 class-level skills | procedural knowledge loaded on demand |
| **Memory** | mem0 (PostgreSQL + pgvector) + `MEMORY.md` | durable semantic recall across sessions |
| **Hooks** | `mem0-session-loader`, `auto-verify`, `taste-summary` | event-driven behavior at session start / agent end |
| **Tools** | MCP servers + terminal + web | the agent's hands |

## The event loop

The gateway is the heartbeat. It fires lifecycle events that hooks subscribe to:

```
session:start ──► mem0-session-loader
                   └─► writes "# Mem0 Recall" block into MEMORY.md
                   └─► load_from_disk() snapshots it into the new session's
                       system prompt  →  the agent "remembers" prior context
      │
      ▼
agent works (driven by SOUL + skills + MCP tools)
      │
      ▼
agent:end ──► auto-verify  ──► taste-summary
              (checks the    (posts approach +
               "done" claim)   confidence)
      │
      ▼
(background) scheduled review reads real work → patches skills
```

### Why memory injection works this way

The subtle bit (verified against Hermes source): the gateway fires
`session:start` for a NEW session **before** that session's system prompt is
built. Hook return values are **discarded** by `emit()`, so the hook can't hand
data back — it must **write to disk** (`MEMORY.md`). Then
`MemoryStore.load_from_disk()` snapshots that block into the fresh prompt.

That's why the mem0 loader writes a recall block *into the file* rather than
returning anything. It uses Hermes' **atomic writer** (`atomic_write_text`) so it
never races the built-in memory tool that also writes `MEMORY.md`. See
`hooks/mem0-session-loader/handler.py`.

> **Native vs custom:** Hermes already ships memory providers (`hermes memory`)
> and an auto-curator. This custom hook covers the specific case of injecting a
> semantic recall block at `session:start`. If your Hermes version auto-injects
> provider memory natively, prefer that and drop the hook to avoid duplicate
> writes. See the hook README.

## The three goals

Everything exists to serve three properties a long-lived agent must have:

1. **Remembers** — mem0 loader injects prior knowledge each session.
2. **Doesn't lie** — auto-verify enforces verification architecturally.
3. **Learns** — the scheduled review patches its own skills.

## The self-improvement flywheel

```
ACT ──► RECORD ──► REVIEW ──► IMPROVE
 │         │          │          │
real     git +      scheduled   patches
work     sessions   review      skills
```

1. **Act** — the agent does real work (git commits, builds, research).
2. **Record** — git history + session transcripts preserve what happened (ground
   truth, not imagination).
3. **Review** — a scheduled review reads the last 24h: real git log, recent
   sessions, skill-library scan.
4. **Improve** — patches skills / encodes lessons for the next session.

Each loop makes the next session smarter. This is the difference between a
stateless assistant and a growing partner.

## Security posture

- **Config excluded from source** — live config, env, and session data are kept
  out of the repo; what ships is documented, adaptable patterns.
- **Verification before claims** — auto-verify is architectural, not just a
  prompt rule.
- **Conservative memory cleanup** — never deletes good facts, only junk.
- **Self-hosted first** — local-first tooling preferred when viable.