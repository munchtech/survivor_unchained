"""Ingest the owner's den sounds (ElevenLabs, 16 Nov 2026) into the bank, by script, re-runnable.

    python tools/sound/demo_ingest.py [--src DIR] [--dry]

From `survivorsunchained_inputs/sounds_demo/*.wav` (16-bit stereo 48 kHz) to `godot/art/sound/<family>_<n>.wav`
(+ `.wav.import`, as every bank file has one) and `godot/art/sound/sounds.json` (family -> take count):

  * trims leading silence (keeps 4 ms), trims the tail and fades it (30 ms, a sting's 250 ms);
  * converts to 16-bit PCM at 44100 Hz (the bank's beds and takes), mono for takes played in the world (the bank pans
    them) and stereo for loops, music and the Pack-Mother's calls;
  * levels each family to the mean loudness (LUFS, tools/audio/measure.py) of its nearest banked neighbour, capped so no
    peak passes -1 dBFS (the cap is written down: "peak-limited");
  * loops (the den's air, the pits, both tracks): cuts the loop where the tail best continues the head and cross-fades
    the head in over the tail, so the seam is the original signal's own next sample; the seam is then measured (step
    jump against the signal's median step, and the level on either side) and the numbers are written to the table.

Output table: `tools/sound/demo_ingest_table.md`. Provenance rows: `docs/team/provenance.md` (written by hand once;
the table lists the source file of each family). No hand edits on outputs: change this script and rerun.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
SOUND = ROOT / "godot" / "art" / "sound"
sys.path.insert(0, str(ROOT / "tools" / "audio"))
import measure as M  # noqa: E402

RATE = 44100
DEFAULT_SRC = Path(r"C:\Users\munch\Desktop\survivorsunchained_inputs\sounds_demo")

# family: (kind, channels, neighbour families whose mean LUFS it takes, [source file stems in take order])
#   kind: "shot" one-shot, "sting" one-shot with a long fade, "loop" seamless loop, "music" loop (the track)
SPEC = {
    # --- the den's air, the pits, the pack far off
    "den_ambience": ("loop", 2, ["bed_deepshaw_night"], ["Ambience Loop"]),
    "den_pits": ("loop", 2, ["bed_fire"], ["Green pits loop"]),
    "den_pack_far": ("shot", 2, ["bed_deepshaw_night"], ["pack at a distance"]),
    # --- music (no banked neighbour: the title's bed plus 2 LU; the score sits under the fight)
    "music_den_explore": ("music", 2, ["bed_title"], ["Music den exploration track"]),
    "music_den_boss": ("music", 2, ["bed_title"], ["Music den boss fight"]),
    "music_den_falls": ("sting", 2, ["bed_title"], ["Music boss falls"]),
    # --- Longtooth Wolf
    "voice_wolf_notice": ("shot", 1, ["kill_hide"], ["wolf notice1", "wolf notice2"]),
    "voice_wolf_lunge": ("shot", 1, ["kill_hide"], ["wolf lunge1", "wolf lunge2"]),
    "voice_wolf_hurt": ("shot", 1, ["hurt_her"], ["wolf hurtyelp 1"]),
    "voice_wolf_death": ("shot", 1, ["kill_hide"], ["wolf death1"]),
    # --- Blight-Sick Wolf
    "voice_wolfb_notice": ("shot", 1, ["kill_hide"], ["blight wolf notice1", "blight wolf notice2", "Blight wolf notice3"]),
    "voice_wolfb_bite": ("shot", 1, ["kill_hide"], ["blight wolf bite 1", "Blight wolf bite2"]),
    "voice_wolfb_lunge": ("shot", 1, ["kill_hide"], ["blight wolf lunge1", "blight wolf lunge2"]),
    "voice_wolfb_hurt": ("shot", 1, ["hurt_her"], ["blight wolf hurtyelp1"]),
    "voice_wolfb_death": ("shot", 1, ["kill_hide"], ["blight wolf death1"]),
    # --- Thicket Tusker
    "voice_boar_notice": ("shot", 1, ["kill_hide"], ["Thicket tusker snort1"]),
    "voice_boar_bite": ("shot", 1, ["kill_hide"], ["thicket tusker grunt1"]),
    "voice_boar_lunge": ("shot", 1, ["kill_hide"], ["Thicket tusker charge"]),
    "voice_boar_death": ("shot", 1, ["kill_hide"], ["Thicket tusker death"]),
    # --- the Pack-Mother's Yearling
    "voice_yearling_notice": ("shot", 1, ["kill_hide"], ["Pack-Mother's Yearling notice1"]),
    "voice_yearling_bite": ("shot", 1, ["kill_hide"], ["Pack-Mother's Yearling bite1", "Pack-Mother's Yearling bite2"]),
    "voice_yearling_lunge": ("shot", 1, ["kill_hide"], ["Pack-Mother's Yearling lunge1", "Pack-Mother's Yearling lunge2"]),
    "voice_yearling_hurt": ("shot", 1, ["hurt_her"], ["Pack-Mother's yearling hurtyelp1"]),
    "voice_yearling_death": ("shot", 1, ["kill_hide"], ["Pack-Mother's yearling death1"]),
    # --- the Pack-Mother (stereo: she is the biggest thing in the room)
    "voice_packmother_arrival": ("shot", 2, ["boss_arrive"], ["Pack Mother arrival howl"]),
    "voice_packmother_drive": ("shot", 2, ["boss_arrive"], ["The Pack mother the drive"]),
    "voice_packmother_hamstring": ("shot", 2, ["boss_arrive"], ["The Pack mother hamstring"]),
    "voice_packmother_moonhowl": ("shot", 2, ["boss_arrive"], ["The Pack mother moon-howl"]),
    "voice_packmother_phase": ("shot", 2, ["boss_arrive"], ["The Pack mother phase change"]),
    "voice_packmother_call": ("shot", 2, ["boss_arrive"], ["The Pack mother the call that brings wolves"]),
    "voice_packmother_death": ("shot", 2, ["boss_down"], ["The Pack mother death"]),
    # --- her
    "her_grunt": ("shot", 1, ["hurt_her"], ["her swing grunt1", "her swing grunt2", "her swing grunt3", "her swing grunt4"]),
    "her_leap": ("shot", 1, ["hurt_her"], ["her leap1", "her leap2", "her leap3", "her leap4"]),
    "her_land": ("shot", 1, ["hard_landing"], ["her landing1", "her landing2", "her landing3"]),
    "her_dodge": ("shot", 1, ["hurt_her"], ["her dodge1", "her dodge2"]),
    "her_perfect": ("shot", 1, ["hurt_her"], ["her perfect"]),
    "her_stance": ("shot", 1, ["hurt_her"], ["Stance1", "Stance2"]),
    "her_heartbeat": ("shot", 1, ["hurt_her"], [f"low-health-heartbeat#{k}" for k in range(4)]),
    # --- (16 Nov 13:01-13:42, the owner's second batch, same folder) skills: Sunder and Groundbreaker are placed in the world (mono);
    #     Bladestorm's six seconds of whirl is the storm's own bed (stereo, a long fade: it is cut at the spin's start, never looped)
    "skill_sunder": ("shot", 1, ["sunder_impact"], ["sunder"]),
    "skill_groundbreaker": ("shot", 1, ["quake_crack"], ["groundbreaker"]),
    "skill_bladestorm": ("sting", 2, ["storm_whir"], ["Bladestorm"]),
    # --- the skill tree (the Lamps screen): open and close are slow swells (stereo), the rest are ticks (mono)
    "tree_open": ("sting", 2, ["ui_open"], ["skill tree open"]),
    "tree_close": ("sting", 2, ["ui_close"], ["skill tree close"]),
    "tree_focus": ("shot", 1, ["ui_card"], ["skill tree focus"]),
    "tree_path": ("shot", 1, ["ui_pick"], ["skill tree path click"]),
    "tree_denied": ("shot", 1, ["ui_deny"], ["skill tree denied"]),
    # --- the interface
    "ui_hover": ("shot", 1, ["ui_card"], ["hover"]),
    "ui_click": ("shot", 1, ["ui_pick"], ["click"]),
    "ui_equip": ("shot", 1, ["ui_pick"], ["equip ui"]),
    # --- loot picked up, by rarity (the drop's own fall is drop_<tier>); gear put on, by slot; a set completed
    "loot_generic": ("shot", 2, ["gold_pickup"], ["Generic loot pickup"]),
    "loot_rare": ("sting", 2, ["drop_rare"], ["Rare loot pickup"]),
    "equip_plate": ("shot", 1, ["impactPlate_medium"], ["Equip plate armor"]),
    "equip_helmboots": ("shot", 1, ["impactPlate_medium"], ["Equp helm or boots"]),
    "set_complete": ("sting", 2, ["drop_set"], ["set complete"]),
}

IMPORT_TEMPLATE = (SOUND / "anvil_0.wav.import")


def read(path):
    import soundfile as sf
    x, r = sf.read(str(path), dtype="float64", always_2d=True)
    return x, r


def to_rate(x, r):
    if r == RATE:
        return x
    g = np.gcd(r, RATE)
    return np.stack([signal.resample_poly(x[:, c], RATE // g, r // g) for c in range(x.shape[1])], axis=1)


def db(v):
    return 20 * np.log10(max(float(v), 1e-10))


def trim(x, tail_db=-55.0, head_db=-50.0):
    """Leading silence off (4 ms of room kept), trailing silence off."""
    env = np.abs(x).max(axis=1)
    thr_h, thr_t = 10 ** (head_db / 20), 10 ** (tail_db / 20)
    idx = np.nonzero(env > thr_h)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(0.004 * RATE))
    idx_t = np.nonzero(env > thr_t)[0]
    b = min(len(x), idx_t[-1] + 1 + int(0.02 * RATE))
    return x[a:b]


def fade_out(x, seconds):
    n = min(len(x), int(seconds * RATE))
    x = x.copy()
    x[len(x) - n:] *= np.linspace(1, 0, n)[:, None] ** 2
    return x


def fade_in(x, seconds):
    n = min(len(x), int(seconds * RATE))
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)[:, None]
    return x


def trim_body(x, drop_db=4.0):
    """A track that fades in and out: keep from where it first reaches its steady level to where it last holds it."""
    w = int(0.5 * RATE)
    mono = x.mean(axis=1)
    r = np.array([db(np.sqrt(np.mean(mono[i:i + w] ** 2))) for i in range(0, len(mono) - w, w)])
    med = float(np.median(r))
    ok = np.nonzero(r >= med - drop_db)[0]
    a, b = ok[0] * w, min(len(x), (ok[-1] + 1) * w)
    return x[a:b], {"body_from_s": a / RATE, "body_to_s": b / RATE}


def make_loop(x, xfade_s):
    """Cut a loop so its end continues into its start. Returns (loop, info).

    out = x[:M] with its first f samples replaced by a cross-fade from x[M:M+f] (the signal as it would have gone
    on past M) into x[0:f]; so out[-1] = x[M-1] is followed by out[0] = x[M], the original's own next sample. M is
    searched near the end for the cut where the tail's last f samples best resemble the head's first f (normalised
    cross-correlation of the mono mix), which keeps a beat or a swell where it was.
    """
    n, f = len(x), int(xfade_s * RATE)
    mono = x.mean(axis=1)
    head = mono[:f]
    hn = np.linalg.norm(head) + 1e-9
    best, best_m = -2.0, n - f
    lo = max(n - int(10 * RATE), f * 2)
    hi = n - f
    step = max(1, int(0.002 * RATE))
    for m in range(lo, hi + 1, step):
        seg = mono[m:m + f]
        c = float(np.dot(seg, head) / ((np.linalg.norm(seg) + 1e-9) * hn))
        # a small bonus for a longer loop: do not throw away seconds for a hair of correlation
        c += 0.02 * (m / n)
        if c > best:
            best, best_m = c, m
    m = best_m
    out = x[:m].copy()
    t = np.linspace(0, np.pi / 2, f)
    w_in, w_out = np.sin(t)[:, None], np.cos(t)[:, None]
    out[:f] = x[:f] * w_in + x[m:m + f] * w_out
    return out, {"cut_s": m / RATE, "corr": best - 0.02 * (m / n), "xfade_s": xfade_s}


def seam_report(x):
    """The numbers at the join: the step across it against the signal's own median step; the level either side."""
    mono = x.mean(axis=1)
    steps = np.abs(np.diff(mono))
    med = float(np.median(steps)) + 1e-9
    p99 = float(np.percentile(steps, 99))
    seam = float(abs(mono[0] - mono[-1]))
    w = int(0.05 * RATE)
    a, b = mono[-w:], mono[:w]
    ra = db(np.sqrt(np.mean(a ** 2))); rb = db(np.sqrt(np.mean(b ** 2)))
    # three seconds either side, to catch a swell or a beat the cut moved
    w2 = int(3.0 * RATE)
    r1 = db(np.sqrt(np.mean(mono[-w2:] ** 2))); r2 = db(np.sqrt(np.mean(mono[:w2] ** 2)))
    # spectral distance of the 200 ms either side (log-magnitude, 24 bands)
    k = int(0.2 * RATE)

    def bands(seg):
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        edges = np.unique(np.geomspace(1, len(sp) - 1, 25).astype(int))
        return np.array([db(sp[edges[i]:edges[i + 1]].mean() + 1e-9) for i in range(len(edges) - 1)])
    sd = float(np.abs(bands(mono[-k:]) - bands(mono[:k])).mean())
    return {"seam_step_over_median": seam / med, "seam_step_over_p99": seam / p99, "rms50_before_db": ra, "rms50_after_db": rb,
            "rms3s_before_db": r1, "rms3s_after_db": r2, "spectral_dist_db": sd}


def seam_ok(i):
    return i["seam_step_over_p99"] <= 1.0 and i["spectral_dist_db"] <= 6 and abs(i["rms3s_before_db"] - i["rms3s_after_db"]) <= 1.5


def lufs(x):
    """Loudness of the mono mixdown, as tools/audio measured every banked take."""
    return M.measure(x.mean(axis=1), RATE)["lufs"]


def neighbour_lufs(fams):
    vals = []
    for fam in fams:
        for f in sorted(SOUND.glob(f"{fam}_*.wav")):
            d, r = read(f)
            vals.append(lufs(d))
    return float(np.mean(vals)), len(vals)


def write_wav(path, x):
    import soundfile as sf
    sf.write(str(path), np.clip(x, -1, 1), RATE, subtype="PCM_16")


def uid_for(name):
    h = hashlib.sha256(("su-den-sound/" + name).encode()).digest()
    alpha = "abcdefghijklmnopqrstuvwxy01234567"
    return "uid://" + "".join(alpha[b % len(alpha)] for b in h[:12])


def write_import(name):
    t = IMPORT_TEMPLATE.read_text()
    res = f"res://art/sound/{name}.wav"
    md5 = hashlib.md5(res.encode()).hexdigest()
    old_uid = [l for l in t.splitlines() if l.startswith("uid=")][0]
    t = t.replace(old_uid, f'uid="{uid_for(name)}"')
    t = t.replace("anvil_0.wav-dd28fb6a7861198a6b15a7c2c5b544fc", f"{name}.wav-{md5}")
    t = t.replace("res://art/sound/anvil_0.wav", res)
    (SOUND / f"{name}.wav.import").write_bytes(t.encode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    src = Path(a.src)
    counts = json.loads((SOUND / "sounds.json").read_text())
    rows = []
    for fam, (kind, ch, neigh, stems) in SPEC.items():
        target, nn = neighbour_lufs(neigh)
        if kind == "music":
            target += 2.0
        for i, stem in enumerate(stems):
            p = src / f"{stem.split('#')[0]}.wav"
            x, r = read(p)
            x = to_rate(x, r)
            if "#" in stem:
                # one cycle (lub-dub, 1 s apart from 0.51 s) of a source that holds several: the heart is paced by the game's timer
                a0 = int((0.45 + int(stem.split("#")[1])) * RATE)
                x = x[a0:a0 + int(0.95 * RATE)]
            if kind in ("shot", "sting"):
                x = trim(x)
                x = fade_in(x, 0.002)
                x = fade_out(x, 0.25 if kind == "sting" else 0.03)
            info = {}
            if kind in ("loop", "music"):
                body = {}
                if kind == "music":
                    x, body = trim_body(x)
                src_x = x
                for xf in (1.5, 2.5, 4.0, 6.0):
                    # the shortest cross-fade that makes the seam pass the gate (a longer one smears more of the take)
                    x, info = make_loop(src_x, xf)
                    info.update(seam_report(x))
                    if seam_ok(info):
                        break
                info.update(body)
            if ch == 1:
                x = x.mean(axis=1, keepdims=True)
            raw_l = lufs(x)
            gain = 10 ** ((target - raw_l) / 20)
            pk = np.abs(x).max()
            limited = False
            if pk * gain > 10 ** (-1 / 20):
                gain = 10 ** (-1 / 20) / pk
                limited = True
            y = x * gain
            out_l = lufs(y)
            name = f"{fam}_{i}"
            if not a.dry:
                write_wav(SOUND / f"{name}.wav", y)
                write_import(name)
            rows.append({"family": fam, "take": i, "src": f"{stem}.wav", "kind": kind, "ch": ch, "dur": len(y) / RATE,
                         "raw_lufs": raw_l, "target": target, "out_lufs": out_l, "peak_db": db(np.abs(y).max()), "limited": limited,
                         "neigh": "+".join(neigh), "info": info})
            if info:
                print("   seam:", {k: round(float(v), 2) for k, v in info.items()})
            print(f"{name:34s} {len(y)/RATE:7.2f}s  raw {raw_l:6.1f} -> {out_l:6.1f} LUFS (target {target:6.1f}){' PEAK-LIMITED' if limited else ''}")
        counts[fam] = len(stems)
    if not a.dry:
        (SOUND / "sounds.json").write_text(json.dumps(counts, indent=1) + "\n", encoding="utf-8")
    table = ["# Den sound ingest (tools/sound/demo_ingest.py)", "",
             "Source: `survivorsunchained_inputs/sounds_demo/` (ElevenLabs, made by the owner, 15-16 Nov 2026, no attribution needed; the last 16 files written 16 Nov 13:01-13:42).",
             "Format: 16-bit PCM, 44100 Hz; mono for takes the bank places in the world, stereo for loops, music, the Pack-Mother's calls.",
             "Level: each family takes the mean LUFS of its nearest banked neighbour (column `neighbour`); music = the title bed +2 LU;",
             "`limited` = the take would have passed -1 dBFS, so its gain was capped there.", "",
             "| family_take | source file | s | kind | ch | raw LUFS | out LUFS | target | peak dBFS | limited | neighbour |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        table.append(f"| {r['family']}_{r['take']} | {r['src']} | {r['dur']:.2f} | {r['kind']} | {r['ch']} | {r['raw_lufs']:.1f} | {r['out_lufs']:.1f} | {r['target']:.1f} | {r['peak_db']:.1f} | {'yes' if r['limited'] else ''} | {r['neigh']} |")
    loops = [r for r in rows if r["info"]]
    table += ["", "## Loops: the seam, by measurement", "",
              "Cut: where the tail best continues the head (normalised cross-correlation `corr`, 1 = identical); the head is cross-faded in over the tail for `xfade`",
              "seconds so the sample after the last is the original signal's own next one. `step/median`: the jump across the seam over the signal's median",
              "sample step (information), and `step/p99`: over the signal's 99th-percentile step (gate: at most 1, the seam is no bigger a jump than the signal makes by itself every few milliseconds). `rms 50 ms` and `rms 3 s`: the level just before the end and just after the start",
              "(both within 1.5 dB = no swell or beat lost at the join). `spec`: mean band-by-band difference of the 200 ms either side (gate under 6 dB).", "",
              "| family | length s | cut at s | corr | xfade s | step/median | step/p99 | rms 50 ms before / after | rms 3 s before / after | spec dB |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in loops:
        i = r["info"]
        table.append(f"| {r['family']} | {r['dur']:.2f} | {i['cut_s']:.2f} | {i['corr']:.2f} | {i['xfade_s']} | {i['seam_step_over_median']:.2f} | {i['seam_step_over_p99']:.2f} | {i['rms50_before_db']:.1f} / {i['rms50_after_db']:.1f} | {i['rms3s_before_db']:.1f} / {i['rms3s_after_db']:.1f} | {i['spectral_dist_db']:.1f} |")
    bad = [r["family"] for r in loops if not seam_ok(r["info"])]
    table += ["", "Seam gate: " + ("FAILS for " + ", ".join(bad) if bad else "all loops pass.")]
    if not a.dry:
        (ROOT / "tools" / "sound" / "demo_ingest_table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print("seam gate:", "FAILS for " + ", ".join(bad) if bad else "all loops pass")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
