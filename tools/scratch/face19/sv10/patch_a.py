"""patch_a.py: add option dpost to hs10's loop: a touching point's pull from below (follow-the-leader) kept after the
contact pass (which otherwise sets its speed afresh): dpost='lod' lodged points only, 'all' every touching point;
dfree: as if free (1) or as far as free/lodged (0)."""
p = open("hs10.py").read()
old = """            xp[i] = x[i] - u - r * (1 - g)
            s.grip[i] = 0; s.surf[i] = 0"""
new = """            xp[i] = x[i] - u - r * (1 - g)
            dp = o.get("dpost")
            if dp and i < 7 and (dp == "all" or lod[i] > 0):
                f = 1.0 if dp == "all" and o.get("dfree") else (max(free[i], lod[i]) if dp == "lod" else free[i])
                dv = -0.9 * f * corr[i + 1] * o.get("dgain", 1.0); vn = dv @ n
                if vn < 0: dv = dv - n * vn
                xp[i] = xp[i] - dv
            s.grip[i] = 0; s.surf[i] = 0"""
assert old in p; p = p.replace(old, new); open("hs10.py", "w").write(p); print("ok")
