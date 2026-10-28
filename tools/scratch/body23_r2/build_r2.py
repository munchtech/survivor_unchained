"""R2 body: loops-v2 (pit band) + C3's elbow_psd{45,90,135}_{l,r} (r1b's fields, mapped by place; NOT its rest/cap field):
A's rest shape everywhere.   python build_r2.py FIELDS.npz OUT.glb"""
import sys, os, json, struct, numpy as np
from scipy.spatial import cKDTree
import r2lib as c
sys.path.insert(0, os.path.join(c.B22, "shoulder"))
import apply
from heroine_neck import _Gl
import pit_hollow_post as ph
from worn_reaver_post import _sparse

PSD = ("elbow_psd45", "elbow_psd90", "elbow_psd135")


def main(fz, out, k=1.0):
    F = np.load(fz)
    b1 = ph.Body(_Gl(c.V1[0])); b2 = ph.Body(_Gl(c.V2[0]))
    def nrm(b):
        N = ph.vn(b.U, b.F)
        for _ in range(3):
            N = N + b.lap(N) * 0.5
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        return N
    N2 = nrm(b2)
    d, j = cKDTree(b1.U).query(b2.U, k=3)
    old = d[:, 0] < 1e-6
    wgt = np.where(old[:, None], np.eye(3)[0], 1.0 / np.maximum(d, 1e-6))
    wgt /= wgt.sum(1, keepdims=True)
    apply.write(c.V2[0], out, np.zeros_like(b2.U), mark="r2_c3_elbow")
    G = _Gl(out); g = G.g
    bb = ph.Body(G)
    assert len(bb.U) == len(b2.U)
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    Nr = ph.vn(bb.U, bb.F)
    for f in PSD:
        for sd in "lr":
            h1 = F["%s_%s" % (f, sd)]
            h2 = (h1[j] * wgt).sum(1) * k
            D = h2[:, None] * N2 / 1000
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
                ip = ip if len(ip) else np.array([0]); inn = inn if len(inn) else np.array([0])
                p.setdefault("targets", []).append({"POSITION": _sparse(g, binb, n, ip, Dp[ip]), "NORMAL": _sparse(g, binb, n, inn, dNp[inn])})
            mesh.setdefault("extras", {}).setdefault("targetNames", []).append("%s_%s" % (f, sd))
            mesh["weights"] = list(mesh.get("weights", [])) + [0]
            print("%s_%s: most %.1f mm" % (f, sd, np.abs(h2).max()))
    g["asset"]["extras"]["elbow_psd"] = {"by": "body23 r2: r1b C3's elbow fields (%s) on loops-v2, k %.2f" % (os.path.basename(fz), k)}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(out, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("written", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
