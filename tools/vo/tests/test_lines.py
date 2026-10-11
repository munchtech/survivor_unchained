"""Who says what in a line (docs/VOICES.md): capitalised parentheses are the
narrator's, lower-case ones are how the person says it, and quotes inside
narration in a person's conversation are that person's."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lines import segments, build, text_hash  # noqa: E402


class SegmentTests(unittest.TestCase):
    def test_a_lower_case_parenthesis_is_acted_not_read(self):
        s = segments("Finders keepers, surface-m— (a sniff) ...Downstairs'll be ever so grateful.", "grimtunnel")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["voice"], "grimtunnel")
        self.assertEqual(s[0]["text"], "Finders keepers, surface-m— ...Downstairs'll be ever so grateful.")
        self.assertEqual(s[0]["acted"], "Finders keepers, surface-m— [a sniff] ...Downstairs'll be ever so grateful.")

    def test_a_direction_at_the_start_or_end(self):
        s = segments("(quietly) Pack it up.", "redcowl")
        self.assertEqual(s, [{"voice": "redcowl", "text": "Pack it up.", "acted": "[quietly] Pack it up."}])
        s = segments("Lie down. (sung, under the water)", "warden")
        self.assertEqual(s, [{"voice": "warden", "text": "Lie down.", "acted": "Lie down. [sung, under the water]"}])

    def test_a_capitalised_parenthesis_is_the_narrators(self):
        s = segments("(He puts the hammer down.) ...Had the reins. (A long breath, through the nose.) She'd want the reins.", "brannoc")
        self.assertEqual([(x["voice"], x["text"]) for x in s], [
            ("narrator", "He puts the hammer down."), ("brannoc", "...Had the reins."),
            ("narrator", "A long breath, through the nose."), ("brannoc", "She'd want the reins.")])

    def test_quotes_in_narration_go_to_the_person(self):
        s = segments('In the dark, much later, she says into your shoulder, "You told me anyway," and nothing else.', "narrator", "sella")
        self.assertEqual([(x["voice"], x["text"]) for x in s], [
            ("narrator", "In the dark, much later, she says into your shoulder,"), ("sella", "You told me anyway,"),
            ("narrator", "and nothing else.")])

    def test_narration_without_an_owner_keeps_its_quotes(self):
        t = 'In his belt-book: "Lamps at the Low Ford lit again." "Dannet not back."'
        self.assertEqual(segments(t, "narrator"), [{"voice": "narrator", "text": t}])


class CodeLineTests(unittest.TestCase):
    """The clock's DayLines and the story fights' pulls are in the manifest."""

    @classmethod
    def setUpClass(cls):
        cls.lines = build()

    def test_a_clock_line_is_the_narrators(self):
        t = "You get up. It takes less than it did."
        hits = [l for l in self.lines if l["id"] == "say." + text_hash(t)]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["voice"], "narrator")
        self.assertEqual(hits[0]["const"], "DayLines.RiseAgain")

    def test_dusk_is_the_gate_guards(self):
        t = "Lamps are lit. Stay where they reach."
        hits = [l for l in self.lines if l["id"].startswith("say.") and l["text"] == t]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["voice"], "guard")
        self.assertEqual(hits[0]["who"], "Gate guard")

    def test_tracker_labels_are_not_lines(self):
        texts = {l["text"] for l in self.lines}
        self.assertNotIn("Answer the night", texts)
        self.assertNotIn("Also out tonight:", texts)

    def test_story_fight_pulls_are_found(self):
        self.assertGreaterEqual(sum(1 for l in self.lines if l.get("const", "").endswith(".Pull")), 4)

    def test_ids_are_unique(self):
        ids = [l["id"] for l in self.lines]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
