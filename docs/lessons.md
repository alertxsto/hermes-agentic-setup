# Lessons Learned

Hard-won pitfalls from running a long-lived Hermes agent. Each is a real
scenario that cost time — documented so it doesn't happen twice.

## Hooks & gateway

- **Hooks only load on gateway restart.** A new hook is written and tested, but
  silent until the gateway restarts. Confirm with `journalctl | grep "Loaded
  hook"` — don't assume.
- **`async def` vs `def` in AST validation.** An async handler is
  `ast.AsyncFunctionDef`, not `ast.FunctionDef`. A naive check "doesn't find" a
  valid `async def handle` — false alarm. Check both types.
- **Hook return values are discarded.** `emit()` swallows hook results, so
  side-effecting hooks (like the mem0 loader writing `MEMORY.md`) must act on
  disk, not return data.
- **A port can be `LISTEN` yet never answer HTTP.** A `python http.server` that
  has run for a day can hang — `ss` still shows `LISTEN`, but `curl` returns
  `000`. Always probe HTTP status, not just the port, and restart the specific
  PID.

## Verification (the auto-verify hook)

- **An agent's "done" is not evidence.** The reason the auto-verify hook exists:
  a claim must be checked. Deterministic checks (git status, HTTP status, log
  scan) work regardless of which model is running.
- **Filter noise hard.** Not every log line with "error" is a real error.
  Exclude `INFO`, `stream_error_clean`, `stream ended`, and bare traceback
  continuation lines. Only report dated `ERROR`/`CRITICAL` headers.
- **Timestamp timezone matters.** The agent log uses local time; a cleanup query
  must use the same zone (`date`, not `date -u`), or the "last 2h" filter is
  wrong.
- **Don't alarm on dev-only services.** An Expo dev server isn't meant to run
  24/7. Mark them (e.g. `# dev-only`) so the verify hook skips them when down —
  otherwise you get a permanent false "down" alarm.
- **Cooldown prevents spam.** A verify hook that fires on every "ok" is noise.
  A 5-minute cooldown file keeps it to one verdict per window.

## Memory

- **Memory injection must be idempotent.** The mem0 loader strips prior recall
  blocks before writing a new one, so repeated `session:start` runs never
  accumulate duplicates.
- **Memory cleanup must be conservative.** Never delete good facts — only
  identical duplicates, obvious noise, and leaked secrets. Audit every removal.
- **Memory store fills up.** Keep entries compact and refresh stale ones; a
  nearly-full store rejects new high-value facts.

## Skills

- **Skills should be class-level, not one-off.** A skill born from a single whim
  is clutter. Merge overlaps into umbrellas (163 → 146).
- **Merge with intent.** Track merges (`absorbed_into`) so cron jobs / references
  that pointed at the old skill get redirected automatically.
- **Patch skills immediately.** If a loaded skill has a wrong step or missing
  pitfall, fix it then — skills that aren't maintained become liabilities.

## Honesty

- **Never claim success without real tool output.** `curl 200`, a passing test,
  file contents — evidence, not vibes. This is the single most important rule
  for an agent the user trusts.
- **Live-probe models before trusting them.** A cheap/free model may mis-answer
  identity checks (one routed as a different assistant). Verify behavior, don't
  assume.