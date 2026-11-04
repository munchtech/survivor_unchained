"""Sound family generator: prompts.json -> ElevenLabs -> cache -> process -> godot/art/sound.
Commands: make <family...>|--all [--dry] [--max-credits N] [--reserve N]; process <family...>|--all; status.
The API key is never printed or logged."""
import sys, os, json, hashlib, datetime, glob, re
import numpy as np
from scipy import signal
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402

RATE = 44100
MODEL = "eleven_text_to_sound_v2"
PROMPTS = os.path.join(HERE, "prompts.json")
CACHE = os.path.join(HERE, "cache")
LOG = os.path.join(HERE, "gen_log.jsonl")
MEAS = os.path.join(HERE, "measure")
SOUND = os.path.join(ROOT, "godot", "art", "sound")
COUNTS = os.path.join(SOUND, "sounds.json")
LEGAL = os.path.join(ROOT, "docs", "legal", "audio_generated.md")
CREDITS_PER_SECOND = 10


def load_families():
    with open(PROMPTS, encoding="utf8") as f:
        return json.load(f)["families"]


def defaults(fam):
    d = {"kind": "oneshot", "stereo": False, "peak_db": -1.0, "loop": False, "tail_db": -55,
         "lufs": -28, "influence": 0.5, "n": 3, "keep": 2}
    d.update(fam)
    return d


def cache_key(fam, i):
    loop = fam["kind"] == "bed"
    s = json.dumps([fam["prompt"], fam["seconds"], fam["influence"], loop, MODEL, i])
    return hashlib.sha256(s.encode()).hexdigest()


def cache_path(key):
    return os.path.join(CACHE, key + ".pcm")


def read_log():
    if not os.path.exists(LOG):
        return []
    with open(LOG, encoding="utf8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ---------- DSP ----------
def decode_pcm(raw):
    a = np.frombuffer(raw[: len(raw) // 4 * 4], dtype="<i2").astype(np.float64) / 32768.0
    return a.reshape(-1, 2)


def highpass(x, hz=25.0):
    sos = signal.butter(2, hz, "highpass", fs=RATE, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def trim_lead(x, db=-45.0, keep_ms=3.0):
    env = np.abs(x) if x.ndim == 1 else np.abs(x).max(axis=1)
    idx = np.nonzero(env > 10 ** (db / 20))[0]
    if not len(idx):
        return x
    start = max(0, idx[0] - int(RATE * keep_ms / 1000))
    return x[start:]


def trim_tail(x, tail_db=-55.0, fade_ms=15.0):
    env = np.abs(x) if x.ndim == 1 else np.abs(x).max(axis=1)
    idx = np.nonzero(env > 10 ** (tail_db / 20))[0]
    if not len(idx):
        return x
    end = min(len(x), idx[-1] + 1)
    x = x[:end].copy()
    f = min(int(RATE * fade_ms / 1000), len(x))
    if f > 0:
        w = 0.5 * (1 + np.cos(np.linspace(0, np.pi, f)))
        x[-f:] *= w if x.ndim == 1 else w[:, None]
    return x


def fade_in(x, ms=2.0):
    x = x.copy()
    f = min(int(RATE * ms / 1000), len(x))
    if f > 0:
        w = np.linspace(0, 1, f, endpoint=False)
        x[:f] *= w if x.ndim == 1 else w[:, None]
    return x


def make_loop(x, xf_s=1.5):
    """Equal-power crossfade of the last xf into the first xf; output length = input - xf."""
    c = int(RATE * xf_s)
    if len(x) <= 2 * c:
        c = len(x) // 3
    t = np.linspace(0, np.pi / 2, c)
    fin, fout = np.sin(t), np.cos(t)
    if x.ndim == 2:
        fin, fout = fin[:, None], fout[:, None]
    head = x[:c] * fin + x[-c:] * fout
    return np.concatenate([head, x[c:len(x) - c]])


def true_peak(x):
    ch = [x] if x.ndim == 1 else [x[:, k] for k in range(x.shape[1])]
    return max(float(np.abs(signal.resample_poly(c, 4, 1)).max()) for c in ch)


def norm_peak(x, db):
    tp = true_peak(x)
    return x * (10 ** (db / 20) / tp) if tp > 0 else x


def norm_lufs(x, target, ceiling_db=-1.0):
    import pyloudnorm as pyln
    l = pyln.Meter(RATE).integrated_loudness(x)
    if not np.isfinite(l):
        return x
    x = x * 10 ** ((target - l) / 20)
    if true_peak(x) > 10 ** (ceiling_db / 20):
        x = norm_peak(x, ceiling_db)
    return x


def process_take(raw, fam):
    s = decode_pcm(raw)
    s = s - s.mean(axis=0)
    s = highpass(s)
    kind = fam["kind"]
    if kind == "oneshot" and not fam["stereo"]:
        s = s.mean(axis=1)
    s = trim_lead(s)
    if kind != "bed":
        s = trim_tail(s, fam["tail_db"])
    s = fade_in(s)
    if kind == "bed":
        s = make_loop(s)
        s = norm_lufs(s, fam["lufs"])
    else:
        s = norm_peak(s, fam["peak_db"])
    return s


# ---------- families ----------
def process_family(name, fam):
    fam = defaults(fam)
    takes = []
    if "cc0" in fam:
        c = fam["cc0"]
        d, r = sf.read(c["path"], dtype="float64", always_2d=True)
        if r != RATE:
            d = signal.resample_poly(d, RATE, r, axis=0)
        if d.shape[1] == 1:
            d = np.repeat(d, 2, axis=1)
        raws = [(0, "cc0", (np.clip(d[:, :2], -1, 1) * 32767).astype("<i2").tobytes())]
        fam.setdefault("prompt", "CC0: %s" % c.get("url", c["path"]))
        fam["seconds"] = len(d) / RATE
        fam["keep"] = 1
    else:
        raws = []
        for i in range(fam["n"]):
            k = cache_key(fam, i)
            if os.path.exists(cache_path(k)):
                with open(cache_path(k), "rb") as f:
                    raws.append((i, k, f.read()))
    if not raws:
        print("%s: no cached takes (run make first)" % name)
        return
    for i, k, raw in raws:
        x = process_take(raw, fam)
        m = M.measure(x, RATE)
        takes.append({"i": i, "key": k, "x": x, "m": m, "drop": None})
    sec = fam["seconds"]
    for t in takes:
        m = t["m"]
        if fam["kind"] == "oneshot" and m["onset_ms"] > 25:
            t["drop"] = "onset %.0f ms > 25" % m["onset_ms"]
        elif m["clipped"] > 0:
            t["drop"] = "clipped %d" % m["clipped"]
        elif fam["kind"] != "bed" and not (0.4 * sec <= m["duration_s"] <= 2.5 * sec):
            t["drop"] = "duration %.2f s outside 40-250%% of %.2f" % (m["duration_s"], sec)
        elif m["rms_dbfs"] < -45:
            t["drop"] = "near-silence rms %.1f" % m["rms_dbfs"]
    ok = [t for t in takes if not t["drop"]]
    keep = fam["keep"]
    if ok:
        mc = float(np.median([t["m"]["centroid_hz"] for t in ok]))
        md = float(np.median([t["m"]["duration_s"] for t in ok]))

        def score(t):
            dc = abs(t["m"]["centroid_hz"] - mc) / max(mc, 1.0)
            dd = abs(t["m"]["duration_s"] - md) / max(md, 0.01)
            return (round(dc + dd, 3), -t["m"]["crest_db"])
        ok.sort(key=score)
    kept = ok[:keep]
    for t in ok[keep:]:
        t["drop"] = "not among the %d most coherent takes" % keep
    if len(kept) < keep:
        print("WARNING %s: only %d of %d wanted takes survive" % (name, len(kept), keep))
    kept.sort(key=lambda t: t["i"])
    os.makedirs(SOUND, exist_ok=True)
    for old in glob.glob(os.path.join(SOUND, name + "_*.wav")):
        if re.fullmatch(re.escape(name) + r"_\d+\.wav", os.path.basename(old)):
            os.remove(old)
            if os.path.exists(old + ".import"):
                os.remove(old + ".import")
    tmpl = open(os.path.join(SOUND, "click_0.wav.import"), encoding="utf8", newline="").read()
    params = tmpl[tmpl.index("[params]"):]
    eol = "\r\n" if "\r\n" in tmpl else "\n"
    files = []
    for k, t in enumerate(kept):
        fn = "%s_%d.wav" % (name, k)
        sf.write(os.path.join(SOUND, fn), t["x"], RATE, subtype="PCM_16")
        imp = ("[remap]" + eol + eol + 'importer="wav"' + eol + 'type="AudioStreamWAV"' + eol + eol +
               "[deps]" + eol + eol + 'source_file="res://art/sound/%s"' % fn + eol + eol + params)
        with open(os.path.join(SOUND, fn + ".import"), "w", encoding="utf8", newline="") as f:
            f.write(imp)
        t["file"] = fn
        files.append(fn)
    update_counts(name, len(kept))
    os.makedirs(MEAS, exist_ok=True)
    rep = {"family": name, "kept": len(kept), "n": len(takes),
           "takes": [{"i": t["i"], "key": t["key"], "file": t.get("file"), "dropped": t["drop"],
                      "measure": t["m"]} for t in takes]}
    with open(os.path.join(MEAS, name + ".json"), "w", encoding="utf8") as f:
        json.dump(rep, f, indent=1)
    write_legal(name, fam, files, [t["key"] for t in kept])
    if kept:
        a = lambda f: float(np.mean([t["m"][f] for t in kept]))
        print("%s: kept %d/%d, %.2f s, peak %.1f dBFS (tp %.1f), %.1f LUFS, centroid %.0f Hz" % (
            name, len(kept), len(takes), a("duration_s"), a("peak_dbfs"), a("true_peak_dbfs"), a("lufs"), a("centroid_hz")))
    else:
        print("%s: kept 0/%d" % (name, len(takes)))


def update_counts(name, n):
    with open(COUNTS, encoding="utf8", newline="") as f:
        raw = f.read()
    eol = "\r\n" if "\r\n" in raw else "\n"
    d = json.loads(raw)
    if n > 0:
        d[name] = n
    else:
        d.pop(name, None)
    out = json.dumps({k: d[k] for k in sorted(d)}, indent=1).replace("\n", eol)
    with open(COUNTS, "w", encoding="utf8", newline="") as f:
        f.write(out)


HEADER = """# Generated audio provenance

These sounds are ElevenLabs sound-effects generations (model eleven_text_to_sound_v2) made on the owner's paid ElevenLabs Starter account. The output is owned by the owner; no attribution is needed on paid plans. CC0 sources are listed with their author and license. Rows are written by `tools/audio/gen.py` and rewritten on reprocess.

| family | files | prompt | seconds | generated (UTC date) | cache keys |
|---|---|---|---|---|---|
"""


def write_legal(name, fam, files, keys):
    rows = {}
    if os.path.exists(LEGAL):
        for line in open(LEGAL, encoding="utf8").read().splitlines():
            if line.startswith("| ") and not line.startswith("| family") and not line.startswith("|---"):
                rows[line.split("|")[1].strip()] = line
    log = [r for r in read_log() if r["family"] == name]
    date = (log[-1]["utc"][:10] if log else datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"))
    if "cc0" in fam:
        c = fam["cc0"]
        prompt = "CC0 source: %s by %s (%s), %s" % (c.get("path"), c.get("author"), c.get("license", "CC0"), c.get("url", ""))
    else:
        prompt = fam["prompt"]
    prompt = prompt.replace("|", "/")
    rows[name] = "| %s | %s | %s | %s | %s | %s |" % (
        name, ", ".join(files), prompt, round(fam["seconds"], 2), date, ", ".join(k[:12] for k in keys))
    os.makedirs(os.path.dirname(LEGAL), exist_ok=True)
    with open(LEGAL, "w", encoding="utf8", newline="\n") as f:
        f.write(HEADER + "\n".join(rows[k] for k in sorted(rows)) + "\n")


# ---------- commands ----------
def pick(args, fams):
    if "--all" in args:
        return list(fams)
    skip = set()
    for fl in ("--max-credits", "--reserve"):
        if fl in args:
            skip.add(args.index(fl) + 1)
    names = [a for i, a in enumerate(args) if not a.startswith("--") and i not in skip]
    for n in names:
        if n not in fams:
            sys.exit("unknown family: %s" % n)
    return names


def opt(args, flag, default):
    if flag in args:
        return int(args[args.index(flag) + 1])
    return default


def cmd_make(args):
    import elevenlabs as E
    fams = load_families()
    names = pick(args, fams)
    dry = "--dry" in args
    max_credits = opt(args, "--max-credits", 3000)
    reserve = opt(args, "--reserve", 15000)
    todo = []
    for n in names:
        f = defaults(fams[n])
        if "cc0" in f:
            continue
        for i in range(f["n"]):
            k = cache_key(f, i)
            if not os.path.exists(cache_path(k)):
                todo.append((n, i, k, f))
    planned = int(sum(f["seconds"] * CREDITS_PER_SECOND for _, _, _, f in todo))
    print("takes to generate: %d, planned about %d credits (cached takes are free)" % (len(todo), planned))
    if dry:
        for n, i, k, f in todo:
            print("  would make %s take %d (%.1f s)" % (n, i, f["seconds"]))
        return
    if todo:
        sub = E.subscription()
        remaining = sub["character_limit"] - sub["character_count"]
        print("subscription: %s, %d of %d credits used, %d remaining" % (
            sub["tier"], sub["character_count"], sub["character_limit"], remaining))
        if remaining - planned < reserve:
            sys.exit("REFUSED: remaining %d minus planned %d would drop below the reserve %d" % (remaining, planned, reserve))
        os.makedirs(CACHE, exist_ok=True)
        spent = 0
        for n, i, k, f in todo:
            if spent >= max_credits:
                print("stopped: --max-credits %d reached" % max_credits)
                break
            raw, cost, trace = E.generate(f["prompt"], f["seconds"], f["influence"], f["kind"] == "bed")
            with open(cache_path(k), "wb") as fh:
                fh.write(raw)
            spent += cost
            with open(LOG, "a", encoding="utf8", newline="\n") as fh:
                fh.write(json.dumps({"family": n, "i": i, "key": k, "prompt": f["prompt"], "seconds": f["seconds"],
                                     "influence": f["influence"], "model": MODEL, "cost": cost, "trace": trace,
                                     "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}) + "\n")
            print("  made %s take %d: %d credits, %d bytes" % (n, i, cost, len(raw)))
        print("spent %d credits this run" % spent)
    for n in names:
        process_family(n, fams[n])


def cmd_process(args):
    fams = load_families()
    for n in pick(args, fams):
        process_family(n, fams[n])


def cmd_status(args):
    import elevenlabs as E
    fams = load_families()
    try:
        s = E.subscription()
        print("subscription: %s, %d of %d credits used, %d remaining" % (
            s["tier"], s["character_count"], s["character_limit"], s["character_limit"] - s["character_count"]))
    except Exception as e:
        print("subscription unavailable: %s" % e)
    spent = {}
    for r in read_log():
        spent[r["family"]] = spent.get(r["family"], 0) + r.get("cost", 0)
    for n, c in sorted(spent.items()):
        print("  spent %s: %d credits" % (n, c))
    notmade = [n for n in fams if not os.path.exists(os.path.join(MEAS, n + ".json"))]
    print("not yet made: %s" % (", ".join(notmade) or "none"))


def main(argv):
    if not argv or argv[0] not in ("make", "process", "status"):
        sys.exit(__doc__)
    {"make": cmd_make, "process": cmd_process, "status": cmd_status}[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
