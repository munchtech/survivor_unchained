"""What the voice tools share: where things are, the TTS worker, and how a
take is judged."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GODOT = os.path.join(ROOT, "godot")
OUT_AUDIO = os.path.join(GODOT, "art", "vo")
INDEX = os.path.join(GODOT, "data", "vo", "index.json")
REFS = os.path.join(HERE, "refs")
# Venvs, model caches and every take ever made live outside the repo
# (tools/vo/README.md says how to set them up).
TOOLS = os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools"))
WORK = os.environ.get("VO_WORK", os.path.join(TOOLS, "work"))
FFMPEG = os.environ.get("FFMPEG") or next((p for p in (os.path.join(TOOLS, "ffmpeg", "bin", "ffmpeg.exe"),
                                                       r"C:\Program Files\ShareX\ffmpeg.exe") if os.path.exists(p)), "ffmpeg")
VOXCPM_PY = os.path.join(TOOLS, "voxcpm", "Scripts" if os.name == "nt" else "bin", "python")


def cast() -> dict:
    return json.load(open(os.path.join(HERE, "cast.json"), encoding="utf-8"))["voices"]


class Worker:
    """A TTS model in its own process and venv, asked one take at a time."""

    def __init__(self, python: str, script: str, env: dict | None = None, cwd: str | None = None):
        e = dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {}))
        self.p = subprocess.Popen([python, script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cwd,
                                  stderr=open(os.path.join(TOOLS, f"{os.path.basename(script)}.log"), "a", encoding="utf-8"),
                                  text=True, encoding="utf-8", env=e, bufsize=1)
        self.lock = threading.Lock()
        hello = json.loads(self.p.stdout.readline())
        self.sr = hello.get("sr")

    def ask(self, **req) -> dict:
        with self.lock:
            self.p.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            self.p.stdin.flush()
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("the TTS worker died (see its log in VO_TOOLS)")
            return json.loads(line)

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(30)
        except Exception:
            self.p.kill()


def voxcpm() -> Worker:
    return Worker(VOXCPM_PY, os.path.join(HERE, "backends", "voxcpm_worker.py"))


def seedvc() -> Worker:
    """Seed-VC, run from its own checkout (VO_TOOLS/seed-vc) in its venv."""
    py = os.path.join(TOOLS, "seedvc", "Scripts" if os.name == "nt" else "bin", "python")
    return Worker(py, os.path.join(HERE, "backends", "seedvc_worker.py"), cwd=os.path.join(TOOLS, "seed-vc"))


# What CommonAccent should hear in each part (the FX voices are not judged on it).
ACCENT = {
    "rav": "scotland", "redcowl": "scotland", "ysolde": "scotland",
    "chid": "ireland", "maeca": "wales",
    "snib": None, "grimtunnel": None, "lampling": None, "warden": None, "bones": None, "barrow_lord": None,
    "kerchief_woman": "scotland",
}


def accent_target(voice: str) -> str | None:
    return ACCENT.get(voice, "england")


def f0_range(v: dict) -> tuple[float, float]:
    """A plausible median pitch for the part, Hz."""
    age, sex = v.get("age", 40), v.get("sex", "m")
    if 0 < age <= 12:
        return 220, 360
    if sex == "f":
        return (150, 235) if age < 60 else (140, 240)
    if v.get("deep"):
        return 65, 120
    return (95, 165) if age < 25 else (75, 150)


def judge(report: dict, voice: str, v: dict, want_wps: tuple[float, float] | None = None) -> tuple[float, list[str]]:
    """A take's score (higher is better) and the reasons it must not ship."""
    bad = []
    if report.get("faults"):
        bad.append(f"words wrong: {report['faults']}")
    # Speech from the first frame is how the model starts a take, and the edit
    # gives it its breath of air; a missing first word shows in the words.
    bad += [a for a in report.get("artefacts", []) if a != "cut off at the head"]
    lo, hi = f0_range(v)
    f0 = report.get("pitch", {}).get("f0_median", 0)
    if f0 and not (lo * 0.9 <= f0 <= hi * 1.1) and not v.get("fx"):
        bad.append(f"pitch {f0:.0f} Hz outside {lo}-{hi}")
    target = accent_target(voice)
    acc = report.get("accent_top", {})
    accent_p = acc.get(target, 0.0) if target else 1.0
    if target and accent_p < 0.5:
        bad.append(f"accent heard as {report.get('accent')} ({report.get('accent_p', 0):.2f}), want {target}")
    score = report.get("utmos", 0) + 1.5 * accent_p
    # Expressiveness: a contour that moves (within reason) reads as acted.
    sd = report.get("pitch", {}).get("f0_sd_st", 0)
    score += 0.25 * min(sd, 4.5)
    wps = report.get("words_per_sec", 0)
    if want_wps and wps:
        lo_w, hi_w = want_wps
        if wps < lo_w * 0.8 or wps > hi_w * 1.25:
            bad.append(f"pace {wps:.1f} words/s, want {lo_w}-{hi_w}")
        score -= 0.5 * max(0, lo_w - wps, wps - hi_w)
    return round(score, 3), bad
