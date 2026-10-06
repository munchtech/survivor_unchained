import os, re
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/LevelUp.cs', [
("""        int Open() => System.Math.Max(0, count - offers.Count);
        void Add(Cand? c)
        {
            if (c == null) return;
            offers.Add(c.O);
            combat.Remove(c);
            passive.Remove(c);
        }""", """        int Open() => System.Math.Max(0, count - offers.Count);
        // What a guarantee put there stays there (the last guarantee does not swap it out).
        var kept = new HashSet<Offer>(offers);
        void Add(Cand? c)
        {
            if (c == null) return;
            offers.Add(c.O);
            kept.Add(c.O);
            combat.Remove(c);
            passive.Remove(c);
        }"""),
("""        var both = combat.Concat(passive).ToList();
        while (Open() > 0 && TakeFrom(b, both) is { } c) Add(c);""", """        var both = combat.Concat(passive).ToList();
        while (Open() > 0 && TakeFrom(b, both) is { } c) { offers.Add(c.O); combat.Remove(c); passive.Remove(c); }"""),
("""            int swap = offers.FindLastIndex(o => o.Kind != OfferKind.Evolve && !waiting.Any(w => IsCatalyst(o, w)) && !(young && o.Kind == OfferKind.Weapon && offers.Count(x => x.Kind == OfferKind.Weapon) == 1));""",
"""            int swap = offers.FindLastIndex(o => !kept.Contains(o));"""),
])

# Allies that a skill raised carry its champion multiplier; all allies go for the throat harder.
edit('logic/Sim/Battle.cs', [
("""        if (o.Summon) dmg *= st.Get(Stat.SummonDamage) * (e.Boss || e.Elite ? 1.6 : 1);""",
"""        if (o.Summon) dmg *= st.Get(Stat.SummonDamage) * (e.Boss || e.Elite ? 2.0 : 1);"""),
])
edit('logic/Sim/Ai.cs', [
("""Credit = e.SummonedBy ?? e.Def.Id });""",
"""Credit = e.SummonedBy ?? e.Def.Id,
                BossDamage = e.SummonedBy != null && Content.Weapons.All.TryGetValue(e.SummonedBy, out var by) ? by.BossDamage : null });"""),
])

p = 'logic/Content/Weapons.cs'
s = open(p, encoding='utf-8').read()
for w, v in [('seeking_motes', 1.1), ('gravecall', 1.6)]:
    pat = r'(Id = "%s", Name = "[^"]*", School = [^\n]*\n[^\n]*\n            Art = "[^"]*", BossDamage = )([\d.]+)' % w
    assert len(re.findall(pat, s)) == 1, w
    s = re.sub(pat, lambda m: m.group(1) + str(v), s)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
