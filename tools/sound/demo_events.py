"""The den's events into godot/data/content/sounds.json (re-runnable; the block between the `den-begin`/`den-end`
comment lines is rewritten whole, nothing else in the file is touched; the C# reader skips comments).

    python tools/sound/demo_events.py

Table of every id, bus, takes and gain: docs/team/den_sound_events.md. Families come from tools/sound/demo_ingest.py.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "godot" / "data" / "content" / "sounds.json"
BEGIN, END = "    // den-begin (tools/sound/demo_events.py)", "    // den-end"

E = {}


def ev(id, bus, take, gain, pitch=None, near=None, stereo=False, lead=False, synth=None, duck=None, extra=None):
    layer = {"take": take, "gain": gain}
    if pitch:
        layer["pitch"] = pitch
    if stereo:
        layer["stereo"] = True
    layers = [layer] + (extra or [])
    d = {"bus": bus}
    if lead:
        d["lead"] = True
    if near is not None:
        d["near"] = near
    if synth:
        d["synth"] = synth
    if duck:
        d["duck"] = duck
    d["layers"] = layers
    E[id] = d


# --- the room: the den's air, its pits, the pack far off, the music
ev("bed.den", "ambience", "den_ambience", 1.0, stereo=True)
ev("den.pits", "ambience", "den_pits", 1.0, stereo=True)
ev("den.pack_far", "ambience", "den_pack_far", 1.0, stereo=True)
ev("music.den.explore", "music", "music_den_explore", 1.0, stereo=True)
ev("music.den.boss", "music", "music_den_boss", 1.0, stereo=True)
ev("music.den.falls", "music", "music_den_falls", 1.0, near=1, stereo=True)

# --- creatures (near 0.5: the bank's distance and pan rule; gain by the loudness of kill_hide 0.42)
P = [0.96, 1.04]
for kind, moments in {"wolf": ["notice", "lunge", "hurt", "death"], "wolfb": ["notice", "bite", "lunge", "hurt", "death"],
                      "boar": ["notice", "bite", "lunge", "death"], "yearling": ["notice", "bite", "lunge", "hurt", "death"]}.items():
    for m in moments:
        g = {"notice": 0.5, "bite": 0.5, "lunge": 0.5, "hurt": 0.42, "death": 0.55}[m]
        if kind in ("boar", "yearling"):
            g *= 1.1
        ev(f"voice.{kind}.{m}", "sfx", f"voice_{kind}_{m}", g, pitch=P, near=0.5)
# the common wolf has no bite of its own: the blight wolf's, a little lower
ev("voice.wolf.bite", "sfx", "voice_wolfb_bite", 0.48, pitch=[0.84, 0.92], near=0.5)
# the Pack-Mother: heard in full, stereo, her moves lead the crowd
for m, take, g in [("arrival", "arrival", 0.8), ("drive", "drive", 0.75), ("hamstring", "hamstring", 0.7), ("moonhowl", "moonhowl", 0.75),
                   ("phase", "phase", 0.8), ("call", "call", 0.75)]:
    ev(f"voice.packmother.{m}", "sfx", f"voice_packmother_{take}", g, near=1, stereo=True, lead=True)
ev("voice.packmother.death", "sfx", "voice_packmother_death", 0.8, near=1, stereo=True, lead=True)

# --- her (near 1: she is the listener)
ev("her.grunt", "sfx", "her_grunt", 0.55, pitch=[0.97, 1.03], near=1)
ev("her.leap", "sfx", "her_leap", 0.6, pitch=[0.98, 1.02], near=1)
ev("her.land", "sfx", "her_land", 0.6, pitch=[0.98, 1.02], near=1)
ev("dodge", "sfx", "her_dodge", 0.55, pitch=[0.97, 1.03], near=1, synth="under")
ev("dodge.perfect", "sfx", "her_perfect", 0.6, near=1, synth="under")
ev("her.stance", "sfx", "her_stance", 0.5, near=1)
ev("heartbeat", "sfx", "her_heartbeat", 0.6, near=1)


def line(id, d):
    return f'    {json.dumps(id)}: {json.dumps(d)}'


def main():
    s = FILE.read_text(encoding="utf-8")
    s = re.sub(r",\n" + re.escape(BEGIN) + r".*?\n" + re.escape(END), "", s, flags=re.S)
    block = ",\n" + BEGIN + "\n" + ",\n".join(line(k, v) for k, v in E.items()) + "\n" + END
    # after the last event (before the events object closes)
    i = s.rstrip().rfind("\n  }\n}")
    s = s[:i] + block + s[i:]
    FILE.write_text(s, encoding="utf-8", newline="\n")
    json.loads(re.sub(r"^\s*//.*$", "", s, flags=re.M))  # still valid JSON once the comment lines are gone
    print(len(E), "events")


if __name__ == "__main__":
    main()
