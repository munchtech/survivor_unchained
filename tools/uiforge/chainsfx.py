"""The tab chain's sound from real chain recordings (CC0; the owner approved public-domain
sounds on 2026-10-05; tools/comfy/in/sfx/SOURCES.md has their pages, authors and hashes):
clean single clinks cut from them, pitched down and given a low body for weight, a rattle bed
for the drag, and a heavy settle. The game plays them as Clips (art/sound/chainLink_N.wav and
the rest), one clink for each link that runs into the eyelet, timed by the slide spring.

    python tools/uiforge/chainsfx.py takes     # cut and make the takes into tools/comfy/out/uiforge/sfx/
    python tools/uiforge/chainsfx.py apply     # into godot/art/sound/ with sounds.json, and the ledger lines

Until the owner records a real chain of our own, these stand in; theirs replaces them.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import resample_poly

import sfxpreview as SP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ROOT))), "")   # the main checkout
SRC = os.environ.get("SFX_IN", r"C:/Users/munch/Desktop/survivorsunchained/tools/comfy/in/sfx")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "sfx")
RATE = SP.RATE

# What each take is cut from (pack folder, file) and its page, for the ledger.
SOURCES = {
    "chain_01": ("oga_80-CC0-RPG-SFX_0", "chain_01.ogg"),
    "chain_02": ("oga_80-CC0-RPG-SFX_0", "chain_02.ogg"),
    "chain_03": ("oga_80-CC0-RPG-SFX_0", "chain_03.ogg"),
    "metal_01": ("oga_80-CC0-RPG-SFX_0", "metal_01.ogg"),
    "metalClick": ("kenney_rpg-audio", "Audio/metalClick.ogg"),
    "metalLatch": ("kenney_rpg-audio", "Audio/metalLatch.ogg"),
    "metalPot1": ("kenney_rpg-audio", "Audio/metalPot1.ogg"),
    "heavy0": ("kenney_impact-sounds", "Audio/impactMetal_heavy_000.ogg"),
    "heavy1": ("kenney_impact-sounds", "Audio/impactMetal_heavy_001.ogg"),
    "winch8": ("oga_winch", "winch - Marker #8.wav"),
    "winch9": ("oga_winch", "winch - Marker #9.wav"),
}
PAGES = {
    "oga_80-CC0-RPG-SFX_0": ("https://opengameart.org/content/80-cc0-rpg-sfx", "rubberduck", "CC0"),
    "kenney_rpg-audio": ("https://kenney.nl/assets/rpg-audio", "Kenney Vleugels (Kenney.nl)", "CC0 1.0"),
    "kenney_impact-sounds": ("https://kenney.nl/assets/impact-sounds", "Kenney Vleugels (Kenney.nl)", "CC0 1.0"),
    "oga_winch": ("https://opengameart.org/content/chain-winch-sounds", "bart", "CC0"),
}


def load(key):
    """A source as float mono at 44.1 kHz (ffmpeg reads ogg and wav alike)."""
    import imageio_ffmpeg
    pack, rel = SOURCES[key]
    p = os.path.join(SRC, pack, rel)
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", p, "-f", "s16le", "-ac", "1", "-ar", str(RATE), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def onsets(x, thr=0.25, gap=0.035):
    """Where strikes start: the envelope's sharp rises above `thr` of its peak, `gap` apart."""
    hop = int(0.003 * RATE)
    e = np.array([np.abs(x[i:i + hop]).max() for i in range(0, len(x) - hop, hop)])
    e = e / (e.max() + 1e-9)
    rise = np.diff(e, prepend=0)
    out, lastt = [], -1.0
    for i in range(len(e)):
        t = i * hop / RATE
        if e[i] > thr and rise[i] > thr * 0.5 and t - lastt > gap:
            out.append(i * hop)
            lastt = t
    return out


def cut(x, at, length=0.18, pre=0.004, tail=0.6):
    """A clink from `at`: a hair before it, faded out over its last `tail` part."""
    a = max(0, at - int(pre * RATE))
    b = min(len(x), a + int(length * RATE))
    s = x[a:b].copy()
    n = len(s)
    f = np.ones(n, np.float32)
    k = int(n * tail)
    f[n - k:] = np.linspace(1, 0, k) ** 2
    f[:int(0.001 * RATE)] = np.linspace(0, 1, int(0.001 * RATE))
    return s * f


def pitch(x, factor):
    """Lower (factor < 1) or raise by resampling, as a slower tape would: heavier, longer."""
    up, down = int(round(1000 / factor)), 1000
    g = math.gcd(up, down)
    return resample_poly(x, up // g, down // g).astype(np.float32)


def norm(x, peak=0.85):
    return (x * (peak / max(1e-6, np.abs(x).max()))).astype(np.float32)


def takes():
    """The takes, made from the sources: clinks, drags, settles."""
    rng = np.random.default_rng(11)
    src = {k: load(k) for k in SOURCES}
    clinks = []
    for k in ("chain_01", "chain_02", "chain_03", "metalClick", "metalLatch"):
        x = src[k]
        for o in onsets(x):
            c = cut(x, o, 0.16)
            # A clink is short and bright at its start: skip what is a rumble or a smear.
            head = np.abs(c[:int(0.01 * RATE)]).max()
            if head > 0.5 * np.abs(c).max() and np.abs(c).max() > 0.08:
                clinks.append((k, o, c))
    rng.shuffle(clinks)
    body = pitch(cut(src["heavy0"], onsets(src["heavy0"])[0], 0.22), 0.55)
    made, used = {}, set()
    for i, (k, o, c) in enumerate(clinks[:8]):
        # Pitched down for weight, a little body of a heavy strike under it.
        p = SP.biquad(pitch(c, rng.uniform(0.6, 0.7)), "low", 6500)
        b = body[:len(p)] if len(body) >= len(p) else np.pad(body, (0, len(p) - len(body)))[:len(p)]
        made[f"chainLink_{i}"] = norm(p + b * 0.35 * np.abs(p).max() / max(1e-6, np.abs(b).max()))
        used.update({k, "heavy0"})
    for i, k in enumerate(("winch8", "winch9")):
        x = src[k]
        # The drag: a third of a second of chain running through, from where it runs steadiest
        # (as long as the slide, so the game plays it whole).
        win = int(0.34 * RATE)
        e = np.convolve(np.abs(x), np.ones(2205) / 2205, mode="same")
        start = int(np.argmax(e[win:-win]) + win - win // 2)
        seg = x[start:start + win].copy()
        seg *= np.minimum(1, np.minimum(np.arange(win) / (0.06 * RATE), (win - np.arange(win)) / (0.12 * RATE)))
        made[f"chainDrag_{i}"] = norm(SP.biquad(pitch(seg, 0.85), "low", 3200), 0.6)
        used.add(k)
    for i, (h, c) in enumerate((("heavy0", "chain_03"), ("heavy1", "chain_02"))):
        hv = pitch(cut(src[h], onsets(src[h])[0], 0.5, tail=0.8), 0.62)
        ch = src[c]
        tail = pitch(cut(ch, onsets(ch)[-1], 0.5, tail=0.8), 0.8)
        n = max(len(hv), len(tail))
        mix = np.pad(hv, (0, n - len(hv))) * 0.9 + np.pad(tail, (0, n - len(tail))) * 0.5
        made[f"chainSettle_{i}"] = norm(mix)
        used.update({h, c})
    return made, used


def save(x, path):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def build():
    os.makedirs(OUT, exist_ok=True)
    made, used = takes()
    for k, x in made.items():
        save(x, os.path.join(OUT, k + ".wav"))
    json.dump(sorted(used), open(os.path.join(OUT, "used.json"), "w"), indent=1)
    print(len(made), "takes from", sorted(used))
    return made


def ledger_lines():
    """One line per source file the takes were cut from, for the provenance records."""
    used = json.load(open(os.path.join(OUT, "used.json")))
    lines = []
    for k in used:
        pack, rel = SOURCES[k]
        url, author, lic = PAGES[pack]
        h = hashlib.sha256(open(os.path.join(SRC, pack, rel), "rb").read()).hexdigest()
        lines.append(f"| {pack}/{rel} | {url} | {author} | {lic} | 2026-10-05 | {h} | cut into art/sound/chain*.wav (tools/uiforge/chainsfx.py) |")
    return lines


def mix(links=6, secs=0.32, seed=3, made=None):
    """Sfx.ChainSlide with the takes, as the game will play it: a clink per link at the spring's
    crossings, the drag under them, the settle at the stop; through the room."""
    made = made or {os.path.basename(p)[:-4]: _read(os.path.join(OUT, p)) for p in os.listdir(OUT) if p.endswith(".wav")}
    rng = np.random.default_rng(seed)
    k = secs / 0.32
    m = SP.Mix(secs + 2.6)
    n = max(2, min(14, links))
    lk = sorted(x for x in made if x.startswith("chainLink"))
    last = None
    for i, t in enumerate(SP.spring_times(n, k)):
        u = (i + 0.5) / n
        name = rng.choice([x for x in lk if x != last])
        last = name
        s = pitch(made[name], rng.uniform(0.94, 1.06)) * 0.32 * (1 - 0.35 * u) * rng.uniform(0.8, 1.1)
        m.put(t + rng.uniform(-0.004, 0.004), s, 0.12)
    m.put(0.02 * k, made[f"chainDrag_{rng.integers(0, 2)}"] * 0.16)
    stop = 0.29 * k
    m.put(stop, made[f"chainSettle_{rng.integers(0, 2)}"] * 0.42, 0.25)
    return m.out()


def _read(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def apply():
    """The takes into godot/art/sound/ (with their .import files), counted in sounds.json."""
    import shutil
    import imports
    snd = os.path.join(ROOT, "godot", "art", "sound")
    counts = json.load(open(os.path.join(snd, "sounds.json"), encoding="utf-8"))
    fams = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".wav"):
            fam, i = f[:-4].rsplit("_", 1)
            fams[fam] = max(fams.get(fam, 0), int(i) + 1)
            shutil.copyfile(os.path.join(OUT, f), os.path.join(snd, f))
    counts.update(fams)
    json.dump(dict(sorted(counts.items())), open(os.path.join(snd, "sounds.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    made = imports.write([os.path.join(snd, f"{fam}_{i}.wav") for fam, n in fams.items() for i in range(n)])
    print("applied", fams, len(made), "imports")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "takes"
    if what == "takes":
        build()
    elif what == "apply":
        apply()
    elif what == "ledger":
        print("\n".join(ledger_lines()))
