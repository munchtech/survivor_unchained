"""Sound family generator: prompts.json -> ElevenLabs -> cache -> process -> godot/art/sound.
Commands: make <family...>|--all [--dry] [--max-credits N] [--reserve N]; process <family...>|--all [--no-import]; import; status.
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


def onset_shape(x):
    """(pre-roll ms, rise ms): 5 ms RMS envelope; pre-roll = first point above -30 dB under the peak, rise = pre-roll
    to the first point within 3 dB of the max (same as scratch attack.py)."""
    y = np.abs(x) if x.ndim == 1 else np.abs(x).max(axis=1)
    win = max(1, int(RATE * 0.005))
    env = np.sqrt(np.convolve(y * y, np.ones(win) / win, mode="same"))
    pk = env.max() + 1e-12
    pre = int(np.argmax(env > pk * 10 ** (-30 / 20)))
    top = int(np.argmax(env > pk * 10 ** (-3 / 20)))
    return pre, pre / RATE * 1000, (top - pre) / RATE * 1000


def trim_preroll(x, keep_ms=2.0):
    pre, _, _ = onset_shape(x)
    start = pre - int(RATE * keep_ms / 1000)
    return x[start:] if start > 0 else x


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
    if fam.get("max_s"):  # cut to a game timing (a windup that must end when its blow lands), fading out
        n = int(fam["max_s"] * RATE)
        if len(s) > n:
            s = s[:n].copy()
            f = int(fam.get("fade_out_ms", 150) * RATE / 1000)
            ramp = np.linspace(1.0, 0.0, f)
            s[-f:] *= ramp[:, None] if s.ndim == 2 else ramp
    if fam.get("max_rise_ms"):
        s = trim_preroll(s)
    s = fade_in(s)
    if kind == "bed":
        s = make_loop(s)
        s = norm_lufs(s, fam["lufs"])
    else:
        s = norm_peak(s, fam["peak_db"])
    return s


# ---------- CLAP + onsets ----------
BASE_NEG = ["music with a melody", "a person speaking or shouting", "silence"]
_clap = {}


def _clap_model():
    if not _clap:
        os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
        os.environ["HF_TOKEN_PATH"] = os.path.join(HERE, "no_such_token")
        from transformers import ClapModel, ClapProcessor
        _clap["m"] = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval()
        _clap["p"] = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    return _clap["m"], _clap["p"]


def _emb(o):
    if hasattr(o, "norm"):
        return o
    return o.pooler_output if getattr(o, "pooler_output", None) is not None else o[0]


def clap_scores(x, prompt, negs):
    import torch
    m, p = _clap_model()
    mono = x.mean(axis=1) if x.ndim == 2 else x
    a = signal.resample_poly(mono, 48000, RATE).astype(np.float32)
    a = a[: 48000 * 10]
    with torch.no_grad():
        ai = p(audio=[a], sampling_rate=48000, return_tensors="pt")
        ae = m.get_audio_features(**ai)
        ti = p(text=[prompt] + negs, return_tensors="pt", padding=True)
        te = m.get_text_features(**ti)
    ae, te = _emb(ae), _emb(te)
    ae = ae / ae.norm(dim=-1, keepdim=True)
    te = te / te.norm(dim=-1, keepdim=True)
    c = (te @ ae[0]).tolist()
    return float(c[0]), float(max(c[1:]))


def count_onsets(x, sr=RATE, n=1024, hop=256):
    mono = x.mean(axis=1) if x.ndim == 2 else x
    if len(mono) < n * 2:
        return 1
    win = np.hanning(n)
    fr = np.lib.stride_tricks.sliding_window_view(mono, n)[::hop]
    sp = np.abs(np.fft.rfft(fr * win, axis=1))
    flux = np.maximum(np.diff(sp, axis=0), 0).sum(axis=1)
    env = np.sqrt((fr ** 2).mean(axis=1))[1:]
    gate = env.max() * 10 ** (-30 / 20)
    thr = flux.mean() + 1.5 * flux.std()
    gap = int(0.06 * sr / hop)
    last, cnt = -10 ** 9, 0
    for i in range(len(flux)):
        if flux[i] < thr or env[i] < gate:
            continue
        lo, hi = max(0, i - 1), min(len(flux), i + 2)
        if flux[i] < flux[lo:hi].max():
            continue
        if i - last >= gap:
            cnt += 1
            last = i
    return cnt


def take_clap(t, fam, negs):
    cp = os.path.join(CACHE, t["key"] + ".clap.json")
    sig = [fam["prompt"], negs]
    if os.path.exists(cp):
        d = json.load(open(cp, encoding="utf8"))
        if d.get("sig") == sig:
            return d["clap"], d["clap_neg"]
    c, n = clap_scores(t["x"], fam["prompt"], negs)
    with open(cp, "w", encoding="utf8") as f:
        json.dump({"sig": sig, "clap": c, "clap_neg": n}, f)
    return c, n


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
    sec = min(fam["seconds"], fam.get("max_s") or fam["seconds"])
    for t in takes:
        m = t["m"]
        if fam["kind"] == "oneshot" and m["onset_ms"] > fam.get("max_onset_ms", 25):
            t["drop"] = "onset %.0f ms > %d" % (m["onset_ms"], fam.get("max_onset_ms", 25))
        elif fam.get("max_rise_ms") and onset_shape(t["x"])[2] > fam["max_rise_ms"]:
            t["drop"] = "rise %.0f ms > %d" % (onset_shape(t["x"])[2], fam["max_rise_ms"])
        elif m["clipped"] > 0:
            t["drop"] = "clipped %d" % m["clipped"]
        elif fam["kind"] != "bed" and not (0.4 * sec <= m["duration_s"] <= 2.5 * sec):
            t["drop"] = "duration %.2f s outside 40-250%% of %.2f" % (m["duration_s"], sec)
        elif m["rms_dbfs"] < -45:
            t["drop"] = "near-silence rms %.1f" % m["rms_dbfs"]
    cc0 = "cc0" in fam
    negs = BASE_NEG + (["several separate hits one after another"] if fam["kind"] == "oneshot" else []) + list(fam.get("neg", []))
    max_on = fam.get("max_onsets", 2)
    min_margin = fam.get("min_margin", 0.0)
    for t in takes:
        if fam["kind"] == "oneshot":
            t["m"]["onsets"] = count_onsets(t["x"])
            if not t["drop"] and t["m"]["onsets"] > max_on:
                t["drop"] = "onsets %d > %d" % (t["m"]["onsets"], max_on)
        if not cc0:
            c, n = take_clap(t, fam, negs)
            t["m"]["clap"], t["m"]["clap_neg"], t["m"]["clap_margin"] = round(c, 4), round(n, 4), round(c - n, 4)
    ok = [t for t in takes if not t["drop"]]
    keep = fam["keep"]
    if not cc0 and ok:
        good = [t for t in ok if t["m"]["clap_margin"] >= min_margin]
        if len(good) < min(2, len(ok)):
            good = sorted(ok, key=lambda t: -t["m"]["clap_margin"])[:2]
            print("WARNING %s: clap margin below %.2f for most takes, keeping best %d by margin" % (name, min_margin, len(good)))
        for t in ok:
            if t not in good:
                t["drop"] = "clap margin %.3f < %.2f" % (t["m"]["clap_margin"], min_margin)
        ok = good
    if ok:
        mc = float(np.median([t["m"]["centroid_hz"] for t in ok]))
        md = float(np.median([t["m"]["duration_s"] for t in ok]))

        def score(t):
            dc = abs(t["m"]["centroid_hz"] - mc) / max(mc, 1.0)
            dd = abs(t["m"]["duration_s"] - md) / max(md, 0.01)
            return (round(dc + dd, 3), -t["m"]["crest_db"])
        ok.sort(key=score)
        if not cc0:
            ok.sort(key=lambda t: -t["m"]["clap_margin"])
            # coherence tie-break within 0.02 margin: greedy groups by margin, coherence order inside each
            rank = {id(t): r for r, t in enumerate(sorted(ok, key=score))}
            groups, cur = [], []
            for t in ok:
                if cur and cur[0]["m"]["clap_margin"] - t["m"]["clap_margin"] > 0.02:
                    groups.append(cur)
                    cur = []
                cur.append(t)
            groups.append(cur)
            ok = [t for g in groups for t in sorted(g, key=lambda t: rank[id(t)])]
    if fam.get("pick"):  # a hand/measure-chosen set of cache indices (among those that pass), e.g. for distinct ladders
        ok = [t for t in ok if t["i"] in fam["pick"]]
        keep = len(ok)
    kept = ok[:keep]
    for t in ok[keep:]:
        t["drop"] = "not among the %d best-ranked takes" % keep
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
        drops = {}
        for t in takes:
            if t["drop"] and t not in kept:
                r = t["drop"].split(" ")[0]
                drops[r] = drops.get(r, 0) + 1
        cl = ""
        if not cc0:
            cl = ", clap %.3f margin %.3f" % (np.mean([t["m"]["clap"] for t in takes]), a_kept("clap_margin", kept))
        print("%s: kept %d/%d, %.2f s, peak %.1f dBFS (tp %.1f), %.1f LUFS, centroid %.0f Hz%s, drops %s" % (
            name, len(kept), len(takes), a("duration_s"), a("peak_dbfs"), a("true_peak_dbfs"), a("lufs"), a("centroid_hz"),
            cl, drops or "none"))
    else:
        print("%s: kept 0/%d" % (name, len(takes)))


def a_kept(f, kept):
    return float(np.mean([t["m"][f] for t in kept]))


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
    if "--no-import" not in args:
        cmd_import([])


GODOT = "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"


def cmd_import(args):
    import subprocess
    r = subprocess.run([GODOT, "--headless", "--path", os.path.join(ROOT, "godot"), "--import"],
                       capture_output=True, timeout=1800)
    print("godot import: exit %d" % r.returncode)


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
    if not argv or argv[0] not in ("make", "process", "import", "status"):
        sys.exit(__doc__)
    {"make": cmd_make, "process": cmd_process, "import": cmd_import, "status": cmd_status}[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
