#!/usr/bin/env python3
"""Auto-verify hook — after a REAL task completes, run cheap deterministic checks
(git clean, service up, recent-error scan) and post a verdict to Telegram.

Security & reliability notes:
  - Uses shell=False everywhere (no command injection from parsed repo/service
    names). No `shell=True`.
  - Never silently swallows failures: every exception is logged to a hook log
    file so a dead hook is visible, not silent.
  - Repo/service list is read from the telemetry collector; generic defaults are
    used only as a last resort (no hardcoded personal project names).

Fires only when all four guards pass: real task + completion claim + substantial
reply + cooldown window open.
"""
import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_HOME_CHANNEL", "")

MIN_RESPONSE_LEN = 80
COOLDOWN_S = 300
COOLDOWN_FILE = Path.home() / ".hermes" / "hooks" / "auto-verify" / ".cooldown"
LOG_DIR = Path.home() / ".hermes" / "hooks" / "auto-verify"
LOG_FILE = LOG_DIR / "hook.log"

logging.basicConfig(
    filename=str(LOG_FILE), level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Real-task signals — conservative, excludes ambiguous everyday words.
TASK_RE = re.compile(
    r"\b(fix|fixing|setup|install|bikin|buat|buatin|kerjain|kerjakan|beresin|benerin|"
    r"coba (cek|baca|riset|research)|research|riset|delegate|analisa|analisis|"
    r"review|verif|verify|migrate|build|deploy|restart|commit|push|integrasi|integrate)\b",
    re.IGNORECASE,
)
CLAIM_RE = re.compile(r"\b(ok|done|selesai|beres|kelar|fixed|sukses)\b", re.IGNORECASE)
SKIP_MSG_RE = re.compile(r"\b(update|upgrade|add|tambah|hapus|remove|sync|colok|config)\b", re.IGNORECASE)


def _run(argv, cwd=None, timeout=8):
    """Run a command with NO shell (argv list). Returns stdout or '' on failure.
    Failures are logged, not swallowed."""
    import subprocess
    try:
        r = subprocess.run(argv, shell=False, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return r.stdout.strip()
    except Exception as e:
        logging.warning("command failed: %r — %s", argv, e)
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
    except Exception as e:
        logging.warning("cooldown check failed: %s", e)
        return False  # fail open: don't block a verification on cooldown errors


def _collector():
    """Parse (repos, services) from the telemetry collector — single source of
    truth. Returns generic defaults if the script is missing/unparseable."""
    script = Path.home() / ".hermes" / "scripts" / "work_prep_collector.sh"
    repos = []       # empty -> no repo checks (graceful, not false positives)
    services = []    # list of (name, host, port, dev_only)
    try:
        text = script.read_text()
        m = re.search(r"ACTIVE_REPOS=\((.*?)\)", text, re.S)
        if m:
            parsed = re.findall(r'"([^"]+)"', m.group(1))
            repos = parsed
        for line in re.findall(r'check_port\s+"([^"]+)"\s+"([^"]+)"(.*)$', text, re.M):
            nm, url, tail = line
            pm = re.search(r"localhost:(\d+)", url)
            if pm:
                services.append((nm, "127.0.0.1", int(pm.group(1)), "dev-only" in tail))
    except Exception as e:
        logging.warning("collector parse failed: %s", e)
    return repos, services


def verify():
    """Return list of (status, msg). status in {'ok','warn','fail'}."""
    checks = []
    home = Path.home()
    repos, services = _collector()

    # 1. Repo cleanliness. Empty repos -> skip (no false positives on a fork).
    if repos:
        dirty = []
        for repo in repos:
            # sanitize: only simple names, never pass arbitrary strings to a shell
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
                logging.warning("skipping repo with unsafe name: %r", repo)
                continue
            out = _run(["git", "status", "--short"], cwd=str(home / repo))
            if out:
                dirty.append(f"{repo}: {len(out.splitlines())} dirty")
        checks.append(("warn", "📦 Repo dirty: " + "; ".join(dirty)) if dirty
                      else ("ok", "📦 Repo bersih"))

    # 2. Service health. dev-only services skipped when down (expected).
    for name, host, port, dev_only in services:
        url = f"http://{host}:{port}/"
        code = _run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url, "--max-time", "3"])
        if code == "200":
            checks.append(("ok", f"🌐 {name} UP"))
        elif dev_only:
            continue
        elif code:
            checks.append(("warn", f"🌐 {name} HTTP {code}"))
        else:
            checks.append(("warn", f"🌐 {name} down (important)"))

    # 3. Real errors in the agent log, last 2h, noise filtered. Pure Python —
    #    no shell pipeline.
    log_path = home / ".hermes" / "logs" / "agent.log"
    if log_path.exists():
        cutoff = datetime.now() - timedelta(hours=2)
        errs = []
        with log_path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not re.match(r"^\d{4}-\d{2}-\d{2}", line):
                    continue  # only dated header lines
                if "ERROR" not in line and "CRITICAL" not in line:
                    continue
                if any(n in line for n in ("stream_error_clean", "stream ended", "INFO")):
                    continue
                try:
                    ts = datetime.fromisoformat(line[0:19].replace(" ", "T"))
                except Exception:
                    continue
                if ts >= cutoff:
                    errs.append(line.strip())
        if errs:
            checks.append(("warn", "⚠️ Recent ERROR: " + " | ".join(e[:90] for e in errs[:2])))
        else:
            checks.append(("ok", "📋 Log bersih"))
    else:
        checks.append(("ok", "📋 (no agent log)"))

    return checks


async def handle(event_type: str, context: dict):
    if not BOT_TOKEN or not CHAT_ID:
        logging.warning("auto-verify skipped: BOT_TOKEN/CHAT_ID not set")
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
        return

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
            r = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": "\n".join(lines), "parse_mode": "Markdown"},
                timeout=8,
            )
            if r.status_code != 200:
                logging.warning("telegram send failed: HTTP %s", r.status_code)
    except Exception as e:
        logging.error("telegram send failed: %s", e)