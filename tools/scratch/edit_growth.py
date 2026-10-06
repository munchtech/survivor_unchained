import os, re
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Weapons.cs', [
("""    /// <summary>Offered in the level-up pool (and so discoverable, and learnable by day).</summary>
    public bool Findable;""", """    /// <summary>Offered in the level-up pool (and so discoverable, and learnable by day).</summary>
    public bool Findable;
    /// <summary>Damage each rank adds (of the base). A single bolt grows more
    /// with its ranks than a field that already strikes a crowd does.</summary>
    public double Growth = Weapons.DamageStep;"""),
])

edit('logic/Sim/Weapons.cs', [
("""            double d = (Def.Base.Damage ?? 0) * (1 + Content.Weapons.DamageStep * (Rank - 1)) * Mods.Damage;""",
"""            double d = (Def.Base.Damage ?? 0) * (1 + Def.Growth * (Rank - 1)) * Mods.Damage;"""),
])

edit('logic/Sim/LevelUp.cs', [
("""                Text = $"+{Content.Weapons.DamageStep * 100:0}% damage (+{(next - 1) * Content.Weapons.DamageStep * 100:0}% in all).{extra}{hint}",""",
"""                Text = $"+{w.Def.Growth * 100:0}% damage (+{(next - 1) * w.Def.Growth * 100:0}% in all).{extra}{hint}","""),
])

# Per-skill growth: bolts and arrows grow faster, fields and rings slower.
growth = {
    'arcweb': 0.3, 'seeking_motes': 0.3, 'volley': 0.28, 'knifestorm': 0.26, 'rimeshard': 0.28, 'umbral_bolt': 0.26,
    'moonbrand': 0.26, 'grave_tether': 0.26, 'judgement_disc': 0.18,
    'dawnpulse': 0.16, 'hallowed_ring': 0.16, 'axe_gyre': 0.17, 'blightfield': 0.18, 'thornbloom': 0.18, 'iron_palms': 0.18,
}
p = 'logic/Content/Weapons.cs'
s = open(p, encoding='utf-8').read()
for w, g in growth.items():
    pat = r'(Id = "%s", Name = "[^"]*", School = [^\n]*\n[^\n]*\n            Art = "[^"]*"(?:, BossDamage = [\d.]+)?, Findable = true)' % w
    n = len(re.findall(pat, s))
    assert n == 1, (w, n)
    s = re.sub(pat, lambda m: m.group(1) + f', Growth = {g}', s)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
