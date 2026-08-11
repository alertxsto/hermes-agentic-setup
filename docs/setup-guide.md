# Setup Guide

How to take the patterns in this repo and build your own agentic Hermes setup.
Adapt, don't copy — the code is real but should match your environment.

## Prerequisites

- A running Hermes Agent instance (gateway + Telegram/Discord/webhook).
- A model provider configured (see `patterns/model-routing.md`).
- (Optional) mem0 for semantic memory (PostgreSQL + pgvector).

## 1. Identity — SOUL

```bash
# Start from the template
cp TEMPLATES/SOUL.TEMPLATE.md ~/.hermes/SOUL.md
# edit the persona to be yours
```

See `soul/asep.md` for a full worked example.

## 2. Skill library

- Curate class-level skills (see `patterns/skill-curation.md`).
- Keep `skills/index.md` as a map of what you have.

## 3. Memory (optional but recommended)

1. Stand up mem0 (PostgreSQL + pgvector).
2. Configure the client (`mem0_client`).
3. Add the `mem0-session-loader` hook.
4. Add the `mem0-auto-cleanup` cron + `cron/scripts/mem0_auto_cleanup.py`.

## 4. Hooks

```bash
mkdir -p ~/.hermes/hooks/auto-verify
cp hooks/auto-verify/handler.py ~/.hermes/hooks/auto-verify/
cp hooks/auto-verify/HOOK.yaml ~/.hermes/hooks/auto-verify/
```

**Then restart the gateway** — hooks only load on restart.

## 5. Cron — the self-improving loop

1. Copy `cron/scripts/work_prep_collector.sh` and point its `ACTIVE_REPOS` at
   your repos.
2. Create a daily briefing cron (see `cron/daily-briefing.md`).
3. Pin it to a reliable provider + fallback (see `patterns/model-routing.md`).

## 6. Model routing

Set one clean default + explicit fallback chain (see
`patterns/model-routing.md`). Remember: fallback config must be a real YAML
**list**, and provider keys belong in `.env` for cron preflight.

## 7. Verify it works

```bash
# hooks loaded?
journalctl | grep "Loaded hook"

# telemetry collector runs?
bash cron/scripts/work_prep_collector.sh

# auto-verify fires on a real task?
# send a task, watch for the verdict in Telegram
```

## Checklist

- [ ] SOUL set
- [ ] skills curated
- [ ] mem0 running + session-loader hook
- [ ] auto-verify + taste-summary hooks (gateway restarted)
- [ ] daily-briefing cron (provider pinned)
- [ ] model routing: one default + fallback
- [ ] `work_prep_collector.sh` points at your repos