# 🤖 Hermes Agent — The Flow

> **How a long-lived AI agent actually works.** Not a config dump — the
> *behavioral flow*: who the agent is (SOUL), how it remembers, how it's kept
> honest, and how it gets smarter every day.
>
> Built on [Hermes Agent](https://hermes-agent.nousresearch.com/docs) by
> Nous Research · [Apache-2.0](LICENSE)

This repo documents a working agent that runs real daily work. Everything here
is the actual mechanism — read the hook sources, the SOUL, the patterns. No
theory, no invented features.

---

## 🧭 The Big Picture

An agent is useful long-term only if three things hold: it **remembers** across
sessions, it **doesn't lie** about results, and it **learns** from what it did.
Everything in this repo serves those three goals.

```
   session starts → memory loads → agent works → claims done
                                              │
                                              ▼  (hook verifies the claim)
                                        verdict to owner
                                              │
    next morning: briefing reads real work → patches its own skills
```

---

## 1 · Who the agent is — the SOUL

A long-lived agent needs a **stable identity and operating code** that survive
across sessions and across model swaps. In Hermes this is `~/.hermes/SOUL.md`,
injected into every session.

The full text is in [`soul/asep.md`](soul/asep.md). Its structure:

- **Identity** — the persona: an assistant that's human, technically sharp, and
  trusted with real work.
- **Communication style** — bullet + bold, Telegram-friendly, short and dense,
  show confidence, use the owner's key words (`gas` = execute, `sebentar` =
  wait, `lanjut` = continue).
- **Working principles** — the operating code:
  - **Plan big work first** — write it, show it, get approval before executing.
  - **Verify before claiming** — every "done" needs real evidence (test output,
    `curl 200`, file contents). No "it's probably fine."
  - **Honesty** — on failure say what failed, what was tried, the alternative.
  - **Respect running services** — confirm before changing them, especially
    while remote.
  - **Kill specific processes only** — never global `pkill`, never the
    orchestrator without asking.
- **Principles** — open-source & self-hosted first, Apache-2.0 for public work,
  judge models by *feel/personality* over benchmarks, respect the user's final
  call.

> Why it matters: consistency. No matter which session or model, the agent
> behaves the same because the SOUL is always there.

---

## 2 · Remembering — the memory flow

A fresh session has a **frozen system prompt** — it can't remember yesterday.
The fix is a layered memory system.

### The mechanism (mem0 session loader)

On `session:start`, a hook [`hooks/mem0-session-loader/handler.py`](hooks/mem0-session-loader/handler.py)
injects prior knowledge into the fresh session. The subtle part (verified
against Hermes source):

- The gateway fires `session:start` for a NEW session, **before** that session's
  system prompt is built.
- The hook **writes a recall block into `MEMORY.md`** on disk.
- Hermes' `load_from_disk()` then snapshots that block into the fresh session's
  system prompt.
- Because hook return values are discarded by the gateway, injection *must*
  happen by writing state to disk, not by returning data.
- The block is **idempotent** — prior recall blocks are stripped so runs never
  accumulate duplicates — and size-capped (trims to top 3 items past a budget).

**Result:** the new agent "remembers" relevant prior work even though it never
saw it. Memory survives across sessions.

### The layers

| Layer | What lives here | Filled by |
|---|---|---|
| `MEMORY.md` (system prompt) | compact, always-present facts | session start |
| **mem0** (vector store) | durable semantic facts | session start, as needed |
| **skills/** | procedural knowledge (*how to do X*) | when a workflow is learned |

> [`patterns/memory.md`](patterns/memory.md) · [`hooks/mem0-session-loader/`](hooks/mem0-session-loader/)

---

## 3 · Honesty — the auto-verify hook

The single most important rule: **an agent must not claim success it didn't
verify.** A claim ("done", "ok") is not evidence. This setup enforces it
*architecturally*, not just by asking the model to be honest.

[`hooks/auto-verify/handler.py`](hooks/auto-verify/handler.py) fires on
`agent:end` and runs deterministic, cheap checks when the agent says it finished
a real task:

1. **Task detection** — only fire when the user's message looks like real work
   (`beresin`, `fix`, `build`, `deploy`…), not casual chat.
2. **Claim detection** — only when the reply actually says ok/done/selesai/fixed.
3. **Verification** — check git cleanliness, service HTTP status, and a recent
   error scan of the agent log.
4. **Verdict** — post the result to the owner.

Noise controls: a **cooldown** (max once per 5 min) and **dev-only tolerance**
(services not meant to run 24/7 are skipped when down, so no false alarm).

```txt
🧾 Auto-Verify · "gas beresin bug css di site-checker"
✅ Repo bersih
✅ site-checker UP
⚠️ the-app down (dev-only, expected)
✅ Log bersih
**⚠️ ada yang perlu dicek**
```

Deterministic + automatic = it works regardless of which model is running.

> [`hooks/auto-verify/`](hooks/auto-verify/) · [`patterns/verification.md`](patterns/verification.md)

---

## 4 · Showing work — the taste summary

Companion to auto-verify: on `agent:end` it posts a compact **taste + confidence**
line (like Command Code), so the human sees not just *that* a task finished but
*how* the agent approached it.

> [`hooks/taste-summary/`](hooks/taste-summary/)

---

## 5 · Getting smarter — the self-improving loop

The defining feature. A daily workflow reads what the agent actually did, finds
gaps, and **patches its own skills**.

```
   ACT      → the agent does real work (git commits, sessions)
   RECORD   → git history + session transcripts preserve what happened
   REVIEW   → a scheduled review reads the last 24h: real git log,
              sessions, skill library scan
   IMPROVE  → patches skills / encodes lessons for the next session
```

This is a **verified, real** loop — the review has autonomously updated skills
with the day's lessons and deduplicated overlapping sections. Each session
inherits the previous ones, so the agent compounds.

> [`patterns/self-improving.md`](patterns/self-improving.md)

---

## 6 · Skills — knowledge that stays sharp

Procedural knowledge lives as **skills**; they're loaded when relevant. The
library is actively curated:

- **~147 skills**, merged down from 163 by consolidating 11 overlapping groups
  into class-level umbrellas.
- **Rule:** a skill captures a *recurring class of work*, not a one-off. Skills
  born from a single whim are clutter and get removed.
- A skill is **patched immediately** when it's found outdated or wrong — skills
  that aren't maintained become liabilities.

> [`skills/index.md`](skills/index.md) · [`patterns/skill-curation.md`](patterns/skill-curation.md)

---

## 🧭 End-to-end flow (one task)

```
owner: "gas beresin bug css di site-checker"
 1  session:start  → mem0 recall injected into the new session
 2  agent works    → SOUL + skills + tools
 3  agent:end      → auto-verify checks the "done" claim → verdict to owner
                    → taste-summary posts approach + confidence
 4  (next review)  → real git log shows the fix, skills patched if needed
 5  next session   → is smarter
```

Details in [`examples/task-flow.md`](examples/task-flow.md).

---

## 🧰 Reference

- [`examples/hook-event-map.md`](examples/hook-event-map.md) — all events & hooks
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/lessons.md`](docs/lessons.md) — hard-won pitfalls
- [`TEMPLATES/`](TEMPLATES/) — SOUL & HOOK starting points
- [`soul/asep.md`](soul/asep.md) — the full SOUL

---

## 📜 License

[Apache-2.0](LICENSE)
