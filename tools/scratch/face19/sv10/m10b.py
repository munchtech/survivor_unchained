"""m10b.py: C# hair19 throw braid against hs10 with the braid's corner rule (cm), and its seen turns c3+ against hair17d."""
from hs10 import *
fr = lg("hair19", "throw_braid"); xs, _ = sim10(fr, "braid", sm=60, smheld=1, smvn=1); cs = today(fr)
e = [np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(xs, cs)][:-1]
print("C# hair19 vs replica: worst %.3f cm" % max(e))
for S in ("hair17d", "hair19"):
    f2 = lg(S, "throw_braid"); c2 = today(f2)
    print(S, "seen worst |turn| p1-p5 c3-c10.5:", " ".join("%.0f" % np.abs(turns2(c2[k])[0][:5]).max() for k in range(6, len(f2) - 1)))
