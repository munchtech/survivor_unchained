# proxy loop: G1's export in memory, the dump's edits mapped onto it, measured.
import os, sys, copy
os.environ["ANIM_PEOPLE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"..\g1\exp_graft")
import numpy as np
from g2lib import *
from skin import Body
import meas, edit

d = load_dump()
b0 = Body.heroine(jiggle=False, head=True, helpers=True)
REF = body_map(b0, d)
meas.prep(b0)
b0._cl = {k: b0.clip(k) for k in ("idle_reaver_town", "reaver_show", "flask_drink", "catch_breath")}
C = edit.Ctx(d, b0)
P0J, P0W = b0.J.copy(), b0.W.copy()
SH0 = C.shares(d["VG"])


def variant(P=None, VG=None, tag="v", delta_w=True):
    b = copy.copy(b0); b.P = b0.P.copy(); b.J = b0.J.copy(); b.W = b0.W.copy()
    ch = np.zeros(len(d["P"]), bool)
    if P is not None:
        ch |= np.linalg.norm(P - d["P"], axis=1) > 1e-7
    if VG is not None:
        ch |= np.abs(VG - d["VG"]).sum(1) > 1e-5
    hk, mm, dist = REF
    sel = ch[mm] & (dist < 5e-3); k = hk[sel]; m_ = mm[sel]
    if P is not None:
        b.P[k] = b.P[k] + glb(P[m_] - d["P"][m_])
    if VG is not None:
        Jn, Wn = split_glb(b, VG[m_], d["names"], b.P[k])
        if delta_w:
            Jo, Wo = split_glb(b, d["VG"][m_], d["names"], b0.P[k])
            nj = len(b.sk.names); F = np.zeros((len(k), nj)); r = np.arange(len(k))[:, None].repeat(4, 1)
            np.add.at(F, (r, b0.J[k]), b0.W[k]); np.add.at(F, (r, Jn), Wn); np.add.at(F, (r, Jo), -Wo)
            F = np.maximum(F, 0); Jn = np.argsort(-F, 1)[:, :4]; Wn = np.take_along_axis(F, Jn, 1); Wn /= Wn.sum(1, keepdims=True)
        b.J[k] = Jn; b.W[k] = Wn
    return meas.m(b, tag), b
