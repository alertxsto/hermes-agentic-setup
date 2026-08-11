"""Mem0 session loader — injects semantic memories into Hermes persistent
memory (MEMORY.md) on session:start, so a fresh agent's frozen system-prompt
memory block includes mem0 recall.

Mechanism (verified 2026-08 against hermes-agent source):
  - Gateway fires "session:start" for a NEW session (gateway/run.py) before the
    AIAgent for that session is initialized.
  - agent_init.py calls MemoryStore.load_from_disk(), which snapshots
    MEMORY.md/USER.md into the agent's frozen system-prompt memory block.
  - Hook emit() discards return values, so injection must happen by WRITING a
    recall section into MEMORY.md on session:start. load_from_disk() then picks
    it up and it lands in the system prompt of the fresh session.
  - MEMORY.md stays well-formed (bare-§ separators) and size-capped so the
    memory tool keeps round-tripping.
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Use Hermes' own atomic writer so this hook never races/partially-writes the
# same MEMORY.md that the built-in memory tool also writes (lost-update safe).
_HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"
if str(_HERMES_AGENT) not in sys.path:
    sys.path.insert(0, str(_HERMES_AGENT))
try:
    from utils import atomic_write_text
    _ATOMIC = True
except Exception:
    _ATOMIC = False

SCRIPTS_DIR = Path.home() / ".hermes" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from mem0_client import HermesMem0
    MEM0_AVAILABLE = True
except Exception:
    MEM0_AVAILABLE = False
    HermesMem0 = None

MEMORY_MD = Path.home() / ".hermes" / "memories" / "MEMORY.md"
LOG_DIR = Path.home() / ".hermes" / "hooks" / "mem0-session-loader"

RECALL_TITLE = "Mem0 Recall (auto, session start)"
MARK_OPEN = f"[{RECALL_TITLE}]"
MARK_CLOSE = f"[/{RECALL_TITLE}]"


def _now() -> str:
    return datetime.now().isoformat()


def _log_error(msg: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (LOG_DIR / "errors.log").open("a") as f:
            f.write(f"[{_now()}] {msg}\n")
    except Exception:
        pass


def _log_load(session_id: str, memories: list) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": _now(),
            "event": "session:start",
            "session_id": session_id,
            "memories_loaded": len(memories),
            "memories": memories,
        }
        with (LOG_DIR / "memory_loads.jsonl").open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _strip_old_recall(text: str) -> str:
    # Remove any prior recall block regardless of heading level (# or ##) so
    # repeated runs stay idempotent (never accumulate duplicates).
    marker_name = re.escape(RECALL_TITLE)
    close_name = re.escape(MARK_CLOSE)
    pat = re.compile(
        r"(?:^|\n)[#]+\s+" + marker_name + r"[\s\S]*?" + close_name,
        re.MULTILINE,
    )
    return pat.sub("", text)


def _write_text_atomic(path: Path, content: str) -> None:
    if _ATOMIC:
        atomic_write_text(path, content, encoding="utf-8", tmp_prefix=".memrecall_")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as tf:
            tf.write(content)
            tmp_name = tf.name
        os.replace(tmp_name, path)


async def handle(event_type: str, context: dict):
    """Load relevant mem0 memories and inject them into MEMORY.md."""
    if not MEM0_AVAILABLE:
        _log_error("mem0_client import failed; recall skipped")
        return

    user_id = context.get("user_id") or os.getenv("MEM0_USER_ID", "default-user")
    session_id = context.get("session_id") or "unknown"

    try:
        mem0 = HermesMem0(enable_llm=False)
        results = mem0.search(
            user_id,
            "preference setup workflow tool language environment project goal memory",
            limit=8,
        )
        items = [r.get("memory", "").strip() for r in results.get("results", []) if r.get("memory")]
        if not items:
            return

        recall = []
        for it in items[:6]:
            it = it.lstrip("- ").strip()
            recall.append(it if len(it) <= 150 else it[:147] + "...")

        existing = MEMORY_MD.read_text(encoding="utf-8") if MEMORY_MD.exists() else "# MEMORY.md\n"

        # Remove any previous recall block from a prior run so it never accumulates.
        existing = _strip_old_recall(existing)

        # Always write exactly ONE heading level so repeated runs stay idempotent.
        block_lines = ["", "# " + RECALL_TITLE, MARK_OPEN]
        block_lines += ["- " + it for it in recall]
        block_lines.append(MARK_CLOSE)
        block = "\n".join(block_lines) + "\n"

        new_content = existing.rstrip("\n") + "\n" + block

        # Budget guard: if still > 3600 chars, keep only the top 3 items.
        if len(new_content) > 3600:
            new_content = _strip_old_recall(new_content)
            tiny = ["", "# " + RECALL_TITLE, MARK_OPEN]
            tiny += ["- " + it for it in recall[:3]]
            tiny.append(MARK_CLOSE)
            new_content = new_content.rstrip("\n") + "\n" + "\n".join(tiny) + "\n"

        _write_text_atomic(MEMORY_MD, new_content)
        _log_load(session_id, recall)

    except Exception as e:
        _log_error(f"session:start error for {session_id}: {e}")