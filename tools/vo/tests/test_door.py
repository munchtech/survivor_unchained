"""Love scenes B (the owner, 6 October; docs/story/LOVE_SCENES.md): the narrator stops at the
door. Behind it a narrator's part is never recorded, locked or not; the bolt, heard from the
stairs, is the one exception, and only word for word. And the lines as written keep it so."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import elevenlabs as E  # noqa: E402
import lines as L  # noqa: E402

DIALOGUE = os.path.join(HERE, "..", "..", "godot", "data", "content", "dialogue.json")
# Where the door opens: the paid room, the free night, the Blind. Every node reached from them is
# behind it, but the gray light at the Blind, which opens outside, in the frost.
ROOTS = (("sella", ("stairs_room", "free_door", "rest_bed")), ("maeca", ("blind",)))
# The only edges from outside into the door. A new way in fails until someone decides its side.
WAYS_IN = {("sella", "stairs_say", "stairs_room"), ("sella", "free_stairs", "free_door"),
           ("sella", "rest_night", "rest_bed"), ("maeca", "blind_ask", "blind")}
OUTSIDE = ("dlg.maeca.blind_morning.",)


class DoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The lines as lines.py would write them now (directions applied), not as last saved.
        cls.lines = {l["id"]: l for l in L.merge(L.build())}

    def test_the_narrator_is_held_behind_the_door_for_good(self):
        for lid in ("dlg.sella.night.0", "dlg.sella.stairs_room.4", "dlg.sella.free_m_kiss.0", "dlg.maeca.blind.1",
                    "dlg.maeca.told_true.0", "dlg.maeca.blind3_morning.0"):
            self.assertEqual(E.held({"id": lid}, "narrator"), E.DOOR_WHY, lid)
            self.assertFalse(E.behind_door({"id": lid}, "sella"), lid)

    def test_the_bolt_and_the_rooms_outside_are_not_behind_it(self):
        for lid in E.DOOR_BOLT:
            self.assertFalse(E.behind_door(self.lines[lid], "narrator"), lid)
        for lid in ("dlg.sella.free_stairs.0", "dlg.sella.stairs.0", "dlg.maeca.blind_walk.0", "dlg.maeca.blind_fire.0",
                    "dlg.maeca.blind_morning.1"):
            self.assertFalse(E.behind_door({"id": lid}, "narrator"), lid)

    def test_the_bolt_is_exempt_only_as_written(self):
        bolt = self.lines["dlg.sella.free_bolt.0"]
        # A's aside pasted back after the bolt, a word of it changed, or no segments to show it: held.
        extra = dict(bolt, segments=bolt["segments"] + [
            {"voice": "narrator", "text": "Her back is still to you. Her forehead is against the door."}])
        changed = dict(bolt, segments=[dict(s, text=s["text"].replace("last coin", "last kiss")) for s in bolt["segments"]])
        for l in (extra, changed, {"id": bolt["id"]}):
            self.assertTrue(E.behind_door(l, "narrator"))
            self.assertEqual(E.held(l, "narrator"), E.DOOR_WHY)

    def test_no_narrator_part_behind_the_door_in_the_lines(self):
        inside = [l for l in self.lines.values() if l["id"].startswith(E.DOOR)]
        self.assertGreater(len(inside), 50)
        for l in inside:
            told = [s["text"] for s in l.get("segments") or [] if s["voice"] == "narrator"]
            self.assertEqual(told, [E.BOLT] if l["id"] in E.DOOR_BOLT else [], l["id"])

    def test_the_saved_lines_are_current(self):
        # The packets are built from manifest.json: stale lines there would pass the door unseen.
        with open(os.path.join(HERE, "manifest.json"), encoding="utf-8") as f:
            man = {l["id"]: l for l in json.load(f)["lines"]}
        now = {i: l for i, l in self.lines.items() if i.startswith(E.DOOR)}
        self.assertEqual(sorted(i for i in man if i.startswith(E.DOOR)), sorted(now), "run tools/vo/lines.py")
        for i, l in now.items():
            self.assertEqual((man[i]["hash"], man[i].get("segments")), (l["hash"], l.get("segments")),
                             f"{i}: manifest.json is stale; run tools/vo/lines.py")

    def test_every_node_behind_the_door_is_in_it(self):
        with open(DIALOGUE, encoding="utf-8") as f:
            d = json.load(f)
        for conv, roots in ROOTS:
            nodes, seen, todo = d[conv]["nodes"], set(), list(roots)
            while todo:
                nid = todo.pop()
                if nid in seen:
                    continue
                seen.add(nid)
                n = nodes[nid]
                todo += [x for x in [n.get("next")] + [c.get("goto") for c in n.get("choices", [])] if x]
            self.assertGreater(len(seen), 5, conv)
            for nid in seen:
                lid = f"dlg.{conv}.{nid}."
                self.assertTrue(lid.startswith(E.DOOR + OUTSIDE), f"{conv}.{nid} is behind the door but not in DOOR")

    def test_the_ways_in_are_known(self):
        with open(DIALOGUE, encoding="utf-8") as f:
            d = json.load(f)
        ways = set()
        for conv, _ in ROOTS:
            nodes = d[conv]["nodes"]
            inside = {k for k in nodes if f"dlg.{conv}.{k}.".startswith(E.DOOR)}
            for k, n in nodes.items():
                if k not in inside:
                    for x in [n.get("next")] + [c.get("goto") for c in n.get("choices", [])]:
                        if x in inside:
                            ways.add((conv, k, x))
        self.assertEqual(ways, WAYS_IN)


if __name__ == "__main__":
    unittest.main()
