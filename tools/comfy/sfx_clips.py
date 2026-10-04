"""Sounds made with LTX 2.5's audio on the local ComfyUI: a short clip is
made for its sound alone (the picture is black and thrown away), and its
audio is cut into a take for the game's recordings (godot/art/sound).

    python tools/comfy/sfx_clips.py <clips dir> [name ...]

Each sound has a few takes (different seeds), named <family>_<n>.wav and
counted in sounds.json, so the mixer never plays the same take twice
running. A clip already in the folder is not made again.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SOUND = os.path.normpath(os.path.join(HERE, "..", "..", "godot", "art", "sound"))

FRAME = ("A completely black screen, nothing visible at all. The sound only, recorded close and clean, "
         "with no music, no voices, no speech. ")

# family: (what is heard, seconds, seeds)
SOUNDS = {
    # The spike tells (combat's charge director): a moment before a people's rush.
    "tell_howl": ("A single lone wolf throws back its head and howls, long, rising and mournful, in a cold forest at "
                  "night, the howl echoing off the trees, then silence.", 4, (401, 402)),
    "tell_drum": ("Three heavy beats on a big war drum made of hide, deep and booming, slow and threatening, the last "
                  "beat ringing out, then silence.", 3, (403, 404)),
    "tell_fuse": ("A lit fuse catches and fizzes, hissing and sputtering sparks as it burns quickly down, close, then "
                  "silence.", 3, (405, 406)),
    "tell_whistle": ("A shrill hollow bone whistle is blown twice in the dark, eerie and piercing, echoing across a "
                     "graveyard, then silence.", 3, (407, 408)),
}


def make(clips, family, text, seconds, seed):
    dst = os.path.join(clips, f"{family}_{seed}.mp4")
    if os.path.exists(dst):
        return dst
    graph = os.path.join(HERE, "graphs", "ltx_t2v.json")
    tmp = os.path.join(clips, f"_{family}_{seed}")
    subprocess.run([sys.executable, os.path.join(HERE, "comfy.py"), "run", graph,
                    "--set", f"405:376.value={json.dumps(FRAME + text)}",
                    "--set", f"405:362.value={seconds}",
                    "--set", f"405:339.noise_seed={seed}",
                    # The picture does not matter: small, so the clip is quick.
                    "--set", "409.megapixels=0.25",
                    "--out", tmp], check=True)
    made = [f for f in os.listdir(tmp) if f.endswith(".mp4")]
    os.replace(os.path.join(tmp, made[0]), dst)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return dst


def take(mp4, out):
    """The clip's sound as a mono 16-bit take at 44.1 kHz: silence trimmed
    from both ends, faded in and out over a few milliseconds, and brought to
    a common peak so every take of a family sits at one level."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = subprocess.run([ff, "-v", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", "44100", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    if x.size == 0:
        raise SystemExit(f"{mp4} has no sound")
    loud = np.where(np.abs(x) > 0.02 * np.abs(x).max())[0]
    x = x[max(0, loud[0] - 441):min(x.size, loud[-1] + 4410)]
    fade = min(441, x.size // 4)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade * 4:] *= np.linspace(1, 0, fade * 4)
    x *= 0.89 / max(1e-4, np.abs(x).max())
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return x.size / 44100


def main():
    clips = os.path.abspath(sys.argv[1])
    want = sys.argv[2:] or list(SOUNDS)
    os.makedirs(clips, exist_ok=True)
    counts_path = os.path.join(SOUND, "sounds.json")
    counts = json.load(open(counts_path))
    for family in want:
        text, seconds, seeds = SOUNDS[family]
        for n, seed in enumerate(seeds):
            mp4 = make(clips, family, text, seconds, seed)
            dur = take(mp4, os.path.join(SOUND, f"{family}_{n}.wav"))
            print(f"{family}_{n}: {dur:.2f}s from seed {seed}", flush=True)
        counts[family] = len(seeds)
    with open(counts_path, "w") as f:
        json.dump(dict(sorted(counts.items())), f, indent=1)


if __name__ == "__main__":
    main()
