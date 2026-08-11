# Skill Curation Pattern

**Problem it solves:** skill libraries grow chaotically — overlapping skills,
one-off "skills" born from a single random task, and dozens of near-duplicates.
This makes the library *less* useful, not more.

**The core rule: skills should be CLASS-LEVEL, not one-off.**

A skill belongs in the library only if it captures a **recurring class of work**,
not a single event. We curate aggressively:

## Principle 1 — Merge overlapping skills into umbrellas

When several skills cover the same domain, consolidate into **one umbrella**
skill and move unique references under it. Track the merge so historical links
keep working.

Example: **163 skills → 146** by merging 11 groups:
- Expo/React Native: 6 → 1 umbrella (`expo-react-native-build`) with 8 references
- Cron operations: 2 → 1
- Next.js self-hosting: 4 → 1
- AI judge: 2 → 1
- Repo docs: 2 → 1 …and so on

Merge with `absorbed_into` so cron jobs / references that point at the old skill
are redirected automatically.

## Principle 2 — Delete one-off "skills"

If a skill was created from a single whim (e.g. "make a tribute website once"),
delete it. It's not a pattern — it's clutter. One-off tasks are not skills.

## Principle 3 — Prefer what already exists

Before adding a tool/MCP/skill, check Hermes' native capabilities. Don't add a
skill that duplicates a built-in tool. Fewer, sharper skills beat a bloated
library.

## Principle 4 — Keep skills current

Skills are living documents. After every task, if the loaded skill was missing
a step or had a wrong command, **patch it immediately** — skills that aren't
maintained become liabilities.

## Outcome

A curated, class-level skill library that actually *loads* when needed and stays
accurate — the agent is smarter because its knowledge is focused, not scattered.