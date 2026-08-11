import re
import unittest
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent.parent / "hooks" / "auto-verify"
HANDLER = HOOK_DIR / "handler.py"


def _code():
    src = HANDLER.read_text()
    doc_end = src.find('"""', src.find('"""') + 3)
    return src[doc_end:]


class TestHandlerSource(unittest.TestCase):
    def test_no_shell_true_in_code(self):
        """Security: the handler must never use shell=True except in a comment."""
        self.assertNotIn("shell=True", _code())

    def test_auto_discovers_not_hardcodes(self):
        """The hook auto-discovers projects from disk + collector; it must not
        carry a hardcoded list literal of project names in the fallback."""
        src = _code().lower()
        # It must reference auto-discovery (not a hardcoded repo list).
        self.assertIn("_discover_projects", src)
        # No hardcoded project-name list literal like ["skill-arena", ...]
        self.assertNotIn('["skill-arena"', src)

    def test_no_silent_except(self):
        """No bare 'except: pass' (silent failure)."""
        self.assertNotIn("except Exception:\n        pass", _code())

    def test_logging_is_configured(self):
        """Hook must log failures, not die silently."""
        src = _code()
        self.assertIn("logging.basicConfig", src)
        self.assertIn("logging.error", src) or self.assertIn("logging.warning", src)

    def test_adaptive_detection_present(self):
        """The smart hook must auto-discover projects and detect targets from the task."""
        src = _code()
        self.assertIn("_discover_projects", src)
        self.assertIn("_detect_targets", src)


if __name__ == "__main__":
    unittest.main()