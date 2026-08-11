# 🤖 Hermes Agent — The Flow

> How a long-lived AI agent actually works: who it is (SOUL), how it remembers,
> how it's kept honest, and how it gets smarter every day. All from a real,
> working deployment.

Built on [Hermes Agent](https://hermes-agent.nousresearch.com/docs) by Nous Research ·
[Apache-2.0](LICENSE)

---

## At a glance

| | |
|---|---|
| **Agent** | one long-lived personal AI assistant |
| **Skills** | 147, across root + 15 categories (incl. 6 security + design/taste suite) |
| **MCP servers** | 7 (github, chrome-devtools, postgres, firecrawl, memory, context7, sequential-thinking) |
| **Hooks** | mem0-session-loader, auto-verify, taste-summary |
| **Memory** | mem0 (PostgreSQL + pgvector) + built-in `MEMORY.md` |
| **Self-improvement** | native curator + memory consolidation |

**Three goals everything serves:**
1. **Remembers** across sessions.
2. **Doesn't lie** about results.
3. **Learns** from what it did.

---

## The loop

```
session:start → memory loads → agent works → claims done
                                            ↓ (hook verifies the claim)
                                      verdict to owner
                                            ↓ (later)
                             review reads real work → patches its own skills
```

1. **Recall** — a hook injects semantic memory into each fresh session.
2. **Act** — SOUL + 147 skills + 7 MCP tools.
3. **Verify** — an auto-verify hook checks "done" claims deterministically.
4. **Learn** — memory consolidation + native curator keep it sharp.

---

## Capabilities (what it can actually do)

**7 MCP servers** — `github` (repos/PRs) · `chrome-devtools` (browser) · `postgres`
(SQL) · `firecrawl` (web) · `memory` (graph) · `context7` (docs) · `sequential-thinking`
(reasoning).

**Standout skill workflows:**
- **AI website judging** — Playwright crawler + vision-LLM auto-scores sites.
- **Agy orchestration** — PLAN → approve → parallel EXECUTE → verify.
- **Unlimited semantic memory** (mem0) — beyond Hermes' built-in cap.
- **6-skill security suite** — intrusion logs, API testing, MCP-poisoning audit,
  CT-logs, prompt-injection detection.
- **WebReaper scraping** — self-hosted MIT scraper with bot-protection + stealth.
- **Design/taste system** — ships UI that doesn't look AI-generated.

Full map: [`skills/index.md`](skills/index.md).

---

## Core components

| Doc | What |
|---|---|
| [`FLOW.md`](FLOW.md) | **start here** — full lifecycle + use cases |
| [`soul/asep.md`](soul/asep.md) | the agent's identity & operating principles |
| [`hooks/`](hooks/) | event-driven extensions (mem0-loader, auto-verify, taste-summary) |
| [`patterns/`](patterns/) | reusable recipes (memory, verification, self-improving, skill curation) |
| [`examples/`](examples/) | task flow + hook event map |
| [`docs/`](docs/) | architecture · lessons · setup guide |
| [`TEMPLATES/`](TEMPLATES/) | SOUL & HOOK starting points |

---

## Honest limits

Built by one person, on one machine. **Not** a community-validated framework.
Independent tests back the hook logic (see [`tests/`](tests/)).

- The auto-verify hook is a **smoke test** (git status, HTTP, log scan), not
  functional/visual proof.
- Hook internals are **coupled to a Hermes version** — verify against yours.
- Prefer **native** Hermes memory/curator where they fit, to avoid duplicating
  this custom work.

---

## License

[Apache-2.0](LICENSE)
