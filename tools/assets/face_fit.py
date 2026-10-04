"""The heroine's face fitted to a reference's (face_refs.py's paintings):
MediaPipe's face landmarks read off each view of the reference, and the
weights of her targets (or sliders) found that best move the same points of
her face (face_lab.py's anchors) to where the reference has them, each view
seen from its own angle at its own scale.

Runs in its own Python, where MediaPipe is (its landmarker model beside it):

    <py> tools/assets/face_fit.py marks <image> <out.json> [left|right|whole] [camera.json key]
    <py> tools/assets/face_fit.py fit <anchors.npz> <reference.png> <out.json> [--start start.json] [--reg 30]

The py is %LOCALAPPDATA%/facefit/.venv/Scripts/python.exe (uv venv, Python 3.11,
mediapipe); the model %LOCALAPPDATA%/facefit/models/face_landmarker.task.

A target's weight runs from 0 to its bound (BOUND); an "incr" and its "decr"
are two (the fit never wants both). The fit is regularised toward nothing
(the face as anchored), so a target the landmarks say little of stays put.
"""
import json
import os
import sys

import numpy as np

MODEL = os.path.join(os.environ.get("LOCALAPPDATA", ""), "facefit", "models", "face_landmarker.task")
BOUND = 1.0

# MediaPipe's landmarks by what they mark (its canonical face mesh's numbers).
OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409, 78, 95, 88, 178, 87, 14, 317,
        402, 318, 324, 308, 191, 80, 81, 82, 13, 312, 311, 310, 415]
EYES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 246, 161, 160, 159, 158, 157, 173, 263, 249, 390, 373, 374, 380, 381, 382, 362,
        466, 388, 387, 386, 385, 384, 398]
BROWS = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46, 300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
NOSE = [1, 2, 98, 327, 4, 5, 195, 197, 6, 168, 48, 278, 64, 294, 129, 358, 49, 279, 115, 344, 220, 440]
IRIS = list(range(468, 478))


def importance(n):
    """How much each landmark counts: the outlines of her features most,
    her face's outline more than its fill."""
    w = np.full(n, 0.35)
    for group, v in ((OVAL, 2.0), (LIPS, 1.5), (EYES, 1.5), (BROWS, 1.0), (NOSE, 1.5)):
        w[group] = v
    w[[i for i in IRIS if i < n]] = 0.0
    return w


def detect(img):
    """The landmarks of the face in an image (RGB array), in its pixels: x
    right, y down, z toward the viewer's far side (MediaPipe's, in x's units)."""
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    opts = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), num_faces=1)
    with vision.FaceLandmarker.create_from_options(opts) as lm:
        res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img[..., :3])))
    if not res.face_landmarks:
        return None
    h, w = img.shape[:2]
    return np.array([[p.x * w, p.y * h, p.z * w] for p in res.face_landmarks[0]])


def load(path, part="whole"):
    from PIL import Image
    img = np.asarray(Image.open(path).convert("RGB"))
    w = img.shape[1]
    if part == "left":
        return img[:, :w // 2], 0
    if part == "right":
        return img[:, w // 2:], w // 2
    return img, 0


def umeyama(src, dst, wt):
    """The scale, turn and shift taking src to dst, weighted (least squares)."""
    W = wt / wt.sum()
    ms, md = (W[:, None] * src).sum(0), (W[:, None] * dst).sum(0)
    a, b = src - ms, dst - md
    C = (W[:, None] * b).T @ a
    U, S, Vt = np.linalg.svd(C)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1, 1, d])
    R = U @ D @ Vt
    s = (S * np.diag(D)).sum() / (W * (a * a).sum(1)).sum()
    return s, R, md - s * R @ ms


def to_3d(L):
    """Image landmarks as points in a right-handed frame: x right, y up, z toward the viewer."""
    return np.c_[L[:, 0], -L[:, 1], -L[:, 2]]


def pose(P, q, wt, R=None):
    """How a view sees her: the turn (from MediaPipe's depths at first, then
    by the picture alone), and the scale and shift in the picture (MediaPipe's
    depths are of another scale than its x and y, so only x and y are
    matched)."""
    if R is None:
        _, R, _ = umeyama(P, q, wt)
    W = wt / wt.sum()
    for _ in range(12):
        X = (R @ P.T).T
        mx, mq = (W[:, None] * X[:, :2]).sum(0), (W[:, None] * q[:, :2]).sum(0)
        a, b = X[:, :2] - mx, q[:, :2] - mq
        s = (W * (a * b).sum(1)).sum() / (W * (a * a).sum(1)).sum()
        t = mq - s * mx
        r = q[:, :2] - (s * X[:, :2] + t)
        # (a small turn w moves a point by w x X: its x by wy Xz - wz Xy, its y by wz Xx - wx Xz)
        Jx = s * np.c_[np.zeros(len(X)), X[:, 2], -X[:, 1]]
        Jy = s * np.c_[-X[:, 2], np.zeros(len(X)), X[:, 0]]
        sw = np.sqrt(W)[:, None]
        Jm = np.vstack([Jx * sw, Jy * sw])
        om = np.linalg.lstsq(Jm, np.concatenate([r[:, 0] * sw[:, 0], r[:, 1] * sw[:, 0]]), rcond=None)[0]
        th = np.linalg.norm(om)
        if th < 1e-7:
            break
        k = om / th
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        R = (np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K) @ R
    return s, R, np.r_[t, 0.0]


def prepared(anchors):
    """An anchor set ready to fit with: its points about their middle (turned
    about the world's origin, a point 1.5 m up swings far for a small turn),
    their moves, and how much each counts."""
    P0, hit = anchors["P0"], anchors["hit"]
    return P0 - P0[hit].mean(0), anchors["D"], importance(len(P0)) * hit


def match(sets, Q):
    """Of anchor sets read off her at several turns, the one that sees her as
    this view does (least miss once posed): MediaPipe puts a landmark on a
    face a little differently from each side, the outline of a cheek most of
    all, so a view is fitted against her seen from as near its own angle."""
    q = to_3d(Q)
    best = None
    for k, (P0, D, imp) in enumerate(sets):
        n = min(len(q), len(P0))
        s, R, t = pose(P0[:n], q[:n], imp[:n] + 1e-9)
        e = np.linalg.norm(((s * (R @ P0[:n].T).T + t) - q[:n])[:, :2], axis=1) / s * 1000
        e = float((e * imp[:n]).sum() / imp[:n].sum())
        if best is None or e < best[1]:
            best = (k, e)
    return best[0]


def fit(views, targets, reg=30.0, start=None, iters=12, keep=None):
    """Her targets' weights that best take her anchored points onto each
    view's landmarks, in the picture: alternately each view's pose (turn,
    scale, shift) and the weights (bounded least squares). `views`: (anchor
    set, landmarks) pairs, the sets prepared()."""
    from scipy.optimize import lsq_linear
    J = len(targets)
    w = np.zeros(J) if start is None else np.array([start.get(t, 0.0) for t in targets])
    lo = np.zeros(J)
    hi = np.full(J, BOUND)
    if keep:                                          # (weights held where they are)
        for j, t in enumerate(targets):
            if t in keep:
                lo[j] = hi[j] = w[j]
                hi[j] += 1e-9
    Rs = [None] * len(views)
    for it in range(iters):
        rows, rhs, poses = [], [], []
        for vi, ((P0, D, imp), Q) in enumerate(views):
            P = P0 + np.tensordot(w, D, 1)
            q = to_3d(Q)
            n = min(len(q), len(P))
            s, R, t = pose(P[:n], q[:n], imp[:n] + 1e-9, Rs[vi])
            Rs[vi] = R
            poses.append((s, R, t))
            # (in millimetres of her face: `reg` is what a unit of weight costs, in mm² of one landmark's miss)
            cw = 1000 * np.sqrt(imp[:n])[:, None]
            A = np.einsum("ij,mkj->kim", R, D[:, :n])[:, :2]          # (k, 2, J)
            b = (q[:n, :2] - (s * (R @ P0[:n].T).T[:, :2] + t[:2])) / s
            rows.append((A * cw[:, :, None]).reshape(-1, J))
            rhs.append((b * cw).ravel())
        A = np.vstack(rows + [np.sqrt(reg) * np.eye(J)])
        b = np.concatenate(rhs + [np.zeros(J)])
        r = lsq_linear(A, b, bounds=(lo, hi), method="bvls")
        w = r.x
    err = []
    for ((P0, D, imp), Q), (s, R, t) in zip(views, poses):
        P = P0 + np.tensordot(w, D, 1)
        q = to_3d(Q)
        n = min(len(q), len(P))
        e = np.linalg.norm(((s * (R @ P[:n].T).T + t) - q[:n])[:, :2], axis=1) / s * 1000
        err.append(float((e * imp[:n]).sum() / imp[:n].sum()))
    # (turned from facing the camera: her world's up to the image's, her front toward the viewer)
    R0 = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])
    yaw = [float(np.degrees(np.arctan2((R @ R0.T)[0, 2], (R @ R0.T)[2, 2]))) for _, R, _ in poses]
    return {t: round(float(v), 3) for t, v in zip(targets, w) if v > 0.01}, err, yaw


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "marks":
        img, x0 = load(a[1], a[3] if len(a) > 3 else "whole")
        L = detect(img)
        if L is None:
            raise SystemExit("no face found in " + a[1])
        out = {"points": (L[:, :2] + [x0, 0]).tolist(), "z": L[:, 2].tolist()}
        if len(a) > 5:
            out["camera"] = json.load(open(a[4], encoding="utf-8-sig"))[a[5]]
        json.dump(out, open(a[2], "w"), indent=0)
        print("MARKS", len(L), "landmarks in", a[1])
    elif a[0] == "fit":
        # Anchor sets by commas: the first for the front view, the rest (her
        # seen turned by so many degrees each) for the other view to be matched to.
        names = a[1].split(",")
        raw = [dict(np.load(p)) for p in names]
        sets = [prepared(r) for r in raw]
        targets = [str(t) for t in raw[0]["targets"]]
        reg = float(a[a.index("--reg") + 1]) if "--reg" in a else 30.0
        start = json.load(open(a[a.index("--start") + 1], encoding="utf-8-sig")) if "--start" in a else None
        marks = []
        # (a reference's two halves; or pictures of one view each, by commas)
        for path, part in ([(p, "whole") for p in a[2].split(",")] if "," in a[2] else [(a[2], "left"), (a[2], "right")]):
            img, _ = load(path, part)
            L = detect(img)
            if L is None:
                raise SystemExit(f"no face in the {part} of {path}")
            marks.append(L)
        views = [(sets[0], marks[0])]
        for L in marks[1:]:
            k = 1 + match(sets[1:], L) if len(sets) > 1 else 0
            views.append((sets[k], L))
            print("VIEW matched to", os.path.basename(names[k]))
        # (targets held where they start: those that move her face toward or away from
        # the camera, which two views from in front say little of, are best set by eye in profile)
        keep = [t for t in targets if any(h in t for h in a[a.index("--hold") + 1].split(","))] if "--hold" in a else None
        w, err, yaw = fit(views, targets, reg=reg, start=start, keep=keep)
        json.dump(w, open(a[3], "w"), indent=1)
        print("FIT", a[2], "->", a[3], "error %s mm, turned %s deg" % ([round(e, 2) for e in err], [round(y) for y in yaw]))
        print(json.dumps(w))
