# Setup Guide

How to build your own agentic Hermes setup from the patterns in this repo.
Adapt, don't copy — the code is real but should match your environment.

## Prerequisites

- A running Hermes Agent instance (gateway + Telegram/Discord/webhook).
- A configured model provider.
- (Optional) mem0 for semantic memory (PostgreSQL + pgvector).

## 1. Identity — SOUL

```bash
cp TEMPLATES/SOUL.TEMPLATE.md ~/.hermes/SOUL.md
# edit the persona to be yours
```

See `soul/asep.md` for a full worked example. The SOUL defines who the agent is
and how it works — it's injected into every session.

## 2. Skill library

- Curate class-level skills (see `patterns/skill-curation.md`).
- Keep `skills/index.md` as a map of what you have.

## 3. Memory (optional but recommended)

1. Stand up mem0 (PostgreSQL + pgvector).
2. Configure the client.
3. Add the `mem0-session-loader` hook (see `hooks/mem0-session-loader/`).

## 4. Hooks — the honesty guarantees

```bash
mkdir -p ~/.hermes/hooks/auto-verify
cp hooks/auto-verify/handler.py ~/.hermes/hooks/auto-verify/
cp hooks/auto-verify/HOOK.yaml ~/.hermes/hooks/auto-verify/
```

**Then restart the gateway** — hooks only load on restart.

Add `taste-summary` the same way for the approach/confidence line.

## 5. Self-improving loop

Set up a scheduled review that reads the last 24h of real work and patches
skills (see `patterns/self-improving.md`). The mechanics:

1. Collect ground truth — recent git log per repo, dirty WIP, service status.
2. Read recent sessions.
3. Scan the skill library.
4. Produce a structured briefing with concrete suggestions.
5. **Patch skills** with the day's lessons.

## 6. Verify it works

```bash
# hooks loaded?
journalctl | grep "Loaded hook"

# auto-verify fires on a real task?
# send a task, watch for the verdict in Telegram
```

## Checklist

- [ ] SOUL set
- [ ] skills curated
- [ ] mem0 running + session-loader hook
- [ ] auto-verify + taste-summary hooks (gateway restarted)
- [ ] self-improving review loop running