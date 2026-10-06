import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('tests/BattleTests.cs', [
("""                    b.SpawnEnemy(def, b.Player.X + Math.Cos(a) * 14, b.Player.Z + Math.Sin(a) * 14,
                        new Battle.SpawnOpts { Level = 1 + (int)Math.Floor(t / 30), Style = SpawnStyle.Rise });""",
"""                    // The horde's level rises as an arena's does: every two and a half minutes.
                    b.SpawnEnemy(def, b.Player.X + Math.Cos(a) * 14, b.Player.Z + Math.Sin(a) * 14,
                        new Battle.SpawnOpts { Level = 1 + (int)Math.Floor(t / 150), Style = SpawnStyle.Rise });"""),
("""        Assert.All(offers, o => Assert.True((o.Kind == OfferKind.Boon && !o.Blessing) || o.Kind == OfferKind.Hone));
        Assert.Equal(3, offers.Count);""", """        // Passives and honing; and a union where two of them belong together (it comes first).
        Assert.All(offers, o => Assert.True((o.Kind == OfferKind.Boon && !o.Blessing) || o.Kind is OfferKind.Hone or OfferKind.Union));
        Assert.Equal(3, offers.Count);"""),
])

edit('tests/BlessingTests.cs', [
("""        Assert.Equal(4, Boons.Milestones[0]);
        Assert.True(Boons.IsMilestone(4));
        Assert.False(Boons.IsMilestone(5));""", """        Assert.Equal(5, Boons.Milestones[0]);
        Assert.True(Boons.IsMilestone(5));
        Assert.False(Boons.IsMilestone(6));"""),
("""        var b = BattleTests.Arena(4);
        for (int i = 0; i < 3; i++) b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
        Assert.Equal(4, b.EmberLevel);
        Assert.Equal(new[] { 4 }, b.PendingBlessings);""", """        var b = BattleTests.Arena(4);
        for (int i = 0; i < 4; i++) b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
        Assert.Equal(5, b.EmberLevel);
        Assert.Equal(new[] { 5 }, b.PendingBlessings);"""),
])

edit('tests/ArenaTests.cs', [
("""        Assert.Contains("might", s.J.Ch.Discovered);""", """        // Only combat skills are discovered (only they can be learned by day).
        Assert.DoesNotContain("might", s.J.Ch.Discovered);"""),
])
print('ok')
