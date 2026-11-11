"""The keyed talk laid over a folk clip (talk.py, folk.py's men's "talk"): no keys leave the clip as it came; one
gesture raises the wrist by the asked amount at the key's time, the upper arm's line where the clip has it."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import talk  # noqa: E402
from rig import DATA, Skeleton, qaxis, qbetween, qmul, qinv  # noqa: E402


def _hang(sk, frames=61):
    """The folk man standing, both arms hanging, the elbows 20 degrees bent forward, a slow sway in the trunk."""
    g, p = sk.rest_globals()
    g, p = g[0], p[0]
    rot = np.repeat(sk.rest_rot[None], frames, axis=0).copy()
    for s in "lr":
        ua, la = sk.i(f"upperarm_{s}"), sk.i(f"lowerarm_{s}")
        down = qbetween(p[la] - p[ua], np.array([0.0, -1.0, 0.0]))
        gu = qmul(down, g[ua])
        gl = qmul(qaxis([-1.0, 0, 0], 20.0), qmul(down, g[la]))
        rot[:, ua] = qmul(qinv(g[sk.parent[ua]]), gu)
        rot[:, la] = qmul(qinv(gu), gl)
    sp = sk.i("spine_01")
    for f in range(frames):
        rot[f, sp] = qmul(rot[f, sp], qaxis([0, 0, 1.0], 2.0 * np.sin(2 * np.pi * f / (frames - 1))))
    return rot, np.repeat(sk.rest_pos[None], frames, axis=0).copy()


@pytest.fixture(scope="module")
def man():
    try:
        talk.keyed_curve()
    except SystemExit:
        pytest.skip("Marionette's motion core is not on this machine")
    sk = Skeleton.load(DATA / "folk_male_skeleton.json")
    return (sk, *_hang(sk))


def test_no_keys_leave_the_clip_untouched(man):
    sk, rot, pos = man
    for spec in ({}, {"hand_r": [], "nod": []}, {"hand_r": [[0.5, 0, "still"], [1.5, 0]]}):
        out, said = talk.lay(sk, rot, pos, spec)
        assert np.array_equal(out, rot)
    assert talk.lay(sk, rot, pos, {})[1] == ""


def test_one_gesture_raises_the_hand_by_the_asked_amount(man):
    sk, rot, pos = man
    spec = {"hand_r": [[0.5, 0, "still"], [1.0, 0.12, "still"], [1.5, 0, "still"]],
            "palm_r": [[0.5, 0, "still"], [1.0, 30, "still"], [1.5, 0, "still"]]}
    out, said = talk.lay(sk, rot, pos, spec)
    (_, p0), (_, p1) = sk.fk(rot, pos), sk.fk(out, pos)
    ua, la, ha = (sk.i(b) for b in ("upperarm_r", "lowerarm_r", "hand_r"))
    rise = p1[:, ha, 1] - p0[:, ha, 1]
    assert abs(rise[30] - 0.12) < 1e-6 and rise.max() < 0.12 + 1e-6 and rise.min() > -1e-6
    assert p1[30, ha, 2] > p0[30, ha, 2] + 0.05                       # up and forward, not back
    u0, u1 = p0[:, la] - p0[:, ua], p1[:, la] - p1[:, ua]
    cos = np.sum(u0 * u1, axis=1) / (np.linalg.norm(u0, axis=1) * np.linalg.norm(u1, axis=1))
    assert np.degrees(np.arccos(np.clip(cos, -1, 1))).max() < 8.0     # (it is 0: only the elbow flexes)
    assert np.abs(p1[:, la] - p0[:, la]).max() < 1e-9                 # the elbow stays at the hang
    arm = {sk.i(f"{b}_r") for b in ("upperarm", "lowerarm", "hand")}
    rest = [j for j in range(len(sk)) if j not in arm]
    assert np.array_equal(out[:, rest], rot[:, rest])                 # the trunk, the legs, the head, the other arm
    assert np.array_equal(out[:15], rot[:15]) and np.array_equal(out[46:], rot[46:])
    assert "right hand raised to 12 cm" in said


def test_a_gesture_across_the_seam_is_refused(man):
    sk, rot, pos = man
    with pytest.raises(SystemExit):
        talk.lay(sk, rot, pos, {"nod": [[0.0, 5], [1.0, 0]]})
    with pytest.raises(SystemExit):
        talk.lay(sk, rot, pos, {"nod": [[1.0, 0, "still"], [9.0, 5]]})


def test_the_declared_talk_reads_its_keys():
    import folk
    name = folk.FOLK["talk"]["m"][2]["talk"]
    spec = talk.spec_of(name)
    assert set(spec) <= set(talk.CHANNELS) and {"hand_l", "hand_r", "nod"} <= set(spec)
    for keys in spec.values():
        ts = [k[0] for k in keys]
        assert ts == sorted(ts) and keys[0][1] == 0 and keys[-1][1] == 0
