"""Cut an animatic from the timelines the game plays: the boards on the
timeline's own clock, with the placeholder voice, the subtitles, temp sound
and temp music, so the pacing judged here is the pacing the game gets.

    python tools/cinematics/animatic.py c01 "card:Play: the dead, the road, the Barrow" c02 ... \
        --out docs/cinematics/shoot/animatics/prologue.mp4

Each item is a timeline id (godot/data/cinematics/<id>.json) or a card
("card:TEXT", 3 s of grey text on black: what the player does in between).
The survivor it is cut for: --calling warden --sex female --hair long
--background hunter (the defaults are the game's CineContext's).

The schedule is CineSchedule's (logic/Cinema/CinePlayer.cs), number for
number: a shot that fits its lines holds to the end of their takes plus its
tail. A take is the line's entry in godot/data/vo/index.json when it was made
from these words (the hash), timed on `read` (the voice without the room's
tail), else `sec`; a line with no take is timed at CineLines.Reading's pace.

The picture is docs/cinematics/shoot/boards/<id>/s<shot>.jpg (boards.py), or
a slate with the shot's note where there is no board yet; a camera move is a
slow zoom over the move's span. The sound: the VO oggs at their cues; the
cinematic SFX made the way Sfx.Cine makes them (or a recording of that
name from godot/art/sound); a temp bed for each music mood; the zone's
ambience. Encoded with ffmpeg (FFMPEG, or C:/Users/munch/vo-tools/ffmpeg).
A text cut list is written beside the film (<out>.txt).
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GODOT = os.path.join(ROOT, "godot")
BOARDS = os.path.join(ROOT, "docs", "cinematics", "shoot", "boards")
FONTS = os.path.join(GODOT, "art", "fonts")
SOUND = os.path.join(GODOT, "art", "sound")
FFMPEG = os.environ.get("FFMPEG") or next(
    (p for p in [r"C:\Users\munch\vo-tools\ffmpeg\bin\ffmpeg.exe"] if os.path.exists(p)), "ffmpeg")

W, H, FPS, SR = 1920, 1080, 24, 48000
CRF = 24
ASPECT = 2.39
PIC_H = int(round(W / ASPECT))           # 803: the picture between the bars
BAR = (H - PIC_H) // 2                    # 138

# The zone's ambience under each cinematic (the game's AmbienceMix at the
# camera, roughly): bed name -> gain.
AMBIENCE = {
    "c01": {"crickets": 0.30, "fire": 0.22, "water": 0.08},
    "c02": {"water": 0.42, "crickets": 0.10},
    "c03": {"water": 0.40, "crickets": 0.06},
    "c04a": {"water": 0.22, "birds": 0.30},
    "c04b": {"birds": 0.32},
}


# --------------------------------------------------------------- schedule --

def load_json(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


DIALOGUE = None
INDEX = None


def dialogue():
    global DIALOGUE
    if DIALOGUE is None:
        DIALOGUE = load_json(os.path.join(GODOT, "data", "content", "dialogue.json"))
    return DIALOGUE


def text_hash(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def reading(text):
    words = [w for w in re.split(r"[ /]", text) if w]
    return max(1.2, 0.5 + len(words) / 2.6)


class Ctx:
    def __init__(self, calling, background, hair, sex, facts):
        self.calling, self.background, self.hair, self.sex = calling, background, hair, sex
        self.facts = set(facts)


def holds(when, ctx):
    if not when:
        return True
    for k, v in (("calling", ctx.calling), ("background", ctx.background), ("hair", ctx.hair), ("sex", ctx.sex)):
        if when.get(k) is not None and v not in when[k]:
            return False
    for f in when.get("facts") or []:
        if f.startswith("!"):
            if f[1:] in ctx.facts:
                return False
        elif f not in ctx.facts:
            return False
    return True


def find_line(line_id):
    """The line as the game finds it: (vo id, raw words, speaker id). Variants:
    the first, as the animatic does not know the world's facts."""
    conv, node = line_id.split(".", 1)
    c = dialogue()[conv]
    n = c["nodes"][node]
    t = n.get("text", "")
    if isinstance(t, list):
        raw = (t[0].get("text", "") if isinstance(t[0], dict) else t[0]) if t else ""
    else:
        raw = t
    return f"dlg.{conv}.{node}.0", raw, n.get("speaker") or c.get("npc")


def take_of(vo_id, raw):
    t = INDEX.get(vo_id)
    return t if t and t.get("hash") == text_hash(raw) else None


def subtitle(raw):
    """The words as the subtitle shows them (CineLines.Subtitle): a lower-case
    (parenthesis) is how the line is said and is dropped; a capitalised one,
    such as a translation, stays. A direction saying it is sung sets italics."""
    sung = False

    def cut(m):
        nonlocal sung
        if not m.group(1).lstrip()[:1].islower():
            return m.group(0)
        if "sung" in m.group(0).lower():
            sung = True
        return " "
    shown = re.sub(r"\s*\(\s*([^()\s][^()]*)\)\s*", cut, raw)
    shown = re.sub(r"[ \t]{2,}", " ", shown).strip()
    shown = shown.replace(" ,", ",").replace(" ?", "?").replace(" !", "!")
    return shown, sung


def line_seconds(line_id):
    vo, raw, _ = find_line(line_id)
    if raw == "":
        return 0.0
    t = take_of(vo, raw)
    if t:
        return t.get("read") or t["sec"]
    return reading(subtitle(raw)[0])


def offset(at, dur):
    if at is None:
        return 0.0
    if isinstance(at, (int, float)):
        return min(float(at), dur)
    s = at.replace(" ", "")
    if s == "end":
        return dur
    if s.startswith("end-"):
        return max(0.0, dur - float(s[4:]))
    return min(float(s), dur)


def cue_at(at, dur, start, ends, wait=False):
    """CineSchedule.At: Offset, or "after:conv.node+0.4" (that long after a line said ends)."""
    if not (isinstance(at, str) and at.startswith("after:")):
        return offset(at, dur)
    s = at[6:].replace(" ", "")
    m = re.search(r"[+-]", s[max(0, s.find(".")):])
    k = m.start() + max(0, s.find(".")) if m else -1
    lid, add = (s[:k], float(s[k:])) if k > 0 else (s, 0.0)
    if lid not in ends:
        raise SystemExit(f"waits for {lid}, which is not said before it")
    return min(max(ends[lid] + add - start, 0.0), float("inf") if wait else dur)


def schedule(tl, ctx):
    """[(shot, start, dur, [(t, cue)])] and the length, as CineSchedule lays it out:
    a line can run on over a cut, and a cue can wait for a line ("after:")."""
    out, t, ends = [], 0.0, {}
    for shot in tl["shots"]:
        if not holds(shot.get("when"), ctx):
            continue
        cues = [c for c in shot.get("cues", []) if holds(c.get("when"), ctx)]
        dur = float(shot["dur"])
        for c in cues:
            if c["do"] == "line":
                ends[c["id"]] = t + cue_at(c.get("at"), float(shot["dur"]), t, ends, wait=True) + line_seconds(c["id"])
        for lid in shot.get("fit") or []:
            if lid not in ends:
                raise SystemExit(f"{tl['id']} shot {shot['id']}: fits {lid}, which it does not say")
            dur = max(dur, ends[lid] - t + shot.get("tail", 0.6))
        timed = []
        for c in cues:
            ct = t + cue_at(c.get("at"), dur, t, ends)
            if c["do"] == "line":
                ends[c["id"]] = ct + line_seconds(c["id"])
            timed.append((ct, c))
        out.append((shot, t, dur, timed))
        t += dur
    return out, t


# ---------------------------------------------------------------- picture --

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name + ".woff2"), size)


F_WORDS = F_ITAL = F_WHO = F_SLUG = F_TITLE = F_SUB = None


def fonts():
    global F_WORDS, F_ITAL, F_WHO, F_SLUG, F_TITLE, F_SUB
    F_WORDS, F_ITAL = font("alegreya-400", 30), font("alegreya-400-italic", 30)
    F_WHO, F_SLUG = font("alegreya-sans-700", 18), font("alegreya-sans-500", 17)
    F_TITLE, F_SUB = font("cinzel-600", 54), font("alegreya-400-italic", 28)


def wrap(text, f, width):
    lines = []
    for para in text.replace(" / ", "\n").replace("/", "\n").split("\n"):
        cur = ""
        for w in para.split():
            trial = (cur + " " + w).strip()
            if f.getlength(trial) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def slate(tl, shot):
    """No board yet: the shot's number, kind and note, grey on dark."""
    im = Image.new("RGB", (W, PIC_H), (30, 31, 34))
    d = ImageDraw.Draw(im)
    lens = (shot.get("cam") or {}).get("lens")
    d.text((80, 70), f"{tl['id'].upper()}  s{shot['id']}  {shot.get('type', '')}" + (f"  {lens} mm" if lens else ""), font=F_TITLE, fill=(150, 150, 150))
    y = 180
    for ln in wrap(shot.get("note", ""), F_WORDS, W - 160):
        d.text((80, y), ln, font=F_WORDS, fill=(190, 186, 176))
        y += 42
    d.text((80, PIC_H - 60), "(no board yet)", font=F_SLUG, fill=(110, 110, 110))
    return im


def board(tl, shot):
    if shot.get("black"):
        return None
    p = os.path.join(BOARDS, tl["id"], f"s{shot['id']}.jpg")
    if not os.path.exists(p):
        return slate(tl, shot)
    im = Image.open(p).convert("RGB")
    # Fill the 2.39:1 picture, cropping what overhangs.
    k = max(W / im.width, PIC_H / im.height)
    im = im.resize((int(math.ceil(im.width * k)), int(math.ceil(im.height * k))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - PIC_H) // 2
    return im.crop((x, y, x + W, y + PIC_H))


def ease(kind, k):
    k = min(1.0, max(0.0, k))
    if kind == "linear":
        return k
    if kind == "in":
        return k * k
    if kind == "out":
        return 1 - (1 - k) ** 2
    if kind == "slow":
        return k * k * k * (k * (k * 6 - 15) + 10)
    return k * k * (3 - 2 * k)


def move_k(shot, local, dur):
    m = (shot.get("cam") or {}).get("move")
    if not m:
        return None, 0.0
    s = offset(m.get("start"), dur)
    e = dur if m.get("end") is None else offset(m.get("end"), dur)
    k = (local - s) / (e - s) if e > s else (1.0 if local >= s else 0.0)
    return m, ease(m.get("ease", "inout"), k)


def framed(pic, shot, local, dur):
    """A camera move as the board can show it: a push is a slow zoom in, a
    crane a pull back and up, a pan or a tilt a drift toward the new look."""
    m, k = move_k(shot, local, dur)
    if m is None:
        return pic
    if m.get("path"):
        z, dx, dy = 1.10 - 0.10 * k, 0.0, 0.04 * (1 - k)
    elif m.get("push"):
        z, dx, dy = 1.0 + 0.07 * k * (1 if m["push"] > 0 else -1), 0.0, 0.0
    else:
        z, dx, dy = 1.06, 0.0, -0.025 + 0.05 * k
    z = max(1.0, z)
    cw, ch = W / z, PIC_H / z
    cx = (W - cw) / 2 + dx * W
    cy = min(max(0, (PIC_H - ch) / 2 + dy * PIC_H), PIC_H - ch)
    return pic.crop((int(cx), int(cy), int(cx + cw), int(cy + ch))).resize((W, PIC_H), Image.BILINEAR)


# ------------------------------------------------------------------ sound --

_rng = np.random.default_rng(7)


def R(a, b):
    return float(_rng.uniform(a, b))


def env(n, a, hold, d):
    t = np.arange(n) / SR
    e = np.ones(n)
    if a > 0:
        e = np.minimum(e, t / a)
    tail = t - a - hold
    decay = np.where(tail > 0, np.exp(-tail * 6.9 / max(d, 1e-3)), 1.0)
    return e * decay


def lowpass(x, f):
    f = min(max(f, 20), SR / 2.2)
    b, a = signal.butter(2, f / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def bandpass(x, f, q):
    f = min(max(f, 40), SR / 2.4)
    bw = f / max(q, 0.3)
    lo, hi = max(20, f - bw / 2), min(SR / 2.1, f + bw / 2)
    b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


_IR = None


def reverb(x, amount):
    global _IR
    if amount <= 0:
        return x
    if _IR is None:
        n = int(SR * 1.8)
        _IR = _rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
        _IR = lowpass(_IR, 3500) * 0.035
    wet = signal.fftconvolve(x, _IR)[: len(x) + len(_IR)]
    y = np.zeros(len(wet))
    y[: len(x)] += x
    return y + wet * amount


def tone(F, F2=None, A=0.005, D=0.3, Hold=0.0, G=0.1, Type="sine", Lp=None, Lp2=None, Verb=0.0, Pan=0.0, Detune=0.0):
    n = int(SR * (A + Hold + D * 1.6)) + 1
    t = np.arange(n) / SR
    f0 = F * 2 ** (Detune / 1200)
    f1 = (F2 or F) * 2 ** (Detune / 1200)
    span = max(A + Hold + D, 1e-3)
    f = f0 * (f1 / f0) ** np.minimum(t / span, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if Type == "saw":
        x = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif Type == "triangle":
        x = 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    elif Type == "square":
        x = np.sign(np.sin(ph))
    else:
        x = np.sin(ph)
    if Lp:
        x = lowpass(x, (Lp + (Lp2 or Lp)) / 2)
    x = x * env(n, A, Hold, D) * G
    return stereo(reverb(x, Verb), Pan)


def hiss(A=0.005, D=0.3, Hold=0.0, G=0.1, Lp=None, Lp2=None, Bp=None, Bp2=None, Q=1.0, Brown=False, Verb=0.0, Pan=0.0):
    n = int(SR * (A + Hold + D * 1.6)) + 1
    x = _rng.standard_normal(n)
    if Brown:
        x = np.cumsum(x)
        x = x - lowpass(x, 8)
        x /= max(1e-6, np.abs(x).max())
    if Bp:
        x = bandpass(x, (Bp + (Bp2 or Bp)) / 2, Q) * 2.2
    elif Lp:
        x = lowpass(x, (Lp + (Lp2 or Lp)) / 2)
    x = x * env(n, A, Hold, D) * G
    return stereo(reverb(x, Verb), Pan)


def stereo(x, pan=0.0):
    a = (min(max(pan, -1), 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * 1.41


def wav_mono(path):
    import wave
    with wave.open(path) as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    dt = {1: np.int8, 2: np.int16, 4: np.int32}[sw]
    x = np.frombuffer(raw, dt).astype(np.float64) / float(2 ** (8 * sw - 1))
    x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    return x


def decode(path):
    """Any audio file as stereo float at SR (ffmpeg)."""
    p = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def sfx(name, g=1.0, pan=0.0):
    """Sfx.Cine's recipes (src/Audio/Sfx.cs), as near as numpy makes them."""
    parts = []

    def at(dt, x):
        parts.append((dt, x))

    if name == "water_close":
        at(0, hiss(A=0.04, D=1.6, G=0.32 * g, Lp=520, Lp2=110, Brown=True))
        at(0, tone(58, 34, D=1.3, G=0.42 * g))
        for i in range(9):
            at(0.12 + i * R(0.06, 0.14), tone(R(260, 420), R(700, 1100), D=R(0.04, 0.08), G=0.035 * g * (1 - i / 11), Lp=1400, Pan=R(-0.3, 0.3)))
    elif name == "drip":
        at(0, tone(R(1250, 1500), R(520, 640), D=0.09, G=0.11 * g, Verb=0.35, Pan=pan))
        at(0.004, tone(2700, 1800, D=0.03, G=0.04 * g, Pan=pan))
    elif name == "owl":
        for dt, f in ((0.0, 392.0), (0.62, 349.0), (0.9, 349.0)):
            at(dt, tone(f, f * 0.94, Type="triangle", A=0.06, D=0.34, G=0.045 * g, Lp=900, Verb=0.8, Pan=pan))
    elif name == "frost_crack":
        for i in range(14):
            at(i * R(0.03, 0.07), hiss(D=R(0.02, 0.05), G=R(0.05, 0.11) * g, Bp=R(1800, 4200), Q=4, Pan=pan + R(-0.15, 0.15)))
        at(0.55, tone(46, 28, D=1.1, G=0.5 * g))
        at(0.55, hiss(D=0.9, G=0.18 * g, Lp=260, Lp2=90, Brown=True))
    elif name == "roots":
        for i in range(7):
            at(i * R(0.08, 0.16), hiss(D=R(0.06, 0.12), G=0.06 * g, Bp=R(500, 1100), Q=2.5, Brown=True, Pan=pan))
    elif name == "rasp":
        at(0, hiss(A=0.35, D=1.2, G=0.07 * g, Bp=850, Bp2=600, Q=1.6, Brown=True, Pan=pan))
    elif name == "breath_out":
        at(0, hiss(A=0.25, D=1.4, G=0.05 * g, Bp=1500, Bp2=900, Q=0.9, Pan=pan))
    elif name == "cloth_water":
        at(0, hiss(A=0.05, D=0.9, G=0.06 * g, Bp=2400, Q=0.7, Pan=pan))
        for i in range(4):
            at(0.2 + i * R(0.12, 0.2), tone(R(1100, 1500), R(500, 700), D=0.07, G=0.05 * g, Verb=0.3, Pan=pan))
    elif name == "hit":
        at(0, tone(62, 33, D=1.5, G=0.55 * g))
        at(0, hiss(D=0.5, G=0.2 * g, Lp=400, Lp2=100, Brown=True))
        at(0.02, hiss(A=0.05, D=0.9, G=0.06 * g, Bp=3400, Bp2=2600, Q=7, Verb=0.5))
        at(0, tone(110, Type="saw", D=1.8, G=0.05 * g, Lp=700, Lp2=200, Verb=0.6))
    elif name == "drone":
        for f in (55.0, 82.41, 110.0):
            at(0, tone(f, Type="saw", A=4, Hold=3, D=4, G=0.045 * g, Lp=260, Lp2=520, Detune=R(-7, 7), Verb=0.7))
        at(0, hiss(A=4, D=6, G=0.035 * g, Bp=700, Q=1.2, Verb=0.6))
    else:
        rec = recording(name)
        if rec is None:
            print(f"  (no sound '{name}')")
            return np.zeros((1, 2))
        at(0, stereo(rec * 0.3 * g, pan))
    n = max(int(dt * SR) + len(x) for dt, x in parts)
    y = np.zeros((n, 2))
    for dt, x in parts:
        i = int(dt * SR)
        y[i:i + len(x)] += x
    return y


def recording(name):
    """A recording of that family from godot/art/sound (its first take)."""
    for f in (f"{name}.wav", f"{name}_0.wav"):
        p = os.path.join(SOUND, f)
        if os.path.exists(p):
            return wav_mono(p)
    return None


def bed(name, n):
    p = os.path.join(SOUND, f"bed_{name}_0.wav")
    x = wav_mono(p)
    reps = int(math.ceil(n / len(x)))
    y = np.tile(x, reps)[:n]
    return np.stack([y, np.roll(y, SR // 3)], axis=1)


# Temp music: a bed for each of the game's moods (src/Audio/Music.cs), made
# here, to judge where music comes and goes, not what it is.

def music_bed(mood, n):
    t = np.arange(n) / SR
    out = np.zeros((n, 2))

    def add(x, pan=0.0):
        out[:] += stereo(x[:n], pan) if x.ndim == 1 else x[:n]

    if mood in ("night", "mystery"):
        for f, p in ((55.0, -0.3), (82.41, 0.3), (110.0, 0.0)):
            x = lowpass(signal.sawtooth(2 * np.pi * f * t * (1 + R(-0.002, 0.002))), 380)
            add(x * 0.05 * (0.7 + 0.3 * np.sin(2 * np.pi * t / R(5, 9))), p)
        if mood == "night":
            # A low flute: a few slow notes, far apart.
            notes = [293.66, 261.63, 220.0, 196.0, 220.0]
            for i, start in enumerate(np.arange(2.0, n / SR, 6.5)):
                f = notes[i % len(notes)]
                seg = tone(f, f, Type="triangle", A=0.5, Hold=1.4, D=1.2, G=0.035, Lp=1200, Verb=0.6)
                j = int(start * SR)
                out[j:j + len(seg)] += seg[: max(0, n - j)]
        else:
            for start in np.arange(1.0, n / SR, 4.0):
                seg = tone(523.25, 520, D=2.5, G=0.03, Verb=0.9)
                j = int(start * SR)
                out[j:j + len(seg)] += seg[: max(0, n - j)]
    elif mood in ("boss", "combat"):
        bpm = 72 if mood == "boss" else 112
        beat = 60 / bpm
        for start in np.arange(0, n / SR, beat):
            k = int(round(start / beat))
            seg = tone(58 if k % 4 == 0 else 52, 34, D=0.5, G=0.32 if k % 4 == 0 else 0.18)
            thud = hiss(D=0.12, G=0.08, Lp=300, Brown=True)
            seg[: len(thud)] += thud[: len(seg)]
            j = int(start * SR)
            out[j:j + len(seg)] += seg[: max(0, n - j)]
        for f in ((41.2, 61.7, 77.8) if mood == "boss" else (55.0, 65.4)):
            add(lowpass(signal.sawtooth(2 * np.pi * f * t), 300) * 0.05)
    elif mood in ("explore", "town"):
        notes = [392.0, 440.0, 523.25, 587.33, 659.25, 523.25, 440.0]
        step = 0.9 if mood == "explore" else 0.7
        for i, start in enumerate(np.arange(0.5, n / SR, step)):
            if mood == "explore" and i % 4 == 3:
                continue
            f = notes[(i * 3) % len(notes)] / (2 if mood == "town" else 1)
            seg = tone(f, f, Type="triangle", A=0.004, D=0.7, G=0.035, Lp=2400, Verb=0.5, Pan=R(-0.3, 0.3))
            j = int(start * SR)
            out[j:j + len(seg)] += seg[: max(0, n - j)]
        add(lowpass(signal.sawtooth(2 * np.pi * 98.0 * t), 300) * 0.02)
    return out


def music_track(timed, start, length):
    """The music cues as gain curves on a bed per mood (silence cuts dead)."""
    n = int(length * SR) + 1
    gains = {}
    cur, level = None, 0.0
    events = sorted((t, c) for t, c in timed if c["do"] == "music")
    curves = {}

    def curve(m):
        if m not in curves:
            curves[m] = np.zeros(n)
        return curves[m]

    # Walk the cues; between them the level holds.
    last_t = 0.0
    for t, c in events + [(start + length, None)]:
        i0, i1 = int((last_t - start) * SR), int((t - start) * SR)
        if cur and cur != "silence":
            curve(cur)[i0:i1] = level
        if c is None:
            break
        mood = (c.get("mood") or "silence").lower()
        to = c.get("intensity", 0.5)
        over = c.get("over", 0)
        if mood != cur:
            cur, level = mood, to
            if mood != "silence" and over > 0:
                ramp = int(over * SR)
                curve(mood)[i1:i1 + ramp] = np.linspace(0, to, len(curve(mood)[i1:i1 + ramp]))
        else:
            level = to
        last_t = t
    mix = np.zeros((n, 2))
    for m, g in curves.items():
        if g.max() <= 0:
            continue
        mix += music_bed(m, n) * g[:, None] * 1.4
    return mix


# -------------------------------------------------------------------- cut --

class Part:
    def __init__(self, tl, ctx):
        self.tl = tl
        self.shots, self.length = schedule(tl, ctx)


def render(items, ctx, out):
    fonts()
    parts = []
    for it in items:
        if it.startswith("card:"):
            parts.append(("card", it[5:], 3.0))
        else:
            tl = load_json(os.path.join(GODOT, "data", "cinematics", f"{it}.json"))
            p = Part(tl, ctx)
            parts.append(("tl", p, p.length))
    total = sum(p[2] for p in parts)
    n_audio = int(total * SR) + SR
    audio = np.zeros((n_audio, 2))
    cuts, subs, titles, slugs = [], [], [], []
    t0 = 0.0
    for kind, p, length in parts:
        if kind == "card":
            cuts.append(("card", p, t0, length))
            t0 += length
            continue
        tl = p.tl
        narrators = tl.get("narrators", ["narrator"])
        amb = AMBIENCE.get(tl["id"], {})
        n = int(length * SR)
        a0 = int(t0 * SR)
        for name, g in amb.items():
            x = bed(name, n) * g
            fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (SR * 0.6))
            audio[a0:a0 + n] += x * fade[:, None]
        all_cues = []
        for shot, s, dur, timed in p.shots:
            cuts.append(("shot", (tl, shot), t0 + s, dur))
            all_cues += [(t0 + t, c) for t, c in timed]
        audio[a0:a0 + n + 1] += music_track(all_cues, t0, length)[: n_audio - a0][: n + 1]
        for t, c in all_cues:
            i = int(t * SR)
            if c["do"] == "line":
                vo, raw, who = find_line(c["id"])
                if raw == "":
                    continue
                take = take_of(vo, raw)
                shown, sung = subtitle(raw)
                secs = (take["sec"] if take else reading(shown)) + c.get("linger", 0.7)
                if take:
                    x = decode(os.path.join(GODOT, "art", "vo", take["file"]))
                    audio[i:i + len(x)] += x[: n_audio - i]
                name = None if who in narrators else (NAMES.get(who) or who.replace("_", " ").title())
                subs.append((t, t + secs, shown, name, sung))
            elif c["do"] == "sfx":
                x = sfx(c["name"], c.get("gain", 1.0), c.get("pan", 0.0))
                audio[i:i + len(x)] += x[: n_audio - i]
            elif c["do"] == "title":
                titles.append((t, t + c.get("seconds", 3.4), c.get("title", ""), c.get("sub")))
        t0 += length
    peak = np.abs(audio).max()
    if peak > 0.98:
        audio *= 0.98 / peak
    write_cutlist(out, cuts, total)
    encode(out, cuts, subs, titles, audio, total)


def speaker_names():
    """Who a speaker id is on screen, as the game names them (npcs.json: speakers, then npcs)."""
    d = load_json(os.path.join(GODOT, "data", "content", "npcs.json"))
    names = {k: v.get("name") for k, v in d.get("npcs", {}).items() if isinstance(v, dict)}
    names.update({k: v.get("name") for k, v in d.get("speakers", {}).items() if isinstance(v, dict)})
    return {k: v for k, v in names.items() if v}


NAMES = speaker_names()


def write_cutlist(out, cuts, total):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    lines = [f"{'time':>7}  {'dur':>5}  shot"]
    for kind, what, t, dur in cuts:
        if kind == "card":
            lines.append(f"{t:7.2f}  {dur:5.2f}  [card] {what}")
        else:
            tl, shot = what
            lines.append(f"{t:7.2f}  {dur:5.2f}  {tl['id']} s{shot['id']} {shot.get('type', '')}")
    lines.append(f"{total:7.2f}  end")
    with open(os.path.splitext(out)[0] + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def encode(out, cuts, subs, titles, audio, total):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="animatic_")
    wav = os.path.join(tmp, "mix.wav")
    import wave
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    proc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF), "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    cache = {}
    frames = int(math.ceil(total * FPS))
    ci = 0
    for fi in range(frames):
        t = fi / FPS
        while ci + 1 < len(cuts) and cuts[ci + 1][2] <= t:
            ci += 1
        kind, what, s, dur = cuts[ci]
        frame = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(frame)
        if kind == "card":
            k = min(1, (t - s) / 0.4, (s + dur - t) / 0.4)
            g = int(170 * max(0, k))
            lines = wrap(what, F_WORDS, W - 400)
            y = H // 2 - len(lines) * 21
            for ln in lines:
                d.text(((W - F_ITAL.getlength(ln)) / 2, y), ln, font=F_ITAL, fill=(g, g, g))
                y += 42
        else:
            tl, shot = what
            key = (tl["id"], shot["id"])
            if key not in cache:
                cache.clear()
                cache[key] = board(tl, shot)
            pic = cache[key]
            if pic is not None:
                frame.paste(framed(pic, shot, t - s, dur), (0, BAR))
            lens = (shot.get("cam") or {}).get("lens")
            slug_l = f"{tl['id'].upper()}  {tl.get('title', '')}"
            slug_r = f"s{shot['id']}  {shot.get('type', '')}" + (f"  {lens} mm" if lens else "") + f"   {t - s:4.1f} / {dur:.1f} s"
            d.text((40, 52), slug_l, font=F_SLUG, fill=(120, 120, 120))
            d.text((W - 40 - F_SLUG.getlength(slug_r), 52), slug_r, font=F_SLUG, fill=(120, 120, 120))
            for a, b, title, sub in titles:
                if a <= t < b:
                    k = min(1, (t - a) / 0.5, (b - t) / 0.6)
                    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    od = ImageDraw.Draw(ov)
                    al = int(255 * max(0, k))
                    tw = F_TITLE.getlength(title.upper())
                    od.text(((W - tw) / 2, H / 2 - 60), title.upper(), font=F_TITLE, fill=(236, 228, 212, al))
                    if sub:
                        od.text(((W - F_SUB.getlength(sub)) / 2, H / 2 + 10), sub, font=F_SUB, fill=(200, 186, 150, al))
                    frame.paste(ov, (0, 0), ov)
                    d = ImageDraw.Draw(frame)
        for a, b, raw, name, sung in subs:
            if a <= t < b:
                k = min(1.0, (b - t) / 0.25)
                f = F_ITAL if name is None or sung else F_WORDS
                lines = wrap(raw, f, 1100)[:2]
                base = H - BAR + max(12, (BAR - 40 * len(lines)) / 2) + (8 if name else 0)
                col = tuple(int(c * k) for c in (236, 228, 212))
                if name:
                    gold = tuple(int(c * k) for c in (200, 180, 138))
                    d.text(((W - F_WHO.getlength(name.upper())) / 2, base - 26), name.upper(), font=F_WHO, fill=gold)
                for j, ln in enumerate(lines):
                    d.text(((W - f.getlength(ln)) / 2, base + j * 40), ln, font=f, fill=col)
        proc.stdin.write(frame.tobytes())
        if fi % (FPS * 20) == 0:
            print(f"  {t:6.1f} / {total:.1f} s")
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(out, f"{total:.1f} s")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("items", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--calling", default="warden")
    ap.add_argument("--background", default="hunter")
    ap.add_argument("--hair", default="long")
    ap.add_argument("--sex", default="female")
    ap.add_argument("--facts", default="")
    ap.add_argument("--index", default=os.path.join(GODOT, "data", "vo", "index.json"))
    ap.add_argument("--plan", action="store_true", help="print the schedule only")
    ap.add_argument("--crf", type=int, default=24, help="x264 quality: 28 keeps a committed cut small")
    a = ap.parse_args()
    global INDEX, CRF
    CRF = a.crf
    INDEX = load_json(a.index)["lines"]
    ctx = Ctx(a.calling, a.background, a.hair, a.sex, [f for f in a.facts.split(",") if f])
    if a.plan:
        for it in a.items:
            if it.startswith("card:"):
                continue
            tl = load_json(os.path.join(GODOT, "data", "cinematics", f"{it}.json"))
            shots, length = schedule(tl, ctx)
            print(f"{it}: {length:.2f} s, {len(shots)} shots")
            for shot, s, dur, _ in shots:
                print(f"  {s:6.2f} {dur:5.2f}  s{shot['id']} {shot.get('type', '')}")
        return
    render(a.items, ctx, a.out)


if __name__ == "__main__":
    main()
