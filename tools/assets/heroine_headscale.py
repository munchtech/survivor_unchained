"""Her head made larger, in the exported body (s21, the owner 14 October 2026:
"def 6% maybe even 7": +7%, 8.0 heads, Loomis's idealistic figure).

The Head joint's rest is given a uniform scale and its inverse bind matrix is
left as it was, so everything skinned to her head (her face, eyes, lashes,
teeth, tongue, her hair, the hat and anything else an outfit binds to it) is
drawn that much larger about the head bone, and her neck blends by its own
weights, exactly as a pose scale on the head bone does (lookdev HEADSCALE,
the sheet the owner chose from). Her meshes' positions are untouched, so every
step that measures them in metres (heroine_mouth.seat, heroine_teethshade,
heroine_seam) keeps working, before or after this.
"""
import json
import struct


def scale(path, k):
    if abs(k - 1.0) < 1e-6:
        return
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    rest = d[20 + jl:]
    hit = [n for n in g["nodes"] if n.get("name") == "Head"]
    assert len(hit) == 1, "one Head node"
    hit[0]["scale"] = [k, k, k]
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = d[:12] + struct.pack("<I", len(js)) + d[16:20] + js + rest
    out = out[:8] + struct.pack("<I", len(out)) + out[12:]
    open(path, "wb").write(out)
    print("HEAD_SCALE %.3f: her head's rest scaled in %s" % (k, path))
