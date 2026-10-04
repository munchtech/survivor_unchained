"""Kimodo's motion as BVH, for tools/anim/retarget.py.

Runs in Kimodo's own environment (C:/Users/munch/Tools/kimodo/.venv, see
docs/ANIM_RESEARCH.md §5):

    <kimodo venv>/python tools/anim/kimodo_bvh.py <motion.npz> <out.bvh>

A Kimodo NPZ (its 30-joint SOMA skeleton: posed_joints and global_rot_mats,
or local_rot_mats and root_positions) is expanded to the 77-joint SOMA with
relaxed hands and written as BVH whose rest is the standard T-pose (every
joint's frame the world's), which is what the retargeter's calibration
expects. kimodo_gen.py writes the same BVH straight from a prompt.
"""
from __future__ import annotations

import sys

import numpy as np
import torch


def npz_to_bvh(npz_path, bvh_path, fps=30.0):
    from kimodo.exports.bvh import save_motion_bvh
    from kimodo.skeleton import SOMASkeleton30, global_rots_to_local_rots
    from kimodo.skeleton.registry import build_skeleton

    d = np.load(npz_path)
    if "local_rot_mats" in d.files:
        local = torch.from_numpy(d["local_rot_mats"]).float()
        root = torch.from_numpy(d["root_positions"]).float()
        J = local.shape[-3]
    else:
        g = torch.from_numpy(d["global_rot_mats"]).float()
        p = torch.from_numpy(d["posed_joints"]).float()
        J = g.shape[-3]
        sk = build_skeleton(J)
        local = global_rots_to_local_rots(g, sk)
        root = p[:, sk.root_idx, :]
    sk = build_skeleton(J)
    if isinstance(sk, SOMASkeleton30):
        local = sk.to_SOMASkeleton77(local)
        sk = sk.somaskel77
    save_motion_bvh(bvh_path, local, root, skeleton=sk, fps=fps, standard_tpose=True)


if __name__ == "__main__":
    npz_to_bvh(sys.argv[1], sys.argv[2])
    print("BVH", sys.argv[2])
