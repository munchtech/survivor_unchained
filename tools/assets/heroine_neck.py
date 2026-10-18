"""Her neck shortened (the owner, 18 October 2026: "our neck is just too long ... freakishly long"; slightly
long is fine, for helmets and gorgets. He picked B from the 1:1 sheet: 3 cm shorter, chin to sternal notch
about 8.5 cm, 0.37 of her head's height, the real average).

    import heroine_neck; heroine_neck.shorten_glb(<heroine.glb>, delta)     (delta in metres; 0 does nothing)

Her Head joint's rest moved `delta` down her neck's own line (its translation in neck_01's space, the neck
bone's length, shortened), her meshes and their skin left as they are. That is exactly what the game's
`--neck-cm -X` drew for the sheet (HerPose: the Head bone's pose position moved along its rest origin), now
her rest: her head, face and hair keep their shapes, the skin weighted between neck_01 and Head is drawn
shorter, and every piece and hair bound to her skeleton follows as her skin does. Run last on the glb, like
heroine_headscale.py, after every step that measures her head (the face steps find her lips by position).
"""
import json
import struct


def shorten_glb(path, delta):
    if not delta:
        return
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    rest = d[20 + jl:]
    hit = [n for n in g["nodes"] if n.get("name") == "Head"]
    assert len(hit) == 1, "one Head node"
    t = hit[0].get("translation", [0.0, 0.0, 0.0])
    L = sum(c * c for c in t) ** 0.5
    assert L > delta, "the neck is shorter than the cut"
    hit[0]["translation"] = [c * (L - delta) / L for c in t]
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = d[:12] + struct.pack("<I", len(js)) + d[16:20] + js + rest
    out = out[:8] + struct.pack("<I", len(out)) + out[12:]
    open(path, "wb").write(out)
    print("NECK_CUT %.1f mm: her Head joint's rest %.1f -> %.1f mm up her neck in %s" % (delta * 1000, L * 1000, (L - delta) * 1000, path))
