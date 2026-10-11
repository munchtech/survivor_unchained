"""A lock binds words, not ids (tools/vo/lock.py)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lock import status  # noqa: E402


class LockStatusTests(unittest.TestCase):
    locks = {"dlg.a.0": {"hash": "abc", "by": "x", "date": "2026-10-11"}}

    def test_ok_when_the_hash_matches(self):
        self.assertEqual(status(self.locks, "dlg.a.0", "abc"), "ok")

    def test_broken_when_the_words_changed(self):
        self.assertEqual(status(self.locks, "dlg.a.0", "def"), "broken")

    def test_gone_when_the_id_is_gone(self):
        self.assertEqual(status(self.locks, "dlg.a.0", None), "gone")

    def test_unlocked_lines_have_no_status(self):
        self.assertEqual(status(self.locks, "dlg.b.0", "abc"), "")


if __name__ == "__main__":
    unittest.main()
