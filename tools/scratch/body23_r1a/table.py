import k, m, numpy as np, warnings, pickle, sys
warnings.filterwarnings('ignore')
M = m.JUDGED + [("w_m80", "l", ("crease",))]
res = {}
for c in sys.argv[1:]:
    dU = np.load(c + "/dU.npy"); sh = dict(np.load(c + "/shapes.npz"))
    B = k.Body(dU=dU, shapes=sh)
    res[c] = m.report(B, log=lambda *a: None)
pickle.dump(res, open("table_%s.pkl" % "_".join(sys.argv[1:]), "wb"))
cs = sys.argv[1:]
print("frame    sd region   " + "  ".join("%-22s" % ("%s max/mean sil-range" % c) for c in cs))
for f, sd, regs in m.JUDGED:
    for rn in regs:
        row = "%-8s %s  %-7s" % (f, sd, rn)
        for c in cs:
            v = res[c][(f, sd)][0].get(rn)
            row += "  %-22s" % ("%.1f/%.1f [%s..%s]" % (v["max"], v["mean"], v["sil_min"], v["sil_max"]) if v else "-")
        print(row)
for c in cs:
    print(c, "look_f width delta %+.1f px" % res[c]["look_w"])
print("knots (B/A): dih p99 deg, H conv max 1/mm")
for f, sd, regs in m.JUDGED:
    for c in cs:
        kn, knA = res[c][(f, sd)][1], res[c][(f, sd)][2]
        print("  %s %-8s %s " % (c, f, sd) + " ".join("%s %.0f/%.0f %.2f/%.2f" % (rn, v["dih_p99"], knA[rn]["dih_p99"], v["H_conv_max"], knA[rn]["H_conv_max"]) for rn, v in kn.items()))
for f, sd in m.OTHER:
    row = "other %-8s %s" % (f, sd)
    for c in cs:
        mv = res[c][(f, sd)][0]
        row += "  %s max %s" % (c, max([v["max"] for v in mv.values() if v] or [0]))
    print(row)
