p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_links.py'
s = open(p, encoding='utf-8').read()
old = '''        bpy.data.objects.remove(ob, do_unlink=True)


if __name__ == "__main__":'''
new = '''        bpy.data.objects.remove(ob, do_unlink=True)
    if spec.get("eyelet"):
        eyelet(spec, sc, out, ss, length, width, wire, states[""])


def eyelet(spec, sc, out, ss, length, width, wire, iron):
    """The chain's anchor (eyelet.png): a forged iron grommet set into the band, its hole wide
    enough for a link to pass, rubbed bright inside where the chain has run through it, with
    two small nails either side. The hole's darkness is added after (chain.py)."""
    e = spec["eyelet"]
    hole = e["hole"] * ss                      # inner radius, render px
    bar = e["bar"] * ss
    bpy.ops.mesh.primitive_torus_add(major_radius=(hole + bar) * U, minor_radius=bar * U,
                                     major_segments=96, minor_segments=24, location=(0, 0, bar * 0.55 * U))
    ring = bpy.context.active_object
    ring.scale = (1.0, 1.0, 0.6)               # forged flat, not a round bar
    bpy.ops.object.transform_apply(scale=True)
    ring.data.materials.append(iron)
    # Where the chain runs through it: a link passing the hole, there only to find the wear.
    lk, _ = C.link_mesh("pass", length * U, width * U, wire * U)
    lk.rotation_euler = (math.pi / 2, 0, 0)
    lk.location = (0, 0, 0)
    bpy.context.view_layer.update()
    C.mark_wear([lk, ring], wire * U)
    bpy.data.objects.remove(lk, do_unlink=True)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=e["nail"] * ss * U, location=((hole + bar * 2 + e["nail"] * ss * 1.6) * sx * U, 0, 0))
        nl = bpy.context.active_object
        nl.scale = (1, 1, 0.5)
        nl.data.materials.append(iron)
    sc.render.filepath = os.path.join(out, "eyelet.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''            "pitch": pitch * 2, "variants": variants, "seed": 5, "gap": 16}''', '''            "pitch": pitch * 2, "variants": variants, "seed": 5, "gap": 16,
            "eyelet": {"hole": 12.5 * 2, "bar": 3.4 * 2, "nail": 1.8 * 2}}''')
s = s.replace('''    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open"]''',
              '''    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open", "eyelet"]''')
s = s.replace('''        if nm.startswith("hot_") or nm == "open":
            img = ember_glow(img, 0.7, edge=10)''', '''        if nm.startswith("hot_") or nm == "open":
            img = ember_glow(img, 0.7, edge=10)
        if nm == "eyelet":
            img = hole_dark(img, 12.5 * 2)''')
s = s.replace('''def links(variants=6''', '''def hole_dark(img, r):
    """The eyelet's hole: dark going down into the band, darkest at its middle, so a link
    drawn under it fades into the dark as it goes in (r in file px)."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot(xx - w / 2 + 0.5, yy - h / 2 + 0.5) / r
    dark = np.clip(1.15 - d, 0, 1) ** 0.6 * 0.96 * (d < 1.02)
    out = img.copy()
    a = out[..., 3]
    out[..., :3] = (out[..., :3] * a[..., None] + np.array([0.012, 0.008, 0.008], np.float32) * (dark * (1 - a))[..., None]) / \\
        np.maximum((a + dark * (1 - a))[..., None], 1e-4)
    out[..., 3] = a + dark * (1 - a)
    return out


def links(variants=6''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
