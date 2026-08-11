# Auto-Verify Hook

**Problem it solves:** agents — especially lightweight models — often *say* "ok,
done" when there's actually a build error, dirty repo, or down service. This is
the **overclaim problem**. This hook makes the claim verifiable.

**When it fires:** on `agent:end`, but only when:
1. The user's message looks like a real task (`fix`, `build`, `deploy`, `beresin`…),
   not casual chat.
2. The agent's reply actually *claims* completion (`ok`, `done`, `selesai`, `fixed`…).
3. A cooldown window (default 5 min) has passed — no spam.

**What it checks** (all deterministic & cheap):
- **Repo cleanliness** — `git status --short` on active repos.
- **Service health** — `curl` HTTP status for dev services.
- **Recent errors** — grep the agent log for real `ERROR`/`CRITICAL` within the
  last 2h (noise filtered: `INFO`, `stream_error_clean`, `tool_executor`).

**Anti-noise design:**
- **Dev-only services** (marked `# dev-only` in the collector) — an Expo dev
  server that's not expected to run 24/7 is *skipped* when down, not alarmed.
- **Cooldown file** — max one verification per 5 minutes.
- **Task/claim regex** — only real tasks with a completion claim trigger it.

## Files

- `HOOK.yaml` — registers the hook on `agent:end`.
- `handler.py` — the verification logic + Telegram verdict.
- `services.txt` note: the hook reads the service list from
  `work_prep_collector.sh` (the single source of truth), so adding a project
  auto-extends verification — no code change needed.

## Outcome

After each real task, the owner gets a compact verdict:

```
🧾 Auto-Verify · "gas beresin bug css skill-arena"
✅ Repo bersih
✅ skill-arena UP
⚠️ warung-app down (dev-only, expected)
✅ Log bersih
**⚠️ ada yang perlu dicek**
```