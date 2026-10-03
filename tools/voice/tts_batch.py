#!/usr/bin/env python3
"""Voice every line that has no take yet, or whose words have changed.

    python3 tools/voice/tts_batch.py --dry-run                 what would be voiced
    python3 tools/voice/tts_batch.py --auditions               each voice's audition lines, for casting
    python3 tools/voice/tts_batch.py                           everything missing or stale
    python3 tools/voice/tts_batch.py --voice vonnra --limit 10 a few of one voice

Reads the manifest (godot/data/voice/lines.json, from tools/voice/extract.py)
and what has been recorded (godot/data/voice/takes.json, which this writes).
Each line that needs a take is sent to synthesize() below with its voiceable
words, its voice and its direction; the result is brought to about -16 LUFS
(ffmpeg's loudnorm, two passes) and written as Ogg Vorbis to the line's path
under godot/ (res://audio/vo/<voice>/<id>.ogg). takes.json is saved after
every take, so a stopped batch picks up where it stopped. The game plays a
take only while its hash matches the words on screen.

A line whose words and voice match a take already made (a moved line, two
variants with the same words) is copied, not voiced again.

Needs Python 3.9+ and ffmpeg (with libvorbis) on the PATH. synthesize() is
the only part that knows about the TTS.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GODOT = os.path.join(ROOT, "godot")
MANIFEST = os.path.join(GODOT, "data", "voice", "lines.json")
TAKES = os.path.join(GODOT, "data", "voice", "takes.json")
HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = os.path.join(HERE, "voices.json")
REFS = os.path.join(HERE, "refs")
AUDITIONS = os.path.join(HERE, "auditions")

LOUDNESS = -16.0   # LUFS, integrated: dialogue
TRUE_PEAK = -1.5   # dBTP
RANGE = 11.0       # LU
RATE = 48000
QUALITY = 5        # libvorbis -q (about 160 kb/s)


# =========================================================================
# THE LOCAL TTS: fill this in on the machine that runs it.
# =========================================================================

def synthesize(text, voice, design, instruction, reference, out_wav):
    """Say `text` in `voice` and write it to `out_wav` (WAV, any rate, mono or
    stereo). Everything else in this tool is done for you.

      text         the words to say: the line's voiceable form, with tokens
                   such as {name} and stage directions already taken out.
      voice        the voice's key ('vonnra', 'narrator', 'townswoman').
      design       the voice-design paragraph from tools/voice/voices.json:
                   a description of the voice for a model that builds one
                   from words (Qwen3-TTS VoiceDesign).
      instruction  how to say this line: emotion, intensity, pace and notes,
                   from tools/voice/directions.json (an instruct / style
                   prompt).
      reference    the path of the voice's chosen reference clip
                   (tools/voice/refs/<voice>.wav, with <voice>.txt holding
                   its words) if one has been chosen, else None. Clone from
                   it when it exists, so every take is the same person;
                   design from `design` only when it does not.

    Raise on failure; the line is skipped and reported, and the batch goes on.
    """
    raise NotImplementedError(
        "synthesize() in tools/voice/tts_batch.py is not connected to a TTS yet: "
        "point it at the local Qwen3-TTS (or run with --placeholder to test the pipeline).")

# =========================================================================


def placeholder(text, voice, design, instruction, reference, out_wav):
    """A soft tone as long as the line would take to say: for checking the
    pipeline and the game's playback without a TTS. Never commit these."""
    seconds = max(0.6, min(14.0, len(text.split()) * 0.36))
    pitch = 180 + (sum(map(ord, voice)) % 9) * 40
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={pitch}:duration={seconds:.2f}",
         "-af", f"volume=0.2,afade=t=in:d=0.05,afade=t=out:st={seconds - 0.2:.2f}:d=0.2", out_wav])


def run(cmd, capture=False):
    r = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr.strip()[-600:]}")
    return r.stderr


def normalise(src, dst):
    """Two-pass EBU R128 loudness to about -16 LUFS, then Ogg Vorbis, mono."""
    measure = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af",
                   f"loudnorm=I={LOUDNESS}:TP={TRUE_PEAK}:LRA={RANGE}:print_format=json", "-f", "null", "-"], capture=True)
    j = measure[measure.rindex("{"):measure.rindex("}") + 1]
    m = json.loads(j)
    af = (f"loudnorm=I={LOUDNESS}:TP={TRUE_PEAK}:LRA={RANGE}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.05,"
          "areverse,silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.15,areverse")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part.ogg"
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", str(RATE), "-c:a", "libvorbis", "-q:a", str(QUALITY), tmp])
    os.replace(tmp, dst)


def disk(res_path):
    assert res_path.startswith("res://"), res_path
    return os.path.join(GODOT, *res_path[len("res://"):].split("/"))


def instruction_for(line, cast):
    d = line.get("direction", {})
    v = cast.get(line["voice"], {})
    bits = [f"{d.get('emotion', v.get('rest', ''))}, intensity {d.get('intensity', 2)} of 5, {d.get('pace', v.get('pace', ''))}."]
    if d.get("wants"):
        bits.append(f"Wants {d['wants'].rstrip('.')}.")
    if d.get("notes"):
        bits.append(d["notes"].rstrip(".") + ".")
    if v.get("accent"):
        bits.append(f"Accent: {v['accent'].rstrip('.')}.")
    return " ".join(bits)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_takes(takes):
    data = {"about": "What has been recorded, and for which words (the hash). Written by tools/voice/tts_batch.py; "
                     "the game plays a take only while its hash matches the words on screen.",
            "takes": dict(sorted(takes.items()))}
    tmp = TAKES + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, TAKES)


def reference(voice):
    p = os.path.join(REFS, voice + ".wav")
    return p if os.path.exists(p) else None


def auditions(cast, say, voices):
    """Each voice's audition lines, several candidates each, for choosing the
    reference clip: tools/voice/auditions/<voice>/<n>_<take>.wav."""
    for key, v in cast.items():
        if key.startswith("_") or (voices and key not in voices):
            continue
        for n, text in enumerate(v.get("auditions", []), 1):
            for take in range(1, 4):
                out = os.path.join(AUDITIONS, key, f"{n}_{take}.wav")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                print(f"audition {key} {n}.{take}: {text[:60]}")
                say(text, key, v.get("design", ""), f"{v.get('rest', '')}, {v.get('pace', '')}. Accent: {v.get('accent', '')}", None, out)
    print(f"Listen in {AUDITIONS}; copy the chosen take to tools/voice/refs/<voice>.wav and its words to <voice>.txt.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--voice", action="append", help="only this voice (repeatable)")
    ap.add_argument("--id", action="append", help="only this line ID (repeatable)")
    ap.add_argument("--limit", type=int, help="stop after this many takes")
    ap.add_argument("--optional", action="store_true", help="also the optional lines (the chapter's page)")
    ap.add_argument("--force", action="store_true", help="voice again even lines whose take is current")
    ap.add_argument("--dry-run", action="store_true", help="say what would be voiced, and stop")
    ap.add_argument("--auditions", action="store_true", help="voice each voice's audition lines for casting, and stop")
    ap.add_argument("--placeholder", action="store_true", help="tones instead of voices, to test the pipeline and the game (never commit them)")
    ap.add_argument("--prune", action="store_true", help="forget takes whose lines are gone from the manifest, and delete their files")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not on the PATH")
    cast = load_json(VOICES, {})
    say = placeholder if a.placeholder else synthesize
    if a.auditions:
        auditions(cast, say, set(a.voice or []))
        return
    lines = load_json(MANIFEST, {}).get("lines", [])
    if not lines:
        sys.exit("no manifest: run python3 tools/voice/extract.py first")
    takes = load_json(TAKES, {}).get("takes", {})
    ids = {l["id"] for l in lines}

    if a.prune:
        for tid in [t for t in takes if t not in ids]:
            f = disk(takes[tid]["file"])
            if os.path.exists(f):
                os.remove(f)
            del takes[tid]
            print(f"pruned {tid}")
        save_takes(takes)

    # What is already on disk, by voice and words: a moved line is copied, not voiced.
    have = {}
    for tid, t in takes.items():
        if os.path.exists(disk(t["file"])):
            have[(t["voice"], t["hash"])] = disk(t["file"])

    todo = []
    for l in lines:
        if l.get("skip") or (l.get("optional") and not a.optional):
            continue
        if a.voice and l["voice"] not in a.voice:
            continue
        if a.id and l["id"] not in a.id:
            continue
        t = takes.get(l["id"])
        current = t and t["hash"] == l["hash"] and os.path.exists(disk(l["file"]))
        if current and not a.force:
            continue
        todo.append((l, "stale" if t else "new"))

    print(f"{len(lines)} lines in the manifest, {len(takes)} recorded; {len(todo)} to voice"
          + (f" (stopping after {a.limit})" if a.limit else ""))
    if a.dry_run:
        by = {}
        for l, why in todo:
            by.setdefault(l["voice"], []).append(why)
        for v, whys in sorted(by.items()):
            print(f"  {v:14} {len(whys):4}  ({whys.count('new')} new, {whys.count('stale')} stale)")
        return

    done = failed = copied = 0
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        for l, why in todo:
            if a.limit and done >= a.limit:
                break
            dst = disk(l["file"])
            words = l.get("say") or l["text"]
            src = have.get((l["voice"], l["hash"]))
            try:
                if src and src != dst and not a.force:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(src, dst)
                    copied += 1
                else:
                    raw = os.path.join(tmp, "take.wav")
                    say(words, l["voice"], cast.get(l["voice"], {}).get("design", ""), instruction_for(l, cast), reference(l["voice"]), raw)
                    normalise(raw, dst)
            except NotImplementedError as e:
                sys.exit(str(e))
            except Exception as e:  # one bad line must not stop the night's batch
                failed += 1
                print(f"  FAILED {l['id']}: {e}")
                continue
            takes[l["id"]] = {"voice": l["voice"], "hash": l["hash"], "file": l["file"]}
            have[(l["voice"], l["hash"])] = dst
            save_takes(takes)
            done += 1
            print(f"  [{done}/{len(todo)}] {why:5} {l['id']}: {words[:70]}")
    print(f"voiced {done - copied}, copied {copied}, failed {failed}, in {time.time() - t0:.0f}s")
    if done:
        print("Open the Godot editor (or run Godot with --headless --import --path godot) to import the new takes before exporting.")


if __name__ == "__main__":
    main()
