# Skill Library — the real capability surface

The agent's procedural knowledge, loaded on demand when a task matches. Numbers
below are counted from the live filesystem (`~/.hermes/skills`), not guessed.

**Total: 147 skills.**

## 🏆 Power skills (what makes this setup distinctive)

| Skill | What it enables |
|---|---|
| **`ai-website-judge`** + `skillarena-judge-ops` | Fully-automatic **AI website judging**: a Playwright crawler walks a site (SPA discovery, per-page crawl, post-auth sweep, mobile routes, budget) and a vision-LLM scores it. A whole self-hosted product. |
| **`agy-coordinator`** | Orchestrate **Agy agents**: PLAN → user approve → parallel EXECUTE → verify. Multi-agent coding. |
| **`mem0-integration`** | **Unlimited semantic memory** beyond Hermes' built-in cap — PostgreSQL + pgvector + fastembed, injected every session. |
| **`ai-agent-orchestration-patterns`** | Run orchestrator agents safely: stuck-detection, ops discipline, never kill. |
| **6 × security skills** | Linux audit-log intrusion, web-server threat detection, MCP tool-poisoning audit, CT-log monitoring, API security testing, AI prompt-injection detection. |
| **`structured-multi-crawler-research`** | Multi-crawler deep research into categorized folders (used for real research projects). |
| **`taste-*`** (7) | Anti-slop design system: default, editorial, soft-calm, strict-GSAP, image-gen, redesign, complete-output — the agent ships UI that doesn't look AI-generated. |
| **`webreaper`** | Fast, free, MIT scraper — a self-hosted Firecrawl alternative (bot-protection, stealth). |
| **`hermes-memory-maintenance`** | Keeps the agent's own memory healthy: audit, dedupe, expand caps, archive to skills. |

## By directory (live count)

| Directory | Skills | Purpose |
|---|---|---|
| **root (uncategorized)** | 16 | security (6), design (design-critique, design-taste-frontend, frontend-design, frontend-ui-engineering, impeccable), hermes-memory-maintenance, user-response-style, apple |
| **autonomous-ai-agents** | 22 | agy/codex/claude-code/opencode orchestration, browser automation, mem0, multi-profile |
| **creative** | 17 | architecture-diagram, excalidraw, manim-video, ascii-art, design systems |
| **devops** | 20 | cloudflared tunnels, cron ops, LVM, self-hosted webapp, 9Router, power monitor |
| **email** | 2 | himalaya IMAP/SMTP, inbox triage |
| **firecrawl** | (plugin) | scrape/search/crawl/deep-research via the Firecrawl MCP |
| **github** | 10 | PR workflow, code review, issue hunting, OSS contributions |
| **media** | 3 | youtube-transcript, gif-search, songsee |
| **mlops** | 7 | llama-cpp, vllm, HF hub, eval harness, skill injection |
| **note-taking** | 1 | obsidian vault |
| **productivity** | 15 | docx, xlsx, powerpoint, notion, pdf, maps, meetings |
| **research** | 8 | arxiv, blogwatcher, grounded-citations, polymarket, multi-crawler |
| **smart-home** | 1 | openhue |
| **social-media** | 1 | xurl (X/Twitter) |
| **software-development** | 21 | ai-website-judge, TDD, systematic-debugging, spike, simplify-code, webreaper |
| **taste** | 7 | anti-slop design: default, editorial, soft-calm, gsap, image-gen, redesign |

## MCP servers (7 enabled)

The agent's real-time external tools:

| Server | Purpose |
|---|---|
| `github` | repos / PRs / issues |
| `chrome-devtools` | browser automation |
| `postgres` | SQL |
| `firecrawl` | web scrape/search/crawl/extract |
| `memory` | knowledge graph |
| `context7` | up-to-date library docs |
| `sequential-thinking` | structured reasoning |

## Curation rules

- **147 skills**, actively curated — overlapping groups merged into class-level
  umbrellas over time (a real pass took 163 → 146, then grew to 147).
- **Class-level only** — a skill captures a recurring pattern, never a one-off
  whim. One-off tasks are deleted.
- **Prefer native** — don't add a skill/MCP that duplicates what Hermes already
  does.
- **Patch immediately** — a wrong/outdated skill is fixed the moment it's found.

> Skills are procedural memory. They're what makes the agent "know how" instead
> of guessing.