"""The Voicebox client against a fake Voicebox (no GPU, no models):

    python -m unittest discover -s tools/vo/tests
"""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from voicebox import Voicebox, VoiceboxError  # noqa: E402

WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + bytes(28)


class Fake:
    """Just enough of Voicebox's REST API, recording what it was asked."""

    def __init__(self):
        self.profiles, self.samples, self.gens, self.asked, self.unloaded = {}, {}, {}, [], []
        self.fail_text = "FAIL"

    def handle(self, method, path, body, ctype):
        self.asked.append((method, path))
        if method == "GET" and path == "/health":
            return 200, {"status": "healthy"}
        if method == "GET" and path == "/models/status":
            return 200, {"models": [
                {"model_name": "qwen-tts-1.7B", "downloaded": True, "loaded": True},
                {"model_name": "chatterbox-turbo", "downloaded": True, "loaded": False},
                {"model_name": "kokoro", "downloaded": False, "loaded": False},
                {"model_name": "whisper-turbo", "downloaded": True, "loaded": True},
            ]}
        if method == "POST" and path == "/models/unload":
            self.unloaded.append(json.loads(body)["model_name"])
            return 200, {"message": "ok"}
        if method == "GET" and path == "/profiles":
            return 200, list(self.profiles.values())
        if method == "POST" and path == "/profiles":
            d = json.loads(body)
            pid = f"p{len(self.profiles) + 1}"
            self.profiles[pid] = {**d, "id": pid, "sample_count": 0}
            return 200, self.profiles[pid]
        if path.startswith("/profiles/") and path.endswith("/samples") and method == "POST":
            pid = path.split("/")[2]
            assert ctype.startswith("multipart/form-data"), ctype
            self.samples.setdefault(pid, []).append(body)
            self.profiles[pid]["sample_count"] += 1
            return 200, {"id": "s1", "profile_id": pid}
        if path.startswith("/profiles/") and method == "GET":
            return 200, self.profiles[path.split("/")[2]]
        if path.startswith("/profiles/") and method == "DELETE":
            self.profiles.pop(path.split("/")[2])
            return 200, {}
        if method == "POST" and path == "/generate":
            d = json.loads(body)
            if d["profile_id"] not in self.profiles:
                return 404, {"detail": "Profile not found"}
            gid = f"g{len(self.gens) + 1}"
            self.gens[gid] = {**d, "id": gid, "status": "generating", "polls": 0}
            return 200, {"id": gid, "status": "generating"}
        if method == "GET" and path.startswith("/history/"):
            g = self.gens[path.split("/")[2]]
            g["polls"] += 1
            if g["polls"] >= 2:
                g["status"] = "failed" if self.fail_text in g["text"] else "completed"
                g["error"] = "engine fell over" if g["status"] == "failed" else None
                g["duration"] = 1.5
            return 200, g
        if method == "GET" and path.startswith("/audio/"):
            return 200, WAV
        return 404, {"detail": "Not Found"}


class Handler(BaseHTTPRequestHandler):
    def _go(self, method):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        code, out = self.server.fake.handle(method, self.path, body, self.headers.get("Content-Type", ""))
        data = out if isinstance(out, bytes) else json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._go("GET")

    def do_POST(self):
        self._go("POST")

    def do_DELETE(self):
        self._go("DELETE")

    def log_message(self, *a):
        pass


class VoiceboxClientTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.fake = self.fake = Fake()
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.vb = Voicebox(f"http://127.0.0.1:{self.server.server_port}", timeout=10, poll=0.01)
        self.tmp = tempfile.mkdtemp()
        self.ref = os.path.join(self.tmp, "ref.wav")
        with open(self.ref, "wb") as f:
            f.write(WAV)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_engines_are_named_and_other_models_left_out(self):
        e = {x["engine"]: x for x in self.vb.engines()}
        self.assertEqual(set(e), {"qwen", "chatterbox_turbo", "kokoro"})
        self.assertTrue(e["qwen"]["loaded"] and e["qwen"]["clones"])
        self.assertFalse(e["kokoro"]["clones"])

    def test_a_profile_is_made_from_reference_audio_with_its_words(self):
        p = self.vb.make_profile("rook", [(self.ref, "Sit down before you fall down.")], engine="chatterbox_turbo")
        self.assertEqual(p["sample_count"], 1)
        self.assertEqual(p["default_engine"], "chatterbox_turbo")
        body = self.fake.samples[p["id"]][0]
        self.assertIn(b'name="reference_text"', body)
        self.assertIn(b"Sit down before you fall down.", body)
        self.assertIn(b'filename="ref.wav"', body)
        # Asking again finds it instead of making a second.
        self.assertEqual(self.vb.make_profile("rook", [(self.ref, "x")])["id"], p["id"])
        self.assertEqual(len(self.fake.profiles), 1)

    def test_a_line_is_generated_with_its_direction_and_written(self):
        self.vb.make_profile("holloway", [(self.ref, "words")])
        out = os.path.join(self.tmp, "takes", "liar.wav")
        r = self.vb.generate("holloway", "So. Tell me why.", out, engine="qwen_custom_voice",
                             instruct="cold fury, held down", seed=3)
        self.assertEqual(open(out, "rb").read(), WAV)
        self.assertEqual(r["duration"], 1.5)
        asked = next(iter(self.fake.gens.values()))
        self.assertEqual((asked["engine"], asked["instruct"], asked["seed"]), ("qwen_custom_voice", "cold fury, held down", 3))
        self.assertNotIn("model_size", asked)

    def test_a_failed_generation_says_why(self):
        self.vb.make_profile("sella", [(self.ref, "words")])
        with self.assertRaisesRegex(VoiceboxError, "engine fell over"):
            self.vb.generate("sella", "FAIL here", os.path.join(self.tmp, "x.wav"))

    def test_a_scene_is_batched_and_a_bad_line_does_not_stop_it(self):
        self.vb.make_profile("rook", [(self.ref, "words")])
        res = self.vb.scene([{"voice": "rook", "text": "One.", "id": "a"},
                             {"voice": "rook", "text": "FAIL two."},
                             {"voice": "nobody", "text": "Three.", "id": "c"},
                             {"voice": "rook", "text": "Four.", "id": "d", "engine": "luxtts"}],
                            os.path.join(self.tmp, "scene"), engine="chatterbox")
        self.assertEqual([r["line"] for r in res], ["a", "001", "c", "d"])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "scene", "a.wav")))
        self.assertIn("engine fell over", res[1]["error"])
        self.assertIn("Profile not found", res[2]["error"])
        self.assertEqual([g["engine"] for g in self.fake.gens.values()], ["chatterbox", "chatterbox", "luxtts"])

    def test_free_unloads_what_is_loaded(self):
        self.assertEqual(self.vb.free(), ["qwen-tts-1.7B"])
        self.assertEqual(self.fake.unloaded, ["qwen-tts-1.7B"])

    def test_no_server_is_a_plain_error(self):
        with self.assertRaisesRegex(VoiceboxError, "not answering"):
            Voicebox("http://127.0.0.1:9").health()


if __name__ == "__main__":
    unittest.main()
