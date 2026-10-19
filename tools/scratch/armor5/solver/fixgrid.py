"""Re-sign the grid's far voxels (beyond the 30 mm shell signed exactly): outside iff connected to an outside boundary
voxel without crossing the shell's inside. python fixgrid.py <in.npz> <out.npz>"""
import sys, numpy as np
from scipy import ndimage
z = dict(np.load(sys.argv[1]))
D = z["D"]
flips = 0
for f in range(len(D)):
    d = D[f]
    barrier = (d > 0) & (d <= 30)
    lab, n = ndimage.label(~barrier)
    bd = np.zeros_like(barrier)
    bd[[0, -1]] = True; bd[:, [0, -1]] = True; bd[:, :, [0, -1]] = True
    seeds = np.unique(lab[bd & (d < 0) & ~barrier])
    outside = np.isin(lab, seeds[seeds > 0])
    far = np.abs(d) > 30
    new = np.where(far, np.where(outside, -np.abs(d), np.abs(d)), d)
    flips += int((np.sign(new) != np.sign(d)).sum())
    D[f] = new
z["D"] = D
np.savez_compressed(sys.argv[2], **z)
print("flipped", flips, "voxels over", len(D), "frames")
