import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Weapons.cs', [
("""        if (atTarget)
        {
            var t = b.DensestHostile(p.X, p.Z, 11, r);
            if (t == null) return false;
            x = t.X; z = t.Z;
        }""", """        if (atTarget)
        {
            // Every other one goes under a champion or worse, when one is near:
            // a field that only ever finds the crowd never brings down what leads it.
            var big = (w.Swing++ & 1) == 1 ? b.NearestHostile(p.X, p.Z, 11, e => e.Elite || e.Boss) : null;
            var t = big ?? b.DensestHostile(p.X, p.Z, 11, r);
            if (t == null) return false;
            x = t.X; z = t.Z;
        }"""),
])

edit('logic/Sim/Battle.cs', [
("""        if (o.Summon) dmg *= st.Get(Stat.SummonDamage);""",
"""        // Allies go for the throat: champions and worse take more from them.
        if (o.Summon) dmg *= st.Get(Stat.SummonDamage) * (e.Boss || e.Elite ? 1.6 : 1);"""),
])

edit('logic/Content/Paths.cs', [
("""            Passives = ["duplicity", "precision", "ferocity", "velocity", "haste", "serration", "fortune"],""",
"""            Passives = ["duplicity", "precision", "ferocity", "velocity", "haste", "serration", "fortune", "evasion"],"""),
("""            Passives = ["emberblood", "expanse", "perennial", "haste", "venom", "might", "searing"],""",
"""            Passives = ["emberblood", "expanse", "perennial", "haste", "venom", "might", "searing", "vitality", "warding"],"""),
("""            Passives = ["conduit", "precision", "haste", "expanse", "duplicity"],""",
"""            Passives = ["conduit", "precision", "haste", "expanse", "duplicity", "vitality"],"""),
("""            Passives = ["duplicity", "haste", "precision", "wisdom", "fortune", "greed"],""",
"""            Passives = ["duplicity", "haste", "precision", "wisdom", "fortune", "greed", "recovery", "warding"],"""),
])
print('ok')
