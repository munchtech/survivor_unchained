import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"src\Game\GameCinema.cs", [
('''                    var to = Atmospheres.ByName(c.Str("preset")!);
                    if (over > 0 && !skipping && c.Str("from") is string fromName)
                    {
                        var from = Atmospheres.ByName(fromName);
                        double last = -1;
                        tweens.Add(new Tween(t0, t0 + over, k => { if (k - last > 0.02 || k >= 1) { last = k; g.SetAtmosphere(Atmospheres.Blend(from, to, k), k >= 1); } }));
                    }
                    else g.SetAtmosphere(to);
                    break;''',
'''                    // A blend of a part of the way, "k0" to "k1" (a dawn begun in one
                    // cinematic and finished in the next); a skip lands on k1.
                    var to = Atmospheres.ByName(c.Str("preset")!);
                    double k0 = c.Num("k0"), k1 = c.Num("k1", 1);
                    if (c.Str("from") is string fromName)
                    {
                        var from = Atmospheres.ByName(fromName);
                        if (over > 0 && !skipping)
                        {
                            double last = -1;
                            tweens.Add(new Tween(t0, t0 + over, k =>
                            {
                                if (k - last <= 0.02 && k < 1) return;
                                last = k;
                                g.SetAtmosphere(Atmospheres.Blend(from, to, k0 + (k1 - k0) * k), k >= 1);
                            }));
                        }
                        else g.SetAtmosphere(k1 >= 1 ? to : Atmospheres.Blend(from, to, k1));
                    }
                    else g.SetAtmosphere(to);
                    break;'''),
])
print("ok")
