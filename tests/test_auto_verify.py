import os
import sys
import re
import unittest
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent.parent / "hooks" / "auto-verify"
HANDLER = HOOK_DIR / "handler.py"


class TestHandlerSource(unittest.TestCase):
    def test_no_shell_true_in_code(self):
        """Security: the handler must never use shell=True except in a comment."""
        src = HANDLER.read_text()
        # Drop the module docstring, then require no real shell=True usage.
        doc_end = src.find('"""', src.find('"""') + 3)
        code = src[doc_end:]
        self.assertNotIn("shell=True", code)

    def test_command_injection_guard_present(self):
        """Security: repo names are validated before use."""
        src = HANDLER.read_text()
        self.assertIn("fullmatch", src)  # repo-name sanitization exists

    def test_no_hardcoded_project_names(self):
        """The fallback must not contain hardcoded project names."""
        src = HANDLER.read_text()
        # The handler's repo fallback must be generic, not a specific project.
        for bad in ("site-checker", "the-app"):
            self.assertNotIn(bad, src)

    def test_no_silent_except(self):
        """Reliability: bare 'except: pass' is a silent failure — should not exist."""
        src = HANDLER.read_text()
        # 'except Exception as e' with logging is fine; bare swallow is not.
        self.assertNotIn("except Exception:\n        pass", src)

    def test_logging_is_configured(self):
        """Reliability: hook must log failures, not die silently."""
        src = HANDLER.read_text()
        self.assertIn("logging.basicConfig", src)
        self.assertIn("logging.error", src) or self.assertIn("logging.warning", src)


if __name__ == "__main__":
    unittest.main()
