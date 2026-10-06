"""Mux the tab chain frames with its sound: two slides (Self to Journal, then Journal to Pack),
at 1080 and 1440, into MP4s in godot/.shots: the modal sound (the one to ship) and the old FM
one, for the A/B. The sound is mixed with the game's room (sfxpreview's Freeverb)."""
import os
import shutil
import subprocess
import sys

import numpy as np

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import chainanim  # noqa: E402
import forge as F  # noqa: E402
import kitboard as KB  # noqa: E402
import sfxpreview as SP  # noqa: E402
import chainsfx as CS  # noqa: E402
import imageio_ffmpeg  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
SHOTS = os.path.join(WT, 'godot', '.shots')
fps = 60
for scale in (1.0, 1.3333334):
    W, H = int(620 * scale), int(100 * scale)

    def band(sel):
        cv = KB.self2(KB.Canvas(1920, 1080, scale), "kit", chain="tabs", sel=sel)
        full = np.asarray(cv.image(), np.float32) / 255
        return np.dstack([full[:H, :W], np.ones((H, W), np.float32)])
    bgs = {i: band(i) for i in (1, 3, 0)}
    tabs = list(KB.TABS)
    a = chainanim.run(tabs, 1, 3, scale, bg=bgs[1], y0=57.0, bg_after=bgs[3], secs=1.4)
    b = chainanim.run(tabs, 3, 0, scale, bg=bgs[3], y0=57.0, bg_after=bgs[0], secs=1.4)
    hold = [a[0]] * 20
    frames = hold + a + b + [b[-1]] * 20
    d = os.path.join(chainanim.CH, 'video')
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for i, f in enumerate(frames):
        F.save(F.to_pil(np.clip(f, 0, 1)), os.path.join(d, f'f{i:04d}.png'))
    total = len(frames) / fps + 0.5
    p = chainanim.sprites()[0]['pitch']
    for name, recipe in (("cc0", CS.mix),):
        snd = np.zeros(int(total * SP.RATE))
        for start, links, seed in ((len(hold) + 4, abs(tabs[3] - tabs[1]) / p, 3), (len(hold) + len(a) + 4, abs(tabs[0] - tabs[3]) / p, 4)):
            s = recipe(int(round(links)), 0.32, seed)
            i0 = int(start / fps * SP.RATE)
            snd[i0:i0 + len(s)] += s[:len(snd) - i0]
        wav = os.path.join(d, f'chain_{name}.wav')
        SP.save(snd, wav)
        out = os.path.join(SHOTS, f'tabchain_{name}_{int(1080 * scale)}.mp4')
        subprocess.run([FF, '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(d, 'f%04d.png'), '-i', wav,
                        '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
        print(out, len(frames), 'frames', flush=True)
