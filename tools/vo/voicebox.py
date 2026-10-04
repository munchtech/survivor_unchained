"""Voicebox (jamiepine/voicebox, MIT): a thin client for its REST API, so any
agent or the pipeline can drive it without the app.

Voicebox is a local voice studio over several engines: cloning with Qwen3-TTS
(`qwen`), LuxTTS (`luxtts`), Chatterbox (`chatterbox`), Chatterbox Turbo
(`chatterbox_turbo`, which acts inline tags such as [sigh] and [laugh]) and
HumeAI TADA (`tada`); preset voices from Kokoro (`kokoro`) and Qwen
CustomVoice (`qwen_custom_voice`, which also takes a spoken-style
instruction). A profile is a named voice: reference clips with their words.

    python tools/vo/voicebox.py engines
    python tools/vo/voicebox.py voices
    python tools/vo/voicebox.py profile rook tools/vo/refs/rook.flac "the words in the clip"
    python tools/vo/voicebox.py say rook "Sit down before you fall down." --engine chatterbox_turbo --out take.wav
    python tools/vo/voicebox.py scene scene.json --out takes/
    python tools/vo/voicebox.py free

A scene file is a list of lines: {"voice": profile name, "text": ..., and
optionally "engine", "instruct", "seed", "id" (the file name)}.

The server: start it headless with `python -m backend.main --port 17493
--data-dir DIR` from a Voicebox checkout (`docs/VOICES.md`), or run the app.
VOICEBOX_URL overrides the address (default http://127.0.0.1:17493).
Only the standard library is used, so any Python can run it.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

URL = os.environ.get("VOICEBOX_URL", "http://127.0.0.1:17493")
CLONING = ("qwen", "luxtts", "chatterbox", "chatterbox_turbo", "tada")
PRESETS = ("kokoro", "qwen_custom_voice")
# Which engine each of Voicebox's models belongs to (its status list names models, not engines).
MODEL_ENGINE = {"qwen-tts": "qwen", "qwen-custom-voice": "qwen_custom_voice", "luxtts": "luxtts",
                "chatterbox-tts": "chatterbox", "chatterbox-turbo": "chatterbox_turbo", "tada": "tada", "kokoro": "kokoro"}


class VoiceboxError(RuntimeError):
    pass


class Voicebox:
    def __init__(self, url: str = URL, timeout: float = 900, poll: float = 1.0):
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.poll = poll

    # -- plumbing ---------------------------------------------------------
    def _call(self, method: str, path: str, body=None, raw: bool = False, headers=None):
        data = None
        headers = dict(headers or {})
        if isinstance(body, (bytes, bytearray)):
            data = bytes(body)
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.url + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            try:
                detail = json.loads(detail).get("detail", detail)
            except ValueError:
                pass
            raise VoiceboxError(f"{method} {path}: {e.code} {detail}") from None
        except urllib.error.URLError as e:
            raise VoiceboxError(f"Voicebox is not answering at {self.url} ({e.reason}); start the server first") from None
        if raw:
            return payload
        return json.loads(payload) if payload else None

    @staticmethod
    def _multipart(fields: dict, file_field: str, path: str) -> tuple[bytes, str]:
        boundary = uuid.uuid4().hex
        out = []
        for k, v in fields.items():
            out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
                   f'filename="{os.path.basename(path)}"\r\nContent-Type: {ctype}\r\n\r\n'.encode())
        with open(path, "rb") as f:
            out.append(f.read())
        out.append(f"\r\n--{boundary}--\r\n".encode())
        return b"".join(out), f"multipart/form-data; boundary={boundary}"

    # -- what there is ----------------------------------------------------
    def health(self) -> dict:
        return self._call("GET", "/health")

    def engines(self) -> list[dict]:
        """Every model Voicebox knows, with its engine, and whether it is
        downloaded and loaded."""
        out = []
        for m in self._call("GET", "/models/status")["models"]:
            eng = next((e for p, e in MODEL_ENGINE.items() if m["model_name"].startswith(p)), None)
            if eng:
                out.append({"engine": eng, "model": m["model_name"], "downloaded": bool(m.get("downloaded")),
                            "loaded": bool(m.get("loaded")), "clones": eng in CLONING})
        return out

    def voices(self) -> list[dict]:
        """The profiles (named voices)."""
        return self._call("GET", "/profiles")

    def presets(self, engine: str) -> list[dict]:
        return self._call("GET", f"/profiles/presets/{urllib.parse.quote(engine)}")["voices"]

    def profile(self, name: str) -> dict | None:
        return next((p for p in self.voices() if p["name"] == name), None)

    def download(self, model: str):
        return self._call("POST", "/models/download", {"model_name": model})

    def free(self, model: str | None = None):
        """Unload a model (or every loaded one) to give the GPU back."""
        names = [model] if model else [e["model"] for e in self.engines() if e["loaded"]]
        for n in names:
            self._call("POST", "/models/unload", {"model_name": n})
        return names

    # -- making voices ----------------------------------------------------
    def make_profile(self, name: str, samples: list[tuple[str, str]], description: str | None = None,
                     engine: str | None = None, language: str = "en", replace: bool = False) -> dict:
        """A cloned voice from reference clips, each with the words it says.
        Only clips we have the right to clone (docs/VOICES.md)."""
        old = self.profile(name)
        if old and not replace:
            return old
        if old:
            self._call("DELETE", f"/profiles/{old['id']}")
        p = self._call("POST", "/profiles", {"name": name, "description": description, "language": language,
                                             "voice_type": "cloned", "default_engine": engine})
        for path, words in samples:
            body, ctype = self._multipart({"reference_text": words}, "file", path)
            self._call("POST", f"/profiles/{p['id']}/samples", body, headers={"Content-Type": ctype})
        return self._call("GET", f"/profiles/{p['id']}")

    def preset_profile(self, name: str, engine: str, voice_id: str, language: str = "en") -> dict:
        old = self.profile(name)
        if old:
            return old
        return self._call("POST", "/profiles", {"name": name, "language": language, "voice_type": "preset",
                                                "preset_engine": engine, "preset_voice_id": voice_id})

    # -- making lines -----------------------------------------------------
    def generate(self, voice: str, text: str, out: str, engine: str | None = None, instruct: str | None = None,
                 seed: int | None = None, model_size: str | None = None, language: str = "en",
                 normalize: bool = False) -> dict:
        """One take of a line in a voice (profile name or id), written to `out`.
        Engines that take no instruction ignore `instruct`; Chatterbox Turbo
        takes its direction as inline tags in the text instead."""
        p = self.profile(voice) or {"id": voice}
        req = {"profile_id": p["id"], "text": text, "language": language, "normalize": normalize}
        for k, v in (("engine", engine), ("instruct", instruct), ("seed", seed), ("model_size", model_size)):
            if v is not None:
                req[k] = v
        g = self._call("POST", "/generate", req)
        gid, t0 = g["id"], time.time()
        while g.get("status") not in ("completed", "failed"):
            if time.time() - t0 > self.timeout:
                raise VoiceboxError(f"generation {gid} still {g.get('status')} after {self.timeout:.0f} s")
            time.sleep(self.poll)
            g = self._call("GET", f"/history/{gid}")
        if g["status"] == "failed":
            raise VoiceboxError(f"generation {gid} failed: {g.get('error')}")
        audio = self._call("GET", f"/audio/{gid}", raw=True)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "wb") as f:
            f.write(audio)
        return {"id": gid, "path": out, "duration": g.get("duration"), "engine": g.get("engine"), "seed": g.get("seed"),
                "took": round(time.time() - t0, 1)}

    def scene(self, lines: list[dict], out_dir: str, engine: str | None = None) -> list[dict]:
        """A batch: every line of a scene in order, one file each
        (`<id>.wav`, or the line's number). A failed line is reported, not fatal."""
        done = []
        for i, l in enumerate(lines):
            name = l.get("id") or f"{i:03d}"
            try:
                r = self.generate(l["voice"], l["text"], os.path.join(out_dir, f"{name}.wav"), l.get("engine", engine),
                                  l.get("instruct"), l.get("seed"))
            except VoiceboxError as e:
                r = {"id": None, "error": str(e)}
            done.append({"line": name, **r})
        return done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default=URL)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("engines")
    sub.add_parser("voices")
    p = sub.add_parser("profile")
    p.add_argument("name"); p.add_argument("audio"); p.add_argument("words")
    p.add_argument("--engine"); p.add_argument("--description"); p.add_argument("--replace", action="store_true")
    s = sub.add_parser("say")
    s.add_argument("voice"); s.add_argument("text"); s.add_argument("--out", required=True)
    s.add_argument("--engine"); s.add_argument("--instruct"); s.add_argument("--seed", type=int)
    b = sub.add_parser("scene")
    b.add_argument("file"); b.add_argument("--out", required=True); b.add_argument("--engine")
    f = sub.add_parser("free")
    f.add_argument("model", nargs="?")
    a = ap.parse_args(argv)
    vb = Voicebox(a.url)
    if a.cmd == "engines":
        res = vb.engines()
    elif a.cmd == "voices":
        res = [{k: v[k] for k in ("name", "id", "voice_type", "default_engine", "sample_count")} for v in vb.voices()]
    elif a.cmd == "profile":
        res = vb.make_profile(a.name, [(a.audio, a.words)], a.description, a.engine, replace=a.replace)
    elif a.cmd == "say":
        res = vb.generate(a.voice, a.text, a.out, a.engine, a.instruct, a.seed)
    elif a.cmd == "scene":
        res = vb.scene(json.load(open(a.file, encoding="utf-8")), a.out, a.engine)
    else:
        res = vb.free(a.model)
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    try:
        main()
    except VoiceboxError as e:
        sys.exit(str(e))
