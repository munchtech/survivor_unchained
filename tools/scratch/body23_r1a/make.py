"""Body 23 r1a: build candidate C1 or C2 on the looped body.  python make.py C1|C2
  1. the shoulder's form authored in the poses that show it (shoulder.py: hanging right arm at w_p45/look_f, akimbo
     left at w_m45/look_f/rL90), carried to rest by inverse skinning, least squares over the frames;
  2. the elbow's bend: elbow_psd45/90/135_{l,r} pose-space shapes (tools/assets/elbow_psd_post.author on the new rings,
     elbow.py: authored in the game frames that show the bend, w_m80/look_f/rL90 left, s_p45 right), driven in game by
     ElbowPsd.cs; shoulder_* shapes kept (psd_keep). (elbow_psd_post.author's synthetic-pose shapes made fins on the
     looped elbow at the frames: dih p99 175-179 deg vs 44-48, Look +10 px: not used.)"""
import os, sys, json, warnings
import numpy as np
warnings.filterwarnings("ignore")
import k, shoulder, b23build as bb
import elbow
from heroine_neck import _Gl

SH = {
    "C1": dict(shoulder.C1, top=9.0, step=5.0, vtap=5.0, belly=3.0, slim=2.5),
    "C2": dict(shoulder.C1, top=14.0, top_s=(-8.0, 46.0), step=8.0, vtap=9.0, vtap_s=(115.0, 36.0), belly=5.0,
               slim=5.0, slim_s=(185.0, 50.0)),
}
EL = {   # elbow_psd_post SCULPT per sample (cut: the corner's sides back as bone; pt: the olecranon point proud;
    #     tcut: the biceps tendon end in above the crease; bic: the flexed belly; br: the thumb-side wad)
    "C1": {45.0: dict(cut=4.0, pt=3.0, tcut=1.5, bic=3.0, br=5.0),
           90.0: dict(cut=10.0, pt=5.0, pt_len=8.0, pt_ang=22.0, tcut=3.0, bic=6.0, br=10.0, fill=1.5),
           135.0: dict(cut=9.0, pt=5.0, pt_len=8.0, pt_ang=22.0, tcut=3.0, bic=6.5, br=10.0, fill=1.5)},
    "C2": {45.0: dict(cut=6.0, pt=4.0, tcut=2.5, bic=4.0, br=6.0),
           90.0: dict(cut=15.0, pt=7.5, pt_len=7.0, pt_ang=20.0, tcut=5.0, bic=8.0, br=12.0, fill=0.8, flex=2.0),
           135.0: dict(cut=13.0, pt=7.0, pt_len=7.0, pt_ang=20.0, tcut=5.0, bic=8.5, br=12.0, fill=0.8, flex=2.0)},
}

EL2 = {"C1": dict(elbow.C1), "C2": {kk: v * 2.4 for kk, v in elbow.C1.items()}}


def make(name, log=print):
    out_dir = os.path.join(k.HERE, name)
    os.makedirs(out_dir, exist_ok=True)
    dU = shoulder.solve(SH[name], log=log)
    shapes = elbow.solve(EL2[name], body=k.Body(dU=dU), log=log)
    dst = os.path.join(out_dir, "heroine.glb")
    bb.write(dst, dU=dU, shapes=shapes, extras={"cand": name, "shoulder": SH[name], "elbow": EL2[name]}, log=log)
    np.save(os.path.join(out_dir, "dU.npy"), dU)
    np.savez_compressed(os.path.join(out_dir, "shapes.npz"), **shapes)
    return dU, shapes


if __name__ == "__main__":
    make(sys.argv[1])
