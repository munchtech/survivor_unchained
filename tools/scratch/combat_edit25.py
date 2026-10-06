W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''     *   the horde    hardens by the minute (Hardening): smoothly, with no cliff,
     *                for the first three quarters of an hour past the half hour,
     *                where a great build has its hour; then compounding, so no
     *                build, however broken, holds for ever. A little quicker too,
     *                to a ceiling (pace a player can still read).''',
'''     *   the horde    hardens by the minute (Hardening): smoothly, with no cliff,
     *                for the first hour past the half hour, where a great build
     *                has its hour; then compounding, so no build, however
     *                broken, holds for ever. A little quicker too, to a low
     *                ceiling (pace a player can still read and outrun).'''),
('''    /// <summary>The order the dark swears the table's oaths: a verb, then a number, then a
    /// verb, so each five minutes asks something new (the table's own are passed over).</summary>
    static readonly string[] DarkDeck = ["hunt", "embers", "champions", "winter", "vigil", "ruin", "iron", "blight", "swarm", "deep"];''',
'''    /// <summary>The order the dark swears the table's oaths (the table's own are passed over):
    /// first the questions of where to stand, read on the ground (burning dead, champions,
    /// bursting dead, the horde's turns twice as often); then pace and number (the hunt,
    /// the swarm); last those that grind (the winter's crawl, iron skin, the blight's
    /// poison and cut mending, levels). An early winter or iron walled the sweep's runs.</summary>
    static readonly string[] DarkDeck = ["embers", "champions", "ruin", "vigil", "hunt", "swarm", "winter", "iron", "blight", "deep"];'''),
('''        // Compounding from three quarters of an hour past: a fortieth a minute.
        double press = m > 45 ? Math.Pow(1.025, m - 45) : 1;
        return ((1 + 0.1 * m + 0.006 * m * m) * press, (1 + 0.035 * m) * press, 1 + Math.Min(0.3, 0.005 * m));''',
'''        // Compounding from an hour past: three hundredths a minute, so by two hours past
        // nothing stands (measured: docs/team/combat.md).
        double press = m > 60 ? Math.Pow(1.03, m - 60) : 1;
        return ((1 + 0.1 * m + 0.006 * m * m) * press, (1 + 0.035 * m) * press, 1 + Math.Min(0.15, 0.004 * m));'''),
])
edit(r'tests\ArenaTests.cs', [
('''            Assert.True(h.Pace <= 1.3);''', '''            Assert.True(h.Pace <= 1.15);'''),
('''        Assert.Contains("The dark swears the Oath of the Hunt", sworn);''', '''        Assert.Contains("The dark swears the Oath of Embers", sworn);'''),
])
print("ok")
