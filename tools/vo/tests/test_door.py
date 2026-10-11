"""Love scenes B (the owner, 6 October; docs/story/LOVE_SCENES.md): the narrator stops at the
door. Behind it a narrator's part is never recorded, locked or not; the bolt, heard from the
stairs, is the one exception. And the lines as written keep it so."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import elevenlabs as E  # noqa: E402


class DoorTests(unittest.TestCase):
    def test_the_narrator_is_held_behind_the_door_for_good(self):
        for lid in ("dlg.sella.night.0", "dlg.sella.stairs_room.4", "dlg.sella.free_m_kiss.0", "dlg.maeca.blind.1",
                    "dlg.maeca.told_true.0", "dlg.maeca.blind3_morning.0"):
            self.assertEqual(E.held({"id": lid}, "narrator"), E.DOOR_WHY, lid)
            self.assertFalse(E.behind_door({"id": lid}, "sella"), lid)

    def test_the_bolt_and_the_rooms_outside_are_not_behind_it(self):
        for lid in ("dlg.sella.free_bolt.0", "dlg.sella.free_sleep_bed.0", "dlg.sella.free_stairs.0", "dlg.sella.stairs.0",
                    "dlg.maeca.blind_walk.0", "dlg.maeca.blind_fire.0", "dlg.maeca.blind_morning.1"):
            self.assertFalse(E.behind_door({"id": lid}, "narrator"), lid)

    def test_no_narrator_part_behind_the_door_in_the_lines(self):
        man = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))["lines"]
        inside = [l for l in man if l["id"].startswith(E.DOOR)]
        self.assertGreater(len(inside), 50)
        for l in inside:
            voices = [s["voice"] for s in l.get("segments") or []]
            if l["id"] in E.DOOR_BOLT:
                self.assertEqual(voices[0], "narrator", l["id"])
                continue
            self.assertNotIn("narrator", voices, l["id"])


if __name__ == "__main__":
    unittest.main()
