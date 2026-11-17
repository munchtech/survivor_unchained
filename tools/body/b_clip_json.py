"""B's clips in tools/anim's clip layout (A's: tracks of bone / rot|pos / keys), for tools that read clips by bone name
on B's skeleton (tools/anim/data/body_p1_skeleton.json): lane D's kit checks with --body p1 (idle_warden, run_warden,
sword_heavy, leap). Lane G, 17 Nov 2026.

    python tools/body/b_clip_json.py <dump dir> <out dir> <clip> [<clip> ...]

<dump dir>: the bake's keys dump (tools/body/out/clips/<clip>.json, git-ignored), written by
`bash tools/body/bake_clips.sh --p1-bake-only <clip>` (P1BakeRun: B's baked globals per frame, the clip as the shipped
her_clips.res plays it). Each keyed bone's local turn is G_parent^-1 G (the 3x3 made orthonormal: the dump has 5
decimals), the pelvis also its local position. Unkeyed bones get no track (skin.Body.clip leaves them at rest).
Not body_p1/p4/: that folder is P4's build output, and p4_pack.sh would pack these as overlays over B's clips.
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SKEL = REPO / "tools" / "anim" / "data" / "body_p1_skeleton.json"


def mat(r):
    m = np.array(r, float).reshape(3, 4)
    u, _, vt = np.linalg.svd(m[:, :3])
    R = u @ vt
    if np.linalg.det(R) < 0:
        u[:, -1] *= -1
        R = u @ vt
    return R, m[:, 3]


def quat(R):
    """xyzw, w >= 0."""
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1.0) * 2
        q = [(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s]
    else:
        i = int(np.argmax(np.diag(R)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1.0 + R[i, i] - R[j, j] - R[k, k]) * 2
        q = [0.0] * 4
        q[i] = 0.25 * s
        q[j] = (R[j, i] + R[i, j]) / s
        q[k] = (R[k, i] + R[i, k]) / s
        q[3] = (R[k, j] - R[j, k]) / s
    q = np.array(q)
    q /= np.linalg.norm(q)
    return q if q[3] >= 0 else -q


def convert(dump, skel_names):
    names, parent = dump["b_names"], dump["b_parent"]
    assert names == skel_names, "the dump's bones are not body_p1_skeleton.json's (republished body? redump both)"
    tracks = {}
    prev = {}
    for fr in dump["B"]:
        G = [mat(r) for r in fr]
        for b in dump["keyed"]:
            j = names.index(b)
            p = parent[j]
            Rp, tp = (np.eye(3), np.zeros(3)) if p < 0 else G[p]
            R = Rp.T @ G[j][0]
            q = quat(R)
            if b in prev and float(np.dot(prev[b], q)) < 0:   # (the short way from the last key)
                q = -q
            prev[b] = q
            tracks.setdefault((b, "rot"), []).append([round(float(v), 6) for v in q])
            if b == "pelvis":
                t = Rp.T @ (G[j][1] - tp)
                tracks.setdefault((b, "pos"), []).append([round(float(v), 6) for v in t])
    return [{"bone": b, "type": ty, "keys": k} for (b, ty), k in tracks.items()]


def main():
    src, out, clips = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
    skel_names = [b["name"] for b in json.loads(SKEL.read_text())["bones"]]
    out.mkdir(parents=True, exist_ok=True)
    for c in clips:
        d = json.loads((src / f"{c}.json").read_text())
        clip = {"name": d["name"], "fps": d["fps"], "loop": d["loop"], "length": d["length"],
                "path": "Armature/Skeleton3D", "tracks": convert(d, skel_names),
                "meta": {"body": "p1", "source": "B's baked keys (bake_clips.sh --p1-bake-only dump), tools/body/b_clip_json.py",
                         "frames": d["frames"]}}
        (out / f"{c}.json").write_text(json.dumps(clip, separators=(",", ":")) + "\n")
        print(c, d["frames"], "frames,", len(clip["tracks"]), "tracks")


if __name__ == "__main__":
    main()
