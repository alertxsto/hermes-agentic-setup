# Verification Pattern

The single most important rule for an agent the user trusts:

> **Never claim success without real tool output.**

An agent's *claim* ("done", "ok", "fixed") is not evidence. Verification makes
claims accountable. This applies at two levels: **in-prompt** (the agent's own
discipline) and **architectural** (a hook that checks regardless of model).

## Level 1 — In-prompt discipline (SOUL)

Encode it in the agent's operating principles:

- Every "done" needs proof: test passed, `curl 200`, file contents.
- No "it's probably fine."
- On failure: say what failed, what was tried, the alternative.
- Never fabricate output.

This trains the model to act honestly — but it's *soft*: a weak model can ignore
it.

## Level 2 — Architectural (the auto-verify hook)

Make verification **deterministic and automatic** so it doesn't depend on the
model's mood. See `hooks/auto-verify/`.

Flow: when the agent claims completion on a real task, the hook runs cheap,
deterministic checks and posts a verdict:

```
🧾 Auto-Verify · "gas beresin bug css site-checker"
✅ Repo bersih
✅ site-checker UP
⚠️ the-app down (dev-only, expected)
✅ Log bersih
**⚠️ ada yang perlu dicek**
```

### Anti-noise design

- **Task detection** — only fire on real tasks, not casual chat.
- **Claim detection** — only when the reply says ok/done/selesai/fixed.
- **Cooldown** — max once per 5 min.
- **Dev-only tolerance** — services not expected to run 24/7 are skipped when
  down (no false alarm).

## What to verify

| Claim | Check |
|---|---|
| "I built X" | command exit 0, artifact exists |
| "service is up" | `curl` → 200 |
| "I fixed the bug" | test passes, repo clean |
| "deployed" | endpoint reachable, no errors in log |

## Rule of thumb

> Trust is built on verifiable claims. The verify hook is cheaper than a broken
> trust relationship.