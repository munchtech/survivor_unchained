import sys, numpy as np, c3lib as c, solve as S
b = c.body(); R = S.regions(b)
F = np.load(sys.argv[1] + "_fields.npz")
for k in F.files:
    v = F[k]; sd = k[-1]
    nz = np.abs(v) > 1e-9
    if not nz.any():
        continue
    i = np.argmax(np.abs(v))
    dsh = np.linalg.norm(b.U[i] - R[sd]["Sh"]) * 1000; de = np.linalg.norm(b.U[i] - R[sd]["El"]) * 1000
    print("%-18s max %6.1f  p99 %5.1f  p90 %5.1f  (+%.1f / %.1f)  at d_sh %.0f d_el %.0f mm  y %.0f" % (k, v[i], np.percentile(np.abs(v[nz]), 99), np.percentile(np.abs(v[nz]), 90), v.max(), v.min(), dsh, de, (b.U[i, 1] - R[sd]["Sh"][1]) * 1000))
