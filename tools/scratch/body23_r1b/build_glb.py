"""C3: write the solved body: A (looped) + the rest move h0 N (normals updated, shoulder PSDs kept: B22 apply.write) +
elbow_psd{45,90,135}_{l,r} morph targets (h N, sparse, with normal deltas; the game drives them: ElbowPsd.cs).
    python build_glb.py FIELDS.npz OUT.glb"""
import sys, json, struct, numpy as np
import c3lib as c
sys.path.insert(0, c.os.path.join(c.B22, "shoulder"))
import apply
from heroine_neck import _Gl
import pit_hollow_post as ph
sys.path.insert(0, c.WT + r"\tools\assets")
from worn_reaver_post import _sparse

PSD = ("elbow_psd45", "elbow_psd90", "elbow_psd135")


def main(fz, out):
    F = np.load(fz); b = c.body()
    dU = (F["h0_l"] + F["h0_r"])[:, None] * b.N / 1000
    apply.write(c.A_GLB, out, dU, mark="c3_outline_solve")
    G = _Gl(out); g = G.g
    bb = ph.Body(G)
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    Nr = ph.vn(bb.U, bb.F)
    for f in PSD:
        for sd in "lr":
            D = F["%s_%s" % (f, sd)][:, None] * b.N / 1000
            dN = ph.vn(bb.U + D, bb.F) - Nr
            o = 0
            for p in prims:
                n = g["accessors"][p["attributes"]["POSITION"]]["count"]
                w = bb.wid[o:o + n]; o += n
                Dp = D[w]
                Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
                Nn = Ns + dN[w]; Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
                dNp = np.where((np.abs(dN[w]).max(1) > 1e-5)[:, None], Nn - Ns, 0)
                ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]; inn = np.nonzero(np.abs(dNp).max(1) > 0)[0]
                if len(ip) == 0:
                    ip = np.array([0]);
                if len(inn) == 0:
                    inn = np.array([0])
                p.setdefault("targets", []).append({"POSITION": _sparse(g, binb, n, ip, Dp[ip]), "NORMAL": _sparse(g, binb, n, inn, dNp[inn])})
            mesh.setdefault("extras", {}).setdefault("targetNames", []).append("%s_%s" % (f, sd))
            mesh["weights"] = list(mesh.get("weights", [])) + [0]
    g["asset"]["extras"]["elbow_psd"] = {"by": "body23 r1b C3 outline solve (fields %s)" % c.os.path.basename(fz)}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(out, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("written", out, "rest move max %.1f mm" % (np.linalg.norm(dU, axis=1).max() * 1000))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
