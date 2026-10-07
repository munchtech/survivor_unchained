"""Her recorded place is in the viewport's own 1920x1080 (the canvas stretch): scale it to each picture."""
import pathlib

here = pathlib.Path(__file__).parent
c = (here / "crops.py").read_text(encoding="utf-8")
helper = '''

def her_at(f, a):
    """Her place in picture f (array a): recorded in the viewport's 1920x1080, scaled to the picture."""
    p = AT.get(f)
    if p is None:
        return (a.shape[1] // 2, a.shape[0] // 2)
    return (round(p[0] * a.shape[1] / 1920), round(p[1] * a.shape[0] / 1080))
'''
c = c.replace("\n\ndef frames(tag):", helper + "\n\ndef frames(tag):", 1)
c = c.replace("c = AT.get(f, (a0.shape[1] // 2, H // 2))", "c = her_at(f, a0)")
c = c.replace("c = AT.get(f, (a.shape[1] // 2, H // 2))", "c = her_at(f, a)")
c = c.replace("c = AT.get(fs[0], (W // 2, H // 2))", "c = her_at(fs[0], st[0][..., None])")
(here / "crops.py").write_text(c, encoding="utf-8")
u = (here / "cut.py").read_text(encoding="utf-8")
u = u.replace("c = C.AT.get(f, (a.shape[1] // 2, H // 2))", "c = C.her_at(f, a)")
(here / "cut.py").write_text(u, encoding="utf-8")
print("ok", c.count("her_at("), u.count("her_at("))
