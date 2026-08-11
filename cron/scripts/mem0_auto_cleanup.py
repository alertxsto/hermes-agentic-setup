#!/usr/bin/env python3
"""Auto-cleanup mem0 store for the active user — conservative mode.

Runs via cron daily. Deletes ONLY:
  1. Exact/near-duplicate memories (normalized content match)
  2. Obvious noise (raw casual chat, cron artifacts, model-switch notes, test prompts)
  3. Sensitive leaks (API-key patterns, balance info)

Keeps everything else. Silent (empty stdout) when nothing to delete, so the
cron wrapper stays quiet — watchdog pattern.
"""
import sys
import os
import re
import datetime
from pathlib import Path

# Configurable: the mem0 user id for this agent. Set your own via env.
USER_ID = os.getenv("MEM0_USER_ID", "default-user")

sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))
from mem0_client import HermesMem0

LOG = Path.home() / ".hermes" / "logs" / "mem0_auto_cleanup.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

# --- Noise patterns (conservative: only obvious junk) ---
NOISE_PREFIXES = (
    "gw ", "coba ", "itu ", "sekarang ", "eh ", "nah ", "tapi ", "woi ",
    "suntik ", "nih ", "terus ", "yey ", "saranin ", "gas ", "woi ",
    "nah sekarang", "eh kenapa", "gas loop", "coba lihat", "itu notes",
    "gw mau", "nah api", "terus pas", "eh tapi",
)
NOISE_PHRASES = (
    "[note: model was just switched", "[important: you are running as a scheduled cron",
    "think briefly, then use a terminal", "you've reached the maximum number of tool-calling",
    "[07/08/26", "[07/08/26,", "prd: campushub", "kys.", "kkys.",
    "api key", "saldo toko", "informasi saldo", "balance", "user_md4eag",
)
NOISE_REGEX = (
    re.compile(r"user_[A-Za-z0-9]{16,}", re.I),          # API key leak
    re.compile(r"^\d{2}/\d{2}/\d{2},\s*\d{2}\.\d{2}\.\d{2}", re.M),  # WhatsApp-style log line
)


def is_noise(text: str) -> bool:
    t = text.strip()
    low = t.lower()
    if len(t) < 25:
        return False  # short facts are likely legit preferences — keep
    for p in NOISE_PREFIXES:
        if low.startswith(p):
            return True
    for p in NOISE_PHRASES:
        if p in low:
            return True
    for rx in NOISE_REGEX:
        if rx.search(t):
            return True
    return False


def main():
    m = HermesMem0(enable_llm=False)

    # Enumerate via multi-query search (queries are generic topics; the user id
    # is configurable via env so this is portable).
    queries = ["user prefer", "workflow", "project", "tools", "website", "login",
               "memory", "test", "setup", "server", "config", "note", "cli",
               "inventory", "cron", "provider", "platform", "design"]
    ids = {}
    for q in queries:
        try:
            for r in m.search(USER_ID, q, limit=50).get("results", []):
                ids[r["id"]] = r
        except Exception:
            pass

    by_id = {mid: r for mid, r in ids.items()}
    # --- Dedup by normalized content (keep first) ---
    seen = {}
    dup_ids = []
    for mid, r in by_id.items():
        norm = " ".join(r.get("memory", "").lower().split())
        if norm in seen:
            dup_ids.append(mid)
        else:
            seen[norm] = mid

    # --- Noise + sensitive ---
    noise_ids = [mid for mid, r in by_id.items()
                 if mid not in dup_ids and is_noise(r.get("memory", ""))]

    to_delete = list(set(dup_ids + noise_ids))
    if not to_delete:
        return  # silent — nothing to do

    deleted = 0
    failed = []
    for mid in to_delete:
        try:
            m.memory.delete(memory_id=mid)
            deleted += 1
        except Exception as e:
            failed.append((mid[:8], str(e)))

    # Log + report
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    lines = [f"[{stamp}] total={len(by_id)} deleted={deleted} failed={len(failed)}"]
    with open(LOG, "a") as f:
        f.write("\n".join(lines) + "\n")

    # Non-empty stdout -> cron delivers a short report (deliver=local anyway)
    print(f"mem0 cleanup: {deleted} removed ({len(by_id)} -> {len(by_id) - deleted})")
    if failed:
        print(f"  failed: {failed}")


if __name__ == "__main__":
    main()
