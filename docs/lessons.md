# Lessons Learned

Hard-won pitfalls from running a long-lived Hermes agent. Each is a real
scenario that cost time — documented so it doesn't happen twice.

## Hooks & gateway

- **Hooks only load on gateway restart.** A new hook is written and tested, but
  silent until the gateway restarts. Confirm with
  `journalctl | grep "Loaded hook"` — don't assume.
- **`async def` vs `def`**: when validating a handler with AST, remember async
  functions are `AsyncFunctionDef`, not `FunctionDef`. A naive check "doesn't
  find" a valid `async def handle` — false alarm.
- **Hook return values are discarded.** `emit()` swallows hook results, so
  side-effecting hooks (like mem0-loader writing MEMORY.md) must act on disk,
  not return data.

## Cron & model routing

- **A cron can "not run" by silently failing on the model.** Check the output
  file — it may contain `[error: network connection lost]` instead of real
  output. The job ran; the model failed.
- **Cron preflight checks env keys, not config.** A provider key stored in
  `config.yaml` may not satisfy the cron's credential check — set it in `.env`.
- **`config set` with a JSON string can write a string, not a list.** Fallback
  `providers` must be a real YAML list or it won't parse.
- **Pin important jobs to a reliable provider** + a fallback chain, so nightly
  work doesn't depend on a flaky default.

## Services

- **A `python http.server` can hang after long uptime** — still shows `LISTEN`
  in `ss` but never answers HTTP (`curl` → 000). A port-check that only tests the
  port misses this; always probe HTTP status, and restart the specific PID.
- **Don't alarm on dev-only services.** An Expo dev server isn't meant to run
  24/7. Mark them (e.g. `# dev-only`) so the verify hook skips them when down.

## Skills & memory

- **Skills should be class-level, not one-off.** A skill born from a single whim
  is clutter. Merge overlaps into umbrellas (163 → 146).
- **Memory cleanup must be conservative.** Never delete good facts — only
  identical duplicates, obvious noise, and leaked secrets. Audit every removal.
- **Memory store fills up.** Keep entries compact and refresh stale ones; a
  nearly-full store rejects new high-value facts.

## Verification

- **Never claim success without real tool output.** `curl 200`, test passing,
  file content — evidence, not vibes. This is the single most important rule for
  an agent the user trusts.
- **Live-probe models before trusting them.** A "free" model may mis-answer
  identity checks (one mis-routed as a different assistant). Verify, don't assume.