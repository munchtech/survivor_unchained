"""Listening-sheet captures: record moments of the game as sound (master + stems), the ids fired, loudness numbers.

  python tools/audio/moments.py run [names...|--all] --tag before|after [--nobank] [--out DIR]
  python tools/audio/moments.py sheet
Assumes the game is already built. One moment at a time."""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", ".."))
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
ROOT = r"C:\Users\munch\Desktop\survivorsunchained_inputs\audio_h3"
STEMS = ["sfx", "music", "ambience", "ui", "flare"]
sys.path.insert(0, HERE)


def moments():
    return json.load(open(os.path.join(HERE, "moments.json"), encoding="utf-8"))


def run_one(m, outdir, nobank):
    wav = os.path.join(outdir, m["name"] + ".wav")
    args = [GODOT, "--path", os.path.join(WT, "godot"), "--resolution", "640x360", "--fixed-fps", "60",
            "--audio-driver", "Dummy", "--", "--shot", m["name"]] + m["flags"] + \
           ["--until", str(m["until"]), "--wav", wav, "--stems", "--soundlog"] + (["--nobank"] if nobank else [])
    log = os.path.join(outdir, m["name"] + ".log")
    t0 = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(args, stdout=lf, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=900)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
            lf.write("\nTIMEOUT\n")
    text = open(log, encoding="utf-8", errors="replace").read()
    ids = [l for l in text.splitlines() if l.startswith("[soundlog]")]
    open(os.path.join(outdir, m["name"] + ".soundlog.txt"), "w", encoding="utf-8").write("\n".join(ids) + "\n")
    return time.time() - t0, ids


def numbers_for(m, outdir, ids):
    import measure as ms
    res = {"name": m["name"], "banked": 0, "synth": 0, "ids": {}}
    for l in ids:
        parts = l.split()
        if len(parts) >= 4:
            res["ids"][parts[1]] = [int(parts[2]), parts[3]]
            res["banked" if parts[3] == "banked" else "synth"] += 1
    wav = os.path.join(outdir, m["name"] + ".wav")
    if os.path.exists(wav):
        d, r = ms.read_wav(wav)
        res["master"] = ms.measure(d, r)
    res["stems"] = {}
    for s in STEMS:
        f = os.path.join(outdir, "%s_%s.wav" % (m["name"], s))
        if os.path.exists(f):
            d, r = ms.read_wav(f)
            res["stems"][s] = ms.measure(d, r)["lufs"]
    return res


def fmt(v):
    return "-inf" if v is None or v == float("-inf") else "%.1f" % v


def row(r, label=None):
    ms_ = r.get("master", {})
    return "| %s | %.1f | %s | %s | %s | %s | %s | %d | %d |" % (
        label or r["name"], ms_.get("duration_s", 0), fmt(ms_.get("peak_dbfs")), fmt(ms_.get("true_peak_dbfs")),
        fmt(ms_.get("lufs")), fmt(ms_.get("lufs_short_max")),
        " | ".join(fmt(r["stems"].get(s)) for s in STEMS), r["banked"], r["synth"])


def head(first="moment"):
    return ("| %s | seconds | peak dBFS | true peak | LUFS | short-term max | " % first + " | ".join(STEMS) +
            " | banked ids | synth ids |\n|" + "---|" * (8 + len(STEMS)))


def cmd_run(a):
    allm = moments()
    sel = allm if a.all or not a.names else [m for m in allm if m["name"] in a.names]
    outdir = a.out or os.path.join(ROOT, a.tag)
    os.makedirs(outdir, exist_ok=True)
    nj = os.path.join(outdir, "numbers.json")
    old = {r["name"]: r for r in json.load(open(nj))} if os.path.exists(nj) else {}
    for m in sel:
        secs, ids = run_one(m, outdir, a.nobank)
        r = numbers_for(m, outdir, ids)
        old[m["name"]] = r
        ms_ = r.get("master", {})
        print("%s: %.0fs wall, tape %.1fs, LUFS %s, peak %s, ids %d banked/%d synth" % (
            m["name"], secs, ms_.get("duration_s", 0), fmt(ms_.get("lufs")), fmt(ms_.get("peak_dbfs")), r["banked"], r["synth"]), flush=True)
        rows = [old[n["name"]] for n in allm if n["name"] in old]
        json.dump(rows, open(nj, "w"), indent=1)
        open(os.path.join(outdir, "numbers.md"), "w", encoding="utf-8").write(head() + "\n" + "\n".join(row(r) for r in rows) + "\n")


def cmd_sheet(a):
    def load(tag):
        p = os.path.join(ROOT, tag, "numbers.json")
        return {r["name"]: r for r in json.load(open(p))} if os.path.exists(p) else {}
    b, af = load("before"), load("after")
    out = ["# Audio H3 listening sheet\n",
           "Each moment is a recording of the game. BEFORE is the old synth sounds; AFTER is the new bank.",
           "Peak is in dB (0 is the loudest possible). LUFS is loudness: higher is louder.\n",
           "**Listen on headphones, AFTER first.** Each moment has a master wav and one wav per bus (`<name>_sfx.wav`, `_music`, `_ambience`, `_ui`, `_flare`). "
           "BEFORE and AFTER run through the same mixer (compressor, makeup gain, -1 dBFS limiter), so loudness differences are the sounds, not the mix.",
           "",
           "**The mix (AFTER):** fights about -20 LUFS integrated (target -20), peaks held at -1 dBFS; ambience about 17 dB under a fight; "
           "the Flare and UI buses above the fight when they fire; calm walks about -25 LUFS. Music is still the generative synth score (docs/team/audio.md 'Music': the next pass).",
           "",
           "**Known:** m07 lights no notable lamp (every notable in reach is behind a road gate); m11's telegraphs are drawn by weight, and this tape got the pull (ring, charge and closing are banked too). "
           "Sounds generation could not get right, for you to make: docs/team/audio.md 'For the owner'.\n"]
    for m in moments():
        n = m["name"]
        out += ["## %s" % n, m["what"], ""]
        for tag, d in (("before", b), ("after", af)):
            out.append("- %s: %s" % (tag, ("%s\\%s\\%s.wav" % (ROOT, tag, n)) if n in d else "not recorded yet"))
        if n in b or n in af:
            out += ["", head("take")]
            for tag, d in (("before", b), ("after", af)):
                if n in d:
                    out.append(row(d[n], tag))
        out.append("")
    os.makedirs(ROOT, exist_ok=True)
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write("\n".join(out))
    print("wrote", os.path.join(ROOT, "README.md"))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("names", nargs="*")
    r.add_argument("--all", action="store_true")
    r.add_argument("--tag", required=True)
    r.add_argument("--nobank", action="store_true")
    r.add_argument("--out")
    sp.add_parser("sheet")
    a = p.parse_args()
    cmd_run(a) if a.cmd == "run" else cmd_sheet(a)


if __name__ == "__main__":
    main()
