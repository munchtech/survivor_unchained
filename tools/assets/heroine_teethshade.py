"""Her side teeth in the mouth's own shade, in her exported glb (heroine.glb): a vertex colour on her teeth.

Her teeth are lit as if the mouth were open to the sky: at the Look (her chin lifted 12 degrees) Sunborn's closed lips
leave a gap at the corner of her mouth, and the canine and premolar behind it read as a white-pink speck (judge s1;
the solver's teeth-green test: Sunborn 44 pixels, Vixen 1). In a real mouth the teeth behind the corners stand in the
cheeks' shade (the buccal corridor), so a smile shows its front teeth lit and its side teeth darker. This gives her
teeth a grey vertex colour (COLOR_0, linear) that is 1 over her front teeth and eases down to SIDE from FRONT to BACK
metres off her mouth's middle (each side alike); People.cs multiplies her teeth's paint by it.

    python tools/assets/heroine_teethshade.py [GLB [OUT]]

On one already done (its teeth mesh's extras say teeth_shade) it does nothing. heroine_outfits.py runs it on the body it
exports, after the seam and the brow fold.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb")
FRONT, BACK = 0.011, 0.020   # (m off her mouth's middle: lit to here, in the cheeks' shade from here)
SIDE = 0.25                  # (her side teeth's colour, linear: the cheeks' shade)


def shade(path, out=None):
    js, binc = hs._load(path)
    mats = [m.get("name") for m in js.get("materials", [])]
    hit = [(m, p) for m in js["meshes"] for p in m["primitives"] if "material" in p and mats[p["material"]] == "teeth"]
    if len(hit) != 1:
        raise SystemExit("TEETHSHADE: found %d teeth primitives" % len(hit))
    m, p = hit[0]
    if "teeth_shade" in m.get("extras", {}):
        print("TEETHSHADE: already done in", path, "- nothing done")
        return
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    V = hs._read(js, binc, p["attributes"]["POSITION"])
    mid = 0.5 * (V[:, 0].min() + V[:, 0].max())
    x = np.clip((np.abs(V[:, 0] - mid) - FRONT) / (BACK - FRONT), 0, 1)
    g = 1 - (1 - SIDE) * x * x * (3 - 2 * x)
    col = np.repeat(g[:, None], 3, 1).astype("<f4")
    bvi = len(js["bufferViews"])
    js["bufferViews"].append({"buffer": 0, "byteLength": col.nbytes})
    chunks[bvi] = col.tobytes()
    js["accessors"].append({"bufferView": bvi, "componentType": 5126, "count": len(col), "type": "VEC3"})
    p["attributes"]["COLOR_0"] = len(js["accessors"]) - 1
    m.setdefault("extras", {})["teeth_shade"] = {"front": FRONT, "back": BACK, "side": SIDE}
    hs._save(out or path, js, chunks)
    print("TEETHSHADE: %d points, middle x %.4f, %d at full shade; written %s" % (len(g), mid, int((g <= SIDE + 1e-6).sum()), out or path))


if __name__ == "__main__":
    a = sys.argv[1:]
    shade(a[0] if a else GLB, a[1] if len(a) > 1 else None)
