"""The ElevenLabs importer: file names to line ids and parts, refusals and
what is missing, and a line mixed again from a final and a placeholder.

    python -m unittest discover -s tools/vo/tests   (the analysis venv: numpy, scipy, soundfile, ffmpeg)
"""
import json
import os
import sys
import tempfile
import time
import unittest

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import import_takes as it  # noqa: E402

MAN = [
    {"id": "dlg.rook.first.0", "voice": "rook", "status": "todo", "hash": "a",
     "segments": [{"voice": "rook", "text": "Sit down before you fall down."}]},
    {"id": "dlg.brannoc.nell_ditch.1", "voice": "brannoc", "status": "todo", "hash": "b",
     "segments": [{"voice": "narrator", "text": "He puts the hammer down."}, {"voice": "brannoc", "text": "Had the reins."},
                  {"voice": "narrator", "text": "A long breath."}, {"voice": "brannoc", "text": "Always wanted the reins."}]},
    {"id": "dlg.rook.hub.2", "voice": "rook", "status": "skip", "hash": "c", "segments": []},
    {"id": "folk.107.f", "voice": "folk_f1", "status": "todo", "hash": "d", "segments": [{"voice": "folk_f1", "text": "Old Oswin's gone."}]},
]


def tone(path, sec=1.2, sr=44100):
    t = np.arange(int(sec * sr)) / sr
    x = 0.3 * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) + 0.01 * np.random.default_rng(1).standard_normal(len(t))
    x = np.concatenate([np.zeros(int(0.4 * sr)), x, np.zeros(int(0.5 * sr))]).astype(np.float32)
    sf.write(path, x, sr)


class NamesTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(it.parse_name("dlg.rook.first.0.wav"), ("dlg.rook.first.0", None))
        self.assertEqual(it.parse_name("x/dlg.brannoc.nell_ditch.1.p3.mp3"), ("dlg.brannoc.nell_ditch.1", 3))
        self.assertEqual(it.parse_name("folk.107.f (1).wav"), ("folk.107.f", None))
        self.assertEqual(it.parse_name("say.8c1f7c369819.WAV"), ("say.8c1f7c369819", None))
        self.assertIsNone(it.parse_name("notes.txt"))
        self.assertIsNone(it.parse_name("ElevenLabs_2026-10-03T19_20_11_SU Mother Rook.mp3"))


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.finals = tempfile.mkdtemp()
        it.FINALS = self.finals

    def touch(self, name, age=0):
        p = os.path.join(self.dir, name)
        open(p, "wb").write(b"RIFF")
        os.utime(p, (time.time() - age, time.time() - age))
        return p

    def test_matching_refusing_and_missing(self):
        files = [self.touch("dlg.rook.first.0.wav", age=10), self.touch("dlg.rook.first.0 (1).wav"),
                 self.touch("dlg.brannoc.nell_ditch.1.p1.wav"), self.touch("dlg.brannoc.nell_ditch.1.wav"),
                 self.touch("dlg.rook.gone.0.wav"), self.touch("dlg.rook.hub.2.wav"), self.touch("Untitled.mp3"),
                 self.touch("dlg.brannoc.nell_ditch.1.p0.wav")]
        p = it.plan(files, MAN)
        got = {(m["line"], m["part"]): os.path.basename(m["file"]) for m in p["matched"]}
        self.assertEqual(got[("dlg.rook.first.0", 0)], "dlg.rook.first.0 (1).wav")  # the newest copy
        self.assertEqual(got[("dlg.brannoc.nell_ditch.1", 1)], "dlg.brannoc.nell_ditch.1.p1.wav")
        why = {os.path.basename(f): w for f, w in p["refused"]}
        self.assertIn("4 parts", why["dlg.brannoc.nell_ditch.1.wav"])
        self.assertIn("no line dlg.rook.gone.0", why["dlg.rook.gone.0.wav"])
        self.assertIn("not voiced", why["dlg.rook.hub.2.wav"])
        self.assertIn("not a line id", why["Untitled.mp3"])
        # With a voice: another voice's part is refused, and what is left to record is listed.
        p = it.plan(files, MAN, "brannoc")
        why = {os.path.basename(f): w for f, w in p["refused"]}
        self.assertIn("narrator's, not brannoc's", why["dlg.brannoc.nell_ditch.1.p0.wav"])
        self.assertIn("rook's, not brannoc's", why["dlg.rook.first.0 (1).wav"])
        self.assertEqual(p["missing"], ["dlg.brannoc.nell_ditch.1.p3"])
        # A bare name for a shared line is the one part that voice speaks there, if it has only one.
        p = it.plan([self.touch("folk.107.f.wav")], MAN, "folk_f1")
        self.assertEqual([(m["line"], m["part"]) for m in p["matched"]], [("folk.107.f", 0)])


class RebuildTests(unittest.TestCase):
    """A line mixed from a final for one part and the placeholder for the
    other, written into the game folder and the index, still a placeholder;
    then final once both parts are."""

    def test_final_replaces_placeholder(self):
        import lines as lines_mod
        import produce
        tmp = tempfile.mkdtemp()
        it.FINALS = os.path.join(tmp, "finals")
        produce.OUT_AUDIO = os.path.join(tmp, "art")
        produce.INDEX = os.path.join(tmp, "index.json")
        os.makedirs(it.FINALS)
        ph = [os.path.join(tmp, f"ph{i}.wav") for i in range(2)]
        for p in ph:
            tone(p, sr=22050)
        line = {"id": "dlg.test.two.0", "voice": "rook", "status": "done", "hash": "h1", "text": "(She looks.) Sit down.",
                "segments": [{"voice": "narrator", "text": "She looks."}, {"voice": "rook", "text": "Sit down."}],
                "direction": {"vol": "level"},
                "take": {"placeholder": True, "parts": [{"voice": "narrator", "src": ph[0], "seed": 1, "score": 0, "similarity": 0.8,
                                                         "utmos": 3, "accent": "england", "wps": 2, "said": "", "style": "p"},
                                                        {"voice": "rook", "src": ph[1], "seed": 1, "score": 0, "similarity": 0.8,
                                                         "utmos": 3, "accent": "england", "wps": 2, "said": "", "style": "p"}]}}
        tone(it.final_path("dlg.test.two.0", 1, 2))
        take = it.rebuild(line, lambda s: None)
        self.assertTrue(take["placeholder"])
        self.assertEqual(take["final_parts"], [1])
        self.assertTrue(os.path.exists(os.path.join(produce.OUT_AUDIO, take["file"])))
        line.update(take=take)
        produce.write_index([line])
        self.assertTrue(json.load(open(produce.INDEX))["lines"]["dlg.test.two.0"]["placeholder"])
        tone(it.final_path("dlg.test.two.0", 0, 2))
        take = it.rebuild(line, lambda s: None)
        self.assertFalse(take["placeholder"])
        self.assertEqual(take["model"], "elevenlabs")
        line.update(take=take)
        produce.write_index([line])
        self.assertNotIn("placeholder", json.load(open(produce.INDEX))["lines"]["dlg.test.two.0"])
        _ = lines_mod


if __name__ == "__main__":
    unittest.main()
