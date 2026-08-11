# Model Routing Pattern

**Problem it solves:** over time a setup accumulates many model providers
(9Router gateway, OpenRouter exports, CLI-pass subscriptions, etc.) — creating a
**mess**: too many choices, wasted spend, and inconsistent routing. The fix is a
**single clean default + explicit fallback chain**.

## The messy state (anti-pattern)

- Several providers compete: `custom`/9Router (many accounts), OpenRouter
  (hundreds of stale models from an old bulk-import), a CLI-pass subscription.
- The default pointed at the gateway, wasting calls; a fallback had wrongly been
  pointed at OpenRouter when a clean subscription already existed.

**Lesson:** more providers ≠ better. Chaos makes the agent slower to pick and
harder to reason about.

## The clean state (pattern)

1. **One default provider** — pick the model that's *free on your plan* and
   reliable. E.g. `cline-pass/deepseek-v4-flash` (free, doesn't burn quota).
2. **Explicit fallback chain** — fallback to a stronger model on the *same*
   provider, then a secondary one. Never fall back to a provider that meaningfully
   adds cost/copies elsewhere.
3. **9Router stays as a *manual pick* tool**, not the default — cleanly listed
   (synced to what it actually serves), never the silent default.

```
Default:  cline-pass/deepseek-v4-flash   (free, main)
Fallback1: cline-pass/glm-5.2            (stronger, same provider)
Fallback2: cline-pass/kimi-k2.7-code     (specialist, same provider)
```

## Key gotchas (learned the hard way)

- **Fallback config MUST be a YAML list** — `config set` with a JSON string can
  silently write it as a string that isn't parsed. Fix by writing real list form.
- **Env-key preflight:** cron jobs validate provider credentials from env. If a
  provider's key lives only in `config.yaml`, the cron preflight may block it —
  set `CLINE_API_KEY` (etc.) in `.env` explicitly.
- **9Router model count:** the Hermes config had **381** stale model entries
  while 9Router really served **50**. Sync the catalog to reality to reduce
  noise and wasted scan.

## Performance sanity

Verify a "free/cheap wins" model isn't secretly bad: compare it against peers
on benchmarks and, crucially, via **live identity probes** (call it and sanity
check it doesn't mis-answer). A cheap model that mis-routes is not worth the
savings.