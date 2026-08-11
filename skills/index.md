# Skill Library Index

A high-level view of how the skill library is organized. Full details in
[`patterns/skill-curation.md`](../patterns/skill-curation.md).

## By category

| Category | Purpose | Examples |
|---|---|---|
| **autonomous-ai-agents** | spawning & orchestrating agents | agy-coordinator, codex, browser-automation, merge-reconciler |
| **creative** | design, ASCII/art, video, diagrams | architecture-diagram, excalidraw, manim-video |
| **devops** | infra, tunnels, self-hosting, backups | cloudflared-tunnel, hermes-cron-operations, lvm-storage |
| **email** | inbox triage, IMAP/SMTP | himalaya, email-inbox-triage |
| **github** | repo/PR/issue workflows | github-pr-workflow, github-code-review |
| **media** | youtube transcripts, gifs, audio | youtube-transcript-processor, gif-search |
| **mlops** | llm serving, evaluation, HF hub | llama-cpp, vllm, evaluating-llms-harness |
| **note-taking** | vaults & notes | obsidian |
| **productivity** | docs/spreadsheets/presentations | docx, xlsx, powerpoint, notion |
| **research** | papers, market data, monitoring | arxiv, blogwatcher, grounded-citations |
| **security** | audit, intrusion, scenario-hardening | analyzing-*-logs, ct-logs, api-security |
| **software-development** | coding QA, debugging, builds | ai-website-judge, systematic-debugging, webreaper |
| **taste** | anti-slop design rules | taste-default, taste-editorial, taste-soft-calm |

## Curation facts

- **146 skills** total after merging 11 overlapping groups (was 163). See
  [`patterns/skill-curation.md`](../patterns/skill-curation.md).
- **`taste-*`** (6 sub-aesthetics), **`github/*`**, **`creative/*`**,
  **`firecrawl/*`** are intentionally NOT merged — each is a distinct concern.
- Skills are **class-level**: no one-off task ever becomes a skill.

## How a skill gets added / improved

1. **Create** only for a recurring class of work (5+ step, non-trivial workflow).
2. **Load it** whenever relevant — skills are scanned before acting.
3. **Patch** immediately when a loaded skill is outdated, wrong, or missing a step.
4. **Merge/delete** overlaps and one-offs during library hygiene.

> Skills are procedural memory. Keep them sharp.