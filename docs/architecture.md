# Architecture

How a production Hermes agent is wired for long-lived, honest, self-improving use.

## Component stack

| Layer | What | Why |
|---|---|---|
| **Gateway** | Hermes gateway (Telegram/Discord/webhook) | single event bus; fires hooks |
| **Identity** | `SOUL.md` | consistent personality + operating principles across sessions |
| **Skill library** | ~146 curated class-level skills | procedural knowledge loaded on demand |
| **Memory** | mem0 (PostgreSQL + pgvector) + MEMORY.md | durable semantic recall across sessions |
| **Hooks** | mem0-loader, auto-verify, taste-summary | event-driven behavior at session start / end |
| **Cron** | daily briefing, mem0 cleanup, git-sync, sessions archive | scheduled background intelligence |
| **Model routing** | one default + explicit fallback chain | predictable cost & behavior |

## Event loop

```
session:start ──► mem0-loader writes recall block ──► system prompt has memory
      │
      ├──► agent works (SOUL + skills + tools)
      │
agent:end ──► auto-verify checks "done" claims ──► taste-summary shows approach
      │
      └──► (background) daily-briefing reads work & patches skills
```

## The self-improvement flywheel

1. **Act** — agent does real work (git, builds, research).
2. **Record** — sessions + git history preserve what happened.
3. **Review** — daily briefing reads the record, finds gaps.
4. **Improve** — patches skills / notes the gaps for tomorrow.

Each loop makes the next session smarter. This is the difference between a
stateless assistant and a growing partner.

## Security posture

- **Config excluded from source** — live config, env, and session data are kept
  out of the repo; what ships is documented, adaptable patterns.
- **Verification before claims** — auto-verify enforces honesty.
- **Conservative memory cleanup** — never deletes good facts, only junk.
- **Self-hosted first** — local-first tooling preferred when a viable option
  exists.
