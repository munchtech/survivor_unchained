def summ(o,tag):
    for s in "rl":
        r=o[s]; t=r["top"]
        print(f"{tag:12s}[{s}] pitR {r['pit_rest']:3.0f} A82>30 {r['A82_pit30']:2d} flask {r['flask_pitcr']:3.0f} catch {r['catch_pitcr']:3.0f} elb {r['A82_elb']:.0%} | idle "+"/".join(f"{x:.2f}" for x in r["idle_sec"])+" A58 "+"/".join(f"{x:.2f}" for x in r["A58_sec"])+" A82 "+"/".join(f"{x:.2f}" for x in r["A82_sec"])
              +" | "+" ".join(f"{k[4:7]} {r[k]['seg']:.1f}/{r[k]['turn']:.0f}" for k in ("sil_deltoid","sil_shoulder_top","sil_bicep") if r[k])
              +(f" | top {t['total']:.0f}d min {t['min']:.0f} conc {t['conc']:.0%}: "+" ".join(f"{x:.0f}" for x in t["turns"]) if t else ""))
