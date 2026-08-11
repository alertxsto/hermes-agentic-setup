#!/usr/bin/env python3
"""Taste summary hook — after a task completes, post a compact Taste summary to Telegram.

Security & reliability notes:
  - Reads taste rules from ~/.hermes/.commandcode/taste/taste/taste.md (fallback default).
  - Clips response to ~48 characters.
  - Never crashes (catches all exceptions and logs them).
  - Uses Telegram Markdown parse_mode with escaped text.
"""
import os
import re
import logging
from pathlib import Path

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_HOME_CHANNEL", "")

LOG_DIR = Path.home() / ".hermes" / "hooks" / "taste-summary"
LOG_FILE = LOG_DIR / "hook.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE), level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

TASTE_FILE = Path.home() / ".hermes" / ".commandcode" / "taste" / "taste" / "taste.md"

DEFAULT_RULES = [
    "Prefer small, reviewable diffs — confidence 0.9",
    "Never over-engineer — confidence 0.8",
]


def _escape_markdown(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'(?<!\\)([_*`\[])', r'\\\1', str(text))


def _load_taste_rules() -> list[str]:
    try:
        if TASTE_FILE.exists():
            content = TASTE_FILE.read_text(encoding="utf-8").strip()
            if content:
                rules = []
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith(("-", "*", "•")):
                        line = line.lstrip("-*• ").strip()
                    if line and not line.startswith("#"):
                        rules.append(line)
                if rules:
                    return rules[:2]
    except Exception as e:
        logging.warning("failed to read taste rules from %s: %s", TASTE_FILE, e)
    return DEFAULT_RULES


async def handle(event_type: str, context: dict):
    try:
        if not BOT_TOKEN or not CHAT_ID:
            logging.warning("taste-summary skipped: BOT_TOKEN/CHAT_ID not set")
            return

        resp_text = (context.get("response") or "").strip()
        if not resp_text:
            resp_text = (context.get("message") or "").strip()

        if not resp_text:
            return

        clean_resp = " ".join(resp_text.split())
        if len(clean_resp) > 48:
            clipped = clean_resp[:45] + "…"
        else:
            clipped = clean_resp

        rules = _load_taste_rules()

        lines = ["*Taste:*"]
        for rule in rules:
            lines.append(f"• {_escape_markdown(rule)}")
        lines.append(f"▸ {_escape_markdown(clipped)}")

        msg_text = "\n".join(lines)

        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg_text, "parse_mode": "Markdown"},
                timeout=8,
            )
            if r.status_code != 200:
                logging.warning("telegram send failed: HTTP %s", r.status_code)
    except Exception as e:
        logging.error("taste-summary hook failed: %s", e, exc_info=True)
