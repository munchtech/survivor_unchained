"""Paint-over trials of a relief render at a few denoise levels."""
import sys
import numpy as np
from sp import *
sys.path.insert(0, os.path.join(W, "tools", "uiforge"))
import paintover as PO
import forge as F

name, ver = sys.argv[1], sys.argv[2]
prompt = sys.argv[3]
dens = [float(x) for x in sys.argv[4].split(",")]
img = np.asarray(Image.open(os.path.join(OUT, "relief", name + ".png")).convert("RGBA"), np.float32) / 255
fw = int(sys.argv[5]) if len(sys.argv) > 5 else img.shape[1] // 8
row = [F.to_pil(F.downsample(img, (fw, fw)))]
bigs = []
for dn in dens:
    p = PO.paint(img, prompt, f"{name}_{ver}_{int(dn*100)}", denoise=dn, seed=11, keep_light=0.75)
    F.to_pil(p).save(os.path.join(V, f"{name}_{ver}_{int(dn*100)}_big.png"))
    row.append(F.to_pil(F.downsample(p, (fw, fw))))
    bigs.append(F.to_pil(p).resize((464, 464), Image.LANCZOS))
s = sheet(row, sizes=(None, fw // 2))
s.save(os.path.join(V, f"{name}_{ver}_po.png"))
sheet([on_bg(F.to_pil(img).resize((464, 464), Image.LANCZOS))] + [on_bg(b) for b in bigs]).save(os.path.join(V, f"{name}_{ver}_po_big.png"))
