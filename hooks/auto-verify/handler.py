#!/usr/bin/env python3
"""Auto-verify hook (smart) — after a REAL task completes, verify the project
the task actually touched, plus a concise overall health check.

What makes it adaptive instead of checking every service:
  - Project map is auto-discovered from git repos on disk + the collector's
    check_port entries (no hardcoded personal list).
  - The task message is scanned for the project(s) it references; only those
    are verified in detail.
  - A brief overall (log scan, sect summary) catches anything else.
  - If no project is matched, it falls back to checking the whole set briefly.

Security: shell=False everywhere, markdown-escaped output, all failures logged.
Fires only when all four guards pass: real task + completion claim + substantial
reply + cooldown window open.
"""
import os
import re
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_HOME_CHANNEL", "")

MIN_RESPONSE_LEN = 80
COOLDOWN_S = 300
COOLDOWN_FILE = Path.home() / ".hermes" / "hooks" / "auto-verify" / ".cooldown"
LOG_DIR = Path.home() / ".hermes" / "hooks" / "auto-verify"
LOG_FILE = LOG_DIR / "hook.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# Real-task signals — conservative.
TASK_RE = re.compile(
    r"\b(fix|fixing|setup|install|bikin|buat|buatin|kerjain|kerjakan|beresin|benerin|"
    r"coba (cek|baca|riset|research)|research|riset|delegate|analisa|analisis|"
    r"review|verif|verify|migrate|build|deploy|restart|commit|push|integrasi|integrate)\b",
    re.IGNORECASE,
)
CLAIM_RE = re.compile(r"\b(ok|done|selesai|beres|kelar|fixed|sukses)\b", re.IGNORECASE)
SKIP_MSG_RE = re.compile(r"\b(update|upgrade|add|tambah|hapus|remove|sync|colok|config)\b", re.IGNORECASE)


def _escape_markdown(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'(?<!\\)([_*`\[])', r'\\\1', str(text))


def _run(argv, cwd=None, timeout=8):
    """Run with NO shell. Returns stdout or '' on failure."""
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
        return False


def _discover_projects():
    """Return dict project_name -> {dir, port, dev_only, aliases}.
    Auto-discovered: git repos in $HOME, plus check_port entries from the
    collector (aliases from name + slug). Nothing hardcoded."""
    home = Path.home()
    # Repos in $HOME that are git repos
    projects = {}
    for d in home.iterdir():
        if d.is_dir() and (d / ".git").exists():
            name = d.name
            projects[name] = {"dir": str(d), "port": None, "dev_only": False, "aliases": {name}}
    # Ports / aliases from the collector's check_port lines
    script = home / ".hermes" / "scripts" / "work_prep_collector.sh"
    try:
        text = script.read_text()
        for nm, url, tail in re.findall(r'check_port\s+"([^"]+)"\s+"([^"]+)"(.*)$', text, re.M):
            pm = re.search(r"localhost:(\d+)", url)
            if not pm:
                continue
            slug = nm.split()[0].lower().strip()  # e.g. "skill-arena" from "(Expo)"
            key = slug if slug in projects else nm.lower().replace(" ", "_")
            if key not in projects:
                projects[key] = {"dir": None, "port": int(pm.group(1)),
                                 "dev_only": "dev-only" in tail, "aliases": {nm.lower()}}
            else:
                projects[key]["port"] = int(pm.group(1))
                projects[key]["dev_only"] = "dev-only" in tail
            projects[key]["aliases"].add(nm.lower())
    except Exception as e:
        logging.warning("collector parse failed: %s", e)
    # Add generic aliases: full slug + snake/camel variants. Skip per-part
    # splitting (e.g. "skill-arena" -> "skill") which caused false positives.
    for name, p in list(projects.items()):
        slug = name.lower().replace("_", "-").replace(" ", "-")
        p["aliases"].add(slug)
    return projects


def _detect_targets(message, projects):
    """Return list of project names referenced in the task message."""
    msg = message.lower()
    hits = []
    for name, p in projects.items():
        # match the primary name or any alias as a whole/regex word
        for alias in p["aliases"]:
            if re.search(r"\b" + re.escape(alias) + r"\b", msg):
                hits.append(name)
                break
    # dedupe, keep order
    return list(dict.fromkeys(hits))


def _check_project(name, p):
    """Verify one project: repo clean (if dir) + service up (if port). Returns list[(status,msg)]."""
    out = []
    # Repo cleanliness
    if p["dir"]:
        dirty = _run(["git", "status", "--short"], cwd=p["dir"])
        if dirty:
            out.append(("warn", f"📂 {_escape_markdown(name)}: {len(dirty.splitlines())} file bersi belum commit"))
        else:
            out.append(("ok", f"📂 {_escape_markdown(name)}: bersih"))
    # Service
    if p["port"]:
        url = f"http://127.0.0.1:{p['port']}/"
        code = _run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url, "--max-time", "3"])
        esc = _escape_markdown(name)
        if code == "200":
            out.append(("ok", f"🌐 {esc}: UP"))
        elif p["dev_only"]:
            out.append(("ok", f"🌐 {esc}: off (dev-only — normal)"))
        elif code:
            out.append(("warn", f"🌐 {esc}: HTTP {code} — cek! (port {p['port']})"))
        else:
            out.append(("warn", f"🌐 {esc}: MATI — port {p['port']} gak jalan. Cek proses."))
    return out


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

    projects = await asyncio.to_thread(_discover_projects)
    targets = _detect_targets(message, projects)

    # If no project detected, fall back to whole set (brief). Limit to avoid spam.
    if not targets:
        # prefer projects that have a service port (more meaningful), cap ~5
        targets = [n for n, p in projects.items() if p["port"]][:5]

    checks = []
    for name in targets:
        checks += await asyncio.to_thread(_check_project, name, projects[name])

    # Overall: log error scan + sector summary
    head = (message[:50] + "…") if len(message) > 50 else message
    lines = [f"🧾 **Auto-Verify** · \"{_escape_markdown(head)}\""]
    lines.append(f"   fokus: {_escape_markdown(', '.join(targets) or 'seluruh')}")
    for status, text in checks:
        icon = "✅" if status == "ok" else "⚠️"
        lines.append(f"{icon} {text}")

    # Log error scan (overall, cheap)
    log_path = Path.home() / ".hermes" / "logs" / "agent.log"
    errs = []
    if log_path.exists():
        cutoff = datetime.now() - timedelta(hours=2)
        with log_path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.match(r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})", line)
                if not m or ("ERROR" not in line and "CRITICAL" not in line):
                    continue
                if any(n in line for n in ("stream_error_clean", "stream ended", "INFO")):
                    continue
                # Filter infra/routine noise that recurs and is not actionable for
                # a coding task (webhook route reload, etc.).
                if any(n in line.lower() for n in (
                    "webhook] failed to reload", "webhook reload",
                    "reload dynamic routes", "route reload")):
                    continue
                try:
                    if datetime.fromisoformat(m.group(1).replace(" ", "T")) >= cutoff:
                        errs.append(line.strip())
                except Exception:
                    continue
    if errs:
        lines.append(f"⚠️ Log: {len(errs)} error dalam 2 jam — {_escape_markdown(errs[-1][:70])}")
    else:
        lines.append("✅ Log bersih")

    warns = sum(1 for s, _ in checks if s == "warn") + (1 if errs else 0)
    verdict = "⚠️ ada yang perlu dicek" if warns else "✅ aman"
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