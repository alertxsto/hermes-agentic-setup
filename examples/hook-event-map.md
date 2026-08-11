# Hook Event Map

Every hook in this setup, when it fires, and what it does. Use this as a
reference for wiring your own hooks.

## The events

| Event | Fires when | Hooks in this setup |
|---|---|---|
| `session:start` | a new session begins, before its prompt is built | `mem0-session-loader` |
| `session:reset` | a session resets | `mem0-session-loader` |
| `agent:end` | an agent run finishes | `auto-verify`, `taste-summary` |

## Hook registry

| Hook | Event(s) | Purpose | Side effect |
|---|---|---|---|
| `mem0-session-loader` | `session:start`, `session:reset` | Inject semantic memory into the fresh session | writes recall block to `MEMORY.md` |
| `auto-verify` | `agent:end` | Verify "done" claims deterministically | posts Telegram verdict |
| `taste-summary` | `agent:end` | Show taste + confidence | posts Telegram taste line |

## HOOK.yaml format

```yaml
name: my-hook
description: What it does
events:
  - agent:end
```

The handler is a Python file next to `HOOK.yaml` with an async entry point:

```python
async def handle(event_type: str, context: dict):
    # event_type: one of the registered events
    # context:    dict with message / response / user info
    ...
```

## Wiring a new hook

1. Create `~/.hermes/hooks/<name>/HOOK.yaml` with the event(s).
2. Create `~/.hermes/hooks/<name>/handler.py` with `async def handle(...)`.
3. **Restart the gateway** — hooks only load on restart.
4. Confirm: `journalctl | grep "Loaded hook"`.

## Gotchas

- **Hook return values are discarded** by the gateway (`emit()` swallows them).
  To influence the agent, write state to disk (e.g. `MEMORY.md`), don't return
  data.
- **`async def`** is `AsyncFunctionDef` in Python AST — a naive
  `isinstance(n, FunctionDef)` check won't "find" a valid async handler. False
  alarm.
- **Restart required** — a new hook is invisible until the gateway restarts.

## See also
- `hooks/*/README.md` — full docs per hook
- `TEMPLATES/HOOK.TEMPLATE.yaml` — starting point