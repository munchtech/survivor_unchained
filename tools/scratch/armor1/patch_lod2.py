import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
L = s.split("\r\n")
a = next(i for i, l in enumerate(L) if l == "    by_mat = {}")
b = next(i for i in range(a, a + 30) if L[i] == '        parts.append(("outfit", mat, attrs, np.concatenate(tris)))')
L[a:b + 1] = '''    by_mat = {}
    for mi, m in enumerate(full.js["meshes"]):
        for mat, attrs, tris in full.prims(mi):
            by_mat.setdefault(mat, []).append((m.get("extras", {}), attrs, tris))
    for mat in sorted(by_mat):
        attrs, tris = slot_join(by_mat[mat], f"{outfit} {mat}")
        parts.append(("outfit", mat, attrs, tris))'''.split("\n")
c = next(i for i, l in enumerate(L) if l == "def lod(folder, outfit):")
L[c:c] = '''def slot_join(items, tag=""):
    """One material's meshes of an outfit, one a slot ((glTF extras, attributes, triangles) each), joined back into the
    one mesh a material was before slots (heroine_outfits.py, armor lead 1): each slot mesh's pieces (extras "pieces":
    [their place in the material's join, their triangles]) cut out, each piece's own run of vertices, and laid back
    in the join's order. Without "pieces", the meshes end to end in their "rank"."""
    keys = list(items[0][1])
    assert all(set(a) == set(keys) for _, a, _ in items), f"{tag}: its slots' meshes carry different attributes"
    for k in keys:
        assert len({a[k][0].dtype for _, a, _ in items}) == 1 and len({a[k][1] for _, a, _ in items}) == 1, f"{tag} {k}"
    chunks = []     # (place in the join, item, first vertex, end vertex, triangles)
    for n, (ex, a, t) in enumerate(items):
        pcs = ex.get("pieces") or [[ex.get("rank", 0) * 100000, len(t)]]
        assert sum(nt for _, nt in pcs) == len(t), f"{tag}: {ex.get('slot')}'s pieces have {sum(nt for _, nt in pcs)} triangles, its mesh {len(t)}"
        off, vend = 0, 0
        for j, nt in pcs:
            tt = t[off:off + nt]
            off += nt
            if not nt:
                continue
            v0, v1 = int(tt.min()), int(tt.max()) + 1
            assert v0 == vend, f"{tag}: a piece's vertices not in one run after the last ({v0} after {vend})"
            vend = v1
            chunks.append((j, n, v0, v1, tt))
        assert vend == len(a["POSITION"][0]), f"{tag}: {len(a['POSITION'][0]) - vend} vertices in no piece"
    chunks.sort(key=lambda c: c[0])
    attrs = {k: (np.concatenate([items[n][1][k][0][v0:v1] for _, n, v0, v1, _ in chunks]), items[0][1][k][1]) for k in keys}
    tris, base = [], 0
    for _, n, v0, v1, tt in chunks:
        tris.append(tt - v0 + base)
        base += v1 - v0
    return attrs, np.concatenate(tris)

'''.split("\n")
open(p, "w", encoding="utf-8", newline="").write("\r\n".join(L))
print("ok")
