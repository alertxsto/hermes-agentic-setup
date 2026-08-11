import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HOOK_DIR = Path(__file__).resolve().parent.parent / "hooks" / "auto-verify"
sys.path.insert(0, str(HOOK_DIR))

import handler  # noqa: E402


def _synthetic_projects():
    """A small, deterministic project map (no dependency on real $HOME)."""
    return {
        "alpha": {"dir": "/tmp/alpha", "port": 3100, "dev_only": False,
                  "aliases": {"alpha", "alpha-app"}},
        "beta": {"dir": "/tmp/beta", "port": 8081, "dev_only": True,
                 "aliases": {"beta", "beta-web"}},
    }


class TestDetectTargets(unittest.TestCase):
    def test_matches_project_by_name(self):
        out = handler._detect_targets("gas beresin bug di alpha", _synthetic_projects())
        self.assertIn("alpha", out)

    def test_matches_by_alias(self):
        out = handler._detect_targets("kerjain alpha-app dong", _synthetic_projects())
        self.assertIn("alpha", out)

    def test_empty_when_no_project_mentioned(self):
        out = handler._detect_targets("gas beresin bug itu aja", _synthetic_projects())
        self.assertEqual(out, [])

    def test_case_insensitive(self):
        out = handler._detect_targets("FIX ALPHA NOW", _synthetic_projects())
        self.assertIn("alpha", out)


class TestCheckProject(unittest.TestCase):
    def setUp(self):
        self.proj = {"dir": "/tmp/x", "port": 3100, "dev_only": False, "aliases": {"x"}}

    def test_clean_repo_and_up_service_is_ok(self):
        # _run returns '' (clean git) then '200' (service up)
        with mock.patch.object(handler, "_run", side_effect=["", "200"]):
            out = handler._check_project("x", self.proj)
        statuses = [s for s, _ in out]
        self.assertIn("ok", statuses)
        self.assertNotIn("warn", statuses)

    def test_dirty_repo_is_warn(self):
        # _run returns 'file1\nfile2' (dirty git)
        with mock.patch.object(handler, "_run", side_effect=["file1\nfile2", "200"]):
            out = handler._check_project("x", self.proj)
        self.assertTrue(any(s == "warn" for s, _ in out))

    def test_service_down_is_warn(self):
        # _run returns '' (clean git) then '' (service down -> no code)
        with mock.patch.object(handler, "_run", side_effect=["", ""]):
            out = handler._check_project("x", self.proj)
        self.assertTrue(any(s == "warn" for s, _ in out))

    def test_dev_only_down_is_ok(self):
        # dev-only service down should NOT warn (it's expected to be off)
        proj = {"dir": None, "port": 8081, "dev_only": True, "aliases": {"b"}}
        with mock.patch.object(handler, "_run", return_value=""):
            out = handler._check_project("b", proj)
        self.assertNotIn("warn", [s for s, _ in out])


class TestCooldown(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cooldown = Path(self.tmpdir) / ".cooldown"
        self.patcher = mock.patch.object(handler, "COOLDOWN_FILE", self.cooldown)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if self.cooldown.exists():
            self.cooldown.unlink()

    def test_second_call_within_window_is_true(self):
        self.assertFalse(handler._in_cooldown())  # first call sets it
        self.assertTrue(handler._in_cooldown())   # second call within 5 min

    def test_after_window_is_false(self):
        self.assertFalse(handler._in_cooldown())
        # Simulate the window passing: write an old timestamp.
        self.cooldown.write_text(str(0))
        self.assertFalse(handler._in_cooldown())


class TestHandlerSource(unittest.TestCase):
    @staticmethod
    def _source():
        with open(HOOK_DIR / "handler.py") as f:
            return f.read()

    def test_no_shell_true_in_code(self):
        self.assertNotIn("shell=True", self._source())

    def test_auto_discovers_not_hardcodes(self):
        src = self._source().lower()
        self.assertIn("_discover_projects", src)
        self.assertNotIn('["skill-arena"', src)

    def test_no_silent_except(self):
        self.assertNotIn("except Exception:\n        pass", self._source())

    def test_logging_is_configured(self):
        src = self._source()
        self.assertIn("logging.basicConfig", src)
        self.assertIn("logging.error", src) or self.assertIn("logging.warning", src)


if __name__ == "__main__":
    unittest.main()