import os, re
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Paths.cs', [
("""            Passives = ["might", "ferocity", "serration", "ironhide", "haste", "fleetfoot", "evasion", "thorns", "venom"],""",
"""            Passives = ["might", "ferocity", "serration", "ironhide", "haste", "fleetfoot", "evasion", "thorns", "venom", "conduit"],"""),
])

edit('logic/Sim/LevelUp.cs', [
# Banished means never again: no ranks, no honing either.
("""        foreach (var w in b.Weapons)
        {
            if (w.Rank >= Content.Weapons.MaxRank)
            {""", """        foreach (var w in b.Weapons)
        {
            if (b.BannedCards.Contains(w.Id)) continue;
            if (w.Rank >= Content.Weapons.MaxRank)
            {"""),
# A rare passive cannot go missing for long: a hard floor under the weighted pity.
("""        // A weapon ready to evolve does not wait more than CatalystPity drafts for its passive.""",
"""        // A rare passive does not go missing for more than RareFloor drafts.
        if (Open() > 0 && mem.RarePity >= RareFloor && !offers.Any(o => o.Kind == OfferKind.Boon && o.Rarity >= Rarity.Rare))
            Add(TakeFrom(b, passive, c => c.O.Rarity >= Rarity.Rare));
        // A weapon ready to evolve does not wait more than CatalystPity drafts for its passive."""),
("""    /// <summary>Drafts a weapon ready to evolve may wait for its passive.</summary>
    public const int CatalystPity = 2;""", """    /// <summary>Drafts a weapon ready to evolve may wait for its passive.</summary>
    public const int CatalystPity = 2;
    /// <summary>Skill drafts a rare passive may go missing for (the weight rises long before).</summary>
    public const int RareFloor = 10;"""),
("""            (r >= Rarity.Rare ? System.Math.Min(3, 1 + 0.2 * mem.RarePity) : 1);""",
"""            (r >= Rarity.Rare ? System.Math.Min(4, 1 + 0.3 * mem.RarePity) : 1);"""),
])

# Banishing a carried skill's rank: the drafted ones may still be checked by the test.
edit('tests/OfferTests.cs', [
("""        Assert.True(longest <= 12, $"{longest} drafts without a rare passive");""",
"""        Assert.True(longest <= LevelUp.RareFloor, $"{longest} drafts without a rare passive");"""),
("""        double Share(bool walking)
        {
            int on = 0, all = 0;
            for (uint seed = 1; seed <= 200; seed++)
            {
                // Two of the Pyre's own (or two of nobody's in particular) carried.
                var b = walking ? BattleTests.Arena(seed, ("cinderfall", 2), ("firepot", 2)) : BattleTests.Arena(seed, ("gale_chakram", 2), ("arcweb", 2));
                Owe(b);
                foreach (var o in LevelUp.Draft(b).Where(o => o.Kind == OfferKind.Weapon))
                {
                    all++;
                    if (Paths.Find("pyre")!.Weapons.Contains(o.Id)) on++;
                }
            }
            return (double)on / all;
        }""", """        // How often the Pyre's other skills (carried by neither build) are offered.
        string[] rest = ["hallowed_ring", "thunderhead", "verdant_lance"];
        double Share(bool walking)
        {
            int on = 0, all = 0;
            for (uint seed = 1; seed <= 300; seed++)
            {
                // Two of the Pyre's own (or two of nobody's in particular) carried.
                var b = walking ? BattleTests.Arena(seed, ("cinderfall", 2), ("firepot", 2)) : BattleTests.Arena(seed, ("gale_chakram", 2), ("arcweb", 2));
                Owe(b);
                foreach (var o in LevelUp.Draft(b).Where(o => o.Kind == OfferKind.Weapon))
                {
                    all++;
                    if (rest.Contains(o.Id)) on++;
                }
            }
            return (double)on / all;
        }"""),
])

# The Weave's single-target edge: the chain's and the motes' champion multipliers.
p = 'logic/Content/Weapons.cs'
s = open(p, encoding='utf-8').read()
for w, v in [('arcweb', 2.4), ('seeking_motes', 1.3)]:
    pat = r'(Id = "%s", Name = "[^"]*", School = [^\n]*\n[^\n]*\n            Art = "[^"]*", BossDamage = )([\d.]+)' % w
    assert len(re.findall(pat, s)) == 1, w
    s = re.sub(pat, lambda m: m.group(1) + str(v), s)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
