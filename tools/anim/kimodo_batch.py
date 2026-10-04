"""Kimodo's takes for kimodo_gen.py, made in one run: the model and its text
encoder loaded once, then every prompt in turn, several takes each, written
as T-pose BVH. Runs in Kimodo's own environment (kimodo_gen.py starts it):

    <kimodo venv>/python tools/anim/kimodo_batch.py <jobs.json> <out dir> [--dry]

jobs.json: [{"name", "prompt", "seconds", "seed", "takes"}]. A job whose
takes are all on disk is skipped, so a run that stops can be started again.
--dry puts a stand-in for the text encoder (noise, not words), to test the
rest of the run without Llama 3.
"""
from __future__ import annotations

import json
import os
import sys
import time
import zlib
from pathlib import Path

import torch


class Stand_in:
    """Noise in place of the text encoder's embedding, the same shape."""

    def __call__(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        feats = []
        for t in texts:
            g = torch.Generator().manual_seed(zlib.crc32(t.encode()))
            feats.append(torch.randn(1, 4096, generator=g))
        return torch.stack(feats), [1] * len(texts)

    def to(self, *a, **k):
        return self

    def eval(self):
        return self


def main(argv):
    jobs = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    out = Path(argv[1])
    dry = "--dry" in argv
    out.mkdir(parents=True, exist_ok=True)

    def paths(job):
        return [out / f"{job['name']}_{k}.bvh" for k in range(job["takes"])]

    todo = [j for j in jobs if not all(p.exists() for p in paths(j))]
    print(f"{len(todo)} of {len(jobs)} prompts to make", flush=True)
    if not todo:
        return

    from kimodo import load_model
    from kimodo.exports.bvh import save_motion_bvh
    from kimodo.skeleton import SOMASkeleton30, global_rots_to_local_rots
    from kimodo.tools import seed_everything

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    t0 = time.time()
    model = load_model("Kimodo-SOMA-RP-v1.1", device=device, default_family="Kimodo",
                       text_encoder=Stand_in() if dry else None)
    print(f"model loaded on {device} in {time.time() - t0:.0f} s", flush=True)
    skeleton = model.skeleton
    if isinstance(skeleton, SOMASkeleton30):
        # (The model hands its motion back on the 77-joint skeleton.)
        skeleton = skeleton.somaskel77.to(device)

    for job in todo:
        t0 = time.time()
        seed_everything(job["seed"])
        frames = int(job["seconds"] * model.fps)
        res = model([job["prompt"]], [frames], constraint_lst=[], num_denoising_steps=100,
                    num_samples=job["takes"], multi_prompt=True, num_transition_frames=5,
                    post_processing=True, return_numpy=True)
        for k, path in enumerate(paths(job)):
            joints = torch.from_numpy(res["posed_joints"][k]).to(device)
            rots = torch.from_numpy(res["global_rot_mats"][k]).to(device)
            local = global_rots_to_local_rots(rots, skeleton)
            save_motion_bvh(str(path), local, joints[:, skeleton.root_idx, :], skeleton=skeleton, fps=model.fps,
                            standard_tpose=True)
        print(f"{job['name']}: {job['takes']} takes in {time.time() - t0:.0f} s", flush=True)
    print("KIMODO DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
