#!/usr/bin/env python3
"""Auto-verify hook (optimized) — after a REAL task completes, run lightweight
verification (git clean, service up, real-error scan) and post a verdict to Telegram.

Fires only when:
  - user msg looks like a real build/fix/deploy task (not casual chat)
  - response actually CLAIMS completion (ok/done/beres/fixed)
  - a cooldown window has passed (no spam)
Verification is deterministic and cheap (git status + curl + grep), scoped to THIS
user's repos/services. The verdict distinguishes verified-facts from agent claims.
"""
import os
import re
import time
import subprocess
from pathlib import Path

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_HOME_CHANNEL", "")

MIN_RESPONSE_LEN = 80
COOLDOWN_S = 300          # don't fire more than once per 5 min
COOLDOWN_FILE = Path.home() / ".hermes" / "hooks" / "auto-verify" / ".cooldown"

# Real-task signals — conservative, excludes ambiguous everyday words.
TASK_RE = re.compile(
    r"\b(fix|fixing|setup|install|bikin|buat|buatin|kerjain|kerjakan|beresin|benerin|"
    r"coba (cek|baca|riset|research)|research|riset|delegate|analisa|analisis|"
    r"review|verif|verify|migrate|build|deploy|restart|commit|push|integrasi|integrate)\b",
    re.IGNORECASE,
)
CLAIM_RE = re.compile(r"\b(ok|done|selesai|beres|kelar|fixed|sukses)\b", re.IGNORECASE)

# Ignore task words that leak from normal conversation.
SKIP_MSG_RE = re.compile(r"\b(update|upgrade|add|tambah|hapus|remove|sync|colok|config)\b", re.IGNORECASE)


def _run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _in_cooldown():
    try:
        if COOLDOWN_FILE.exists():
            last = float(COOLDOWN_FILE.read_text().strip() or "0")
            if time.time() - last < COOLDOWN_S:
                return True
        COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
        COOLDOWN_FILE.write_text(str(time.time()))
        return False
    except Exception:
        return False


def _collector():
    """Return (repos, services) parsed from work_prep_collector.sh — the single
    source of truth for active repos and dev services this user runs.
    services is a list of (name, host, port, dev_only)."""
    script = Path.home() / ".hermes" / "scripts" / "work_prep_collector.sh"
    repos = ["skill-arena", "warung-app"]  # safe fallback
    services = []  # list of (name, host, port, dev_only)
    try:
        text = script.read_text()
        # ACTIVE_REPOS=( "a" "b" ... )
        m = re.search(r"ACTIVE_REPOS=\((.*?)\)", text, re.S)
        if m:
            parsed = re.findall(r'"([^"]+)"', m.group(1))
            if parsed:
                repos = parsed
        # check_port "name" "http://host:PORT/..."  [# dev-only]
        for line in re.findall(r'check_port\s+"([^"]+)"\s+"([^"]+)"(.*)$', text, re.M):
            nm, url, tail = line
            pm = re.search(r"localhost:(\d+)", url)
            if pm:
                dev_only = "dev-only" in tail
                services.append((nm, "localhost", int(pm.group(1)), dev_only))
    except Exception:
        pass
    return repos, services


def verify():
    """Return list of (status, msg). status in {'ok','warn','fail'}."""
    checks = []
    home = str(Path.home())
    repos, services = _collector()

    # 1. Repo cleanliness — from collector's ACTIVE_REPOS.
    dirty_repos = []
    for repo in repos:
        out = _run(f"cd {home}/{repo} 2>/dev/null && git status --short 2>/dev/null | head -8")
        if out:
            dirty_repos.append(f"{repo}: {len(out.splitlines())} dirty")
    checks.append(("warn", "📦 Repo dirty: " + "; ".join(dirty_repos)) if dirty_repos
                  else ("ok", "📦 Repo bersih"))

    # 2. Dev services — from collector's check_port entries.
    #    dev-only services (marked `# dev-only`) are NOT expected to run 24/7:
    #    when down we skip them (no false alarm); when up we note them.
    if services:
        for name, host, port, dev_only in services:
            code = _run(f"curl -s -o /dev/null -w '%{{http_code}}' http://{host}:{port}/ --max-time 3")
            if code == "200":
                checks.append(("ok", f"🌐 {name} UP"))
            elif dev_only:
                continue  # normal for dev-only to be down — don't alarm
            elif code:
                checks.append(("warn", f"🌐 {name} HTTP {code}"))
            else:
                checks.append(("warn", f"🌐 {name} down (important)"))
    else:
        code = _run("curl -s -o /dev/null -w '%{http_code}' http://localhost:3100/ --max-time 3")
        checks.append(("ok", "🌐 skill-arena UP") if code == "200"
                      else ("warn", f"🌐 skill-arena HTTP {code or 'down'}"))

    # 3. Real errors only, recent (last 2h). Use a timestamp-bounded grep: only
    #    lines whose leading ISO timestamp is >= 2h ago. Bare traceback continuation
    #    lines (no timestamp) are ignored — we only report the dated ERROR header.
    err = _run(
        f"grep -E 'ERROR|CRITICAL' {home}/.hermes/logs/agent.log 2>/dev/null "
        f"| grep -viE 'stream_error_clean|stream ended|INFO' "
        f"| awk -v cutoff=\"$(date -d '2 hours ago' '+%Y-%m-%d %H:%M:%S')\" "
        f"'/^[0-9]{4}-[0-9]{2}-[0-9]{2}/ && $0 >= cutoff' | tail -3"
    )
    if err:
        excerpt = " | ".join(l[:90] for l in err.splitlines()[:2])
        checks.append(("warn", f"⚠️ Recent ERROR: {excerpt}"))
    else:
        checks.append(("ok", "📋 Log bersih"))

    return checks


async def handle(event_type: str, context: dict):
    if not BOT_TOKEN or not CHAT_ID:
        return
    message = (context.get("message") or "").strip()
    response = (context.get("response") or "").strip()
    if not message or len(response) < MIN_RESPONSE_LEN:
        return
    if not TASK_RE.search(message) or SKIP_MSG_RE.search(message):
        return
    if not CLAIM_RE.search(response):
        return
    if _in_cooldown():
        return  # recently verified, skip to avoid spam

    checks = verify()
    head = (message[:55] + "…") if len(message) > 55 else message
    lines = [f"🧾 **Auto-Verify** · \"{head}\""]
    for status, text in checks:
        icon = "✅" if status == "ok" else ("⚠️" if status == "warn" else "❌")
        lines.append(f"{icon} {text}")
    verdict = "✅ aman" if all(s == "ok" for s, _ in checks) else "⚠️ ada yang perlu dicek"
    lines.append(f"**{verdict}**")

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": "\n".join(lines), "parse_mode": "Markdown"},
                timeout=8,
            )
    except Exception:
        pass