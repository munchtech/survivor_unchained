"""Shared arm/torso metrics for a run: gp [T,J,3] global positions, Y up. j: dict of joint indices
(shL shR elL elR hdL hdR hipL hipR spine_lo neck chest). Returns dict per side + torso."""
import numpy as np
def unit(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)
def ang(a, b): return np.degrees(np.arccos(np.clip(np.sum(unit(a) * unit(b), -1), -1, 1)))
def metrics(gp, j):
    lat = unit(gp[:, j["shL"]] - gp[:, j["shR"]])
    up0 = gp[:, j["neck"]] - gp[:, j["spine_lo"]]
    up = unit(up0 - lat * np.sum(up0 * lat, -1, keepdims=True))
    fwd = np.cross(lat, up)
    mid = gp[:, j["chest"]]
    res = {}
    Ls = []
    for side, sg in (("l", 1), ("r", -1)):
        S, E, H = gp[:, j["sh" + side.upper()]], gp[:, j["el" + side.upper()]], gp[:, j["hd" + side.upper()]]
        L = float(np.mean(np.linalg.norm(E - S, axis=-1) + np.linalg.norm(H - E, axis=-1)))
        Ls.append(L)
        lo = lat * sg
        u = unit(E - S)
        abd = np.degrees(np.arcsin(np.clip(np.sum(u * lo, -1), -1, 1)))
        sag = np.degrees(np.arctan2(np.sum(u * fwd, -1), -np.sum(u * up, -1)))  # + forward of hanging
        elb = ang(S - E, H - E)  # 180 straight
        hf = np.sum((H - mid) * fwd, -1)
        kf, kb = int(np.argmax(hf)), int(np.argmin(hf))
        res[side] = dict(L=L, abd_max=abd.max(), abd_mean=abd.mean(), sag_fwd=sag.max(), sag_back=sag.min(),
                         sag_range=sag.max() - sag.min(), elb_min=elb.min(), elb_max=elb.max(), elb_mean=elb.mean(),
                         hand_travel=(hf.max() - hf.min()) / L,
                         hand_h_fwd=float(np.sum((H[kf] - S[kf]) * up[kf])) / L,
                         hand_cross_fwd=float(np.sum((H[kf] - S[kf]) * lo[kf])) / L,  # - = toward midline from shoulder line
                         elbow_out_max=float(np.max(np.sum((E - S) * lo, -1))) / L,
                         hand_h_cm=float(np.sum((H[kf] - S[kf]) * up[kf])), hand_cross_cm=float(np.sum((H[kf] - S[kf]) * lo[kf])),
                         elbow_out_cm=float(np.max(np.sum((E - S) * lo, -1))))
    # counter-rotation: horizontal yaw of shoulder line vs hip line
    def yaw(a, b):
        d = gp[:, a] - gp[:, b]
        return np.degrees(np.arctan2(d[:, 2], d[:, 0]))
    ys, yh = yaw(j["shL"], j["shR"]), yaw(j["hipL"], j["hipR"])
    ys, yh = np.unwrap(np.radians(ys)), np.unwrap(np.radians(yh))
    d = np.degrees(ys - yh); ys, yh = np.degrees(ys), np.degrees(yh)
    lean = np.degrees(np.arccos(np.clip(up[:, 1], -1, 1)))
    res["torso"] = dict(shoulder_yaw_amp=(np.percentile(ys, 97) - np.percentile(ys, 3)) / 2,
                        hip_yaw_amp=(np.percentile(yh, 97) - np.percentile(yh, 3)) / 2,
                        counter_amp=(np.percentile(d, 97) - np.percentile(d, 3)) / 2, lean=float(lean.mean()))
    return res
def fmt(name, r):
    t = r["torso"]
    s = [f"{name:24s} lean {t['lean']:4.1f} shYaw±{t['shoulder_yaw_amp']:4.1f} hipYaw±{t['hip_yaw_amp']:4.1f} ctr±{t['counter_amp']:4.1f}"]
    for side in "lr":
        a = r[side]
        s.append(f"   {side}: abd {a['abd_max']:4.1f}/{a['abd_mean']:4.1f}  sag +{a['sag_fwd']:4.1f}/{a['sag_back']:5.1f} (rng {a['sag_range']:4.1f})  "
                 f"elb {a['elb_min']:3.0f}-{a['elb_max']:3.0f} (m{a['elb_mean']:3.0f})  handTrav {a['hand_travel']:.2f}L  "
                 f"fwdHand h{a['hand_h_fwd']:+.2f}L x{a['hand_cross_fwd']:+.2f}L  elbOut {a['elbow_out_max']:+.2f}L  "
                 f"[{a['hand_h_cm']:+.0f} {a['hand_cross_cm']:+.0f} {a['elbow_out_cm']:+.0f} cm, L {a['L']*100:.0f}]")
    return "\n".join(s)
