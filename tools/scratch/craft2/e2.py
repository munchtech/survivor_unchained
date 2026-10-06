from ed import sub
sub('tests/CraftingEconomy.cs', [
("""/// Act 1's crafting economy played forward day by day (docs/CRAFTING_DESIGN.md 13.3–13.4):
/// the measured faucets, a survivor who crafts on what they wear with the real forge (quotes,
/// heat, terms), and the design's targets. The faucets, per won night, are the combat lead's
/// sweep at 71608a4 (deft bot, fodder gold at 2%, gear only from carriers): ember at the end,
/// champions, gold by people (the Kerchiefs' at the day's champion rate, scaled by what an arena
/// really sets, MapRules.ChampionGold); the gear is the arena's own drop rule (ArenaRun.OnLoot, about 20""",
"""/// Act 1's crafting economy played forward day by day (docs/CRAFTING_DESIGN.md 13.3–13.4):
/// the measured faucets, a survivor who crafts on what they wear with the real forge (quotes,
/// heat, terms), and the design's targets. The faucets, per won night, are the combat lead's
/// sweep at 71608a4 (deft bot, gear only from carriers): ember at the end and champions; the gold
/// by people is CraftingProbe's at 4c32586 (arena fodder at 0.15% of the day's gold, champions at
/// 7%, bosses and minibosses in full); the gear is the arena's own drop rule (ArenaRun.OnLoot, about 20"""),
("""    static readonly int[] Ember = [57, 62, 67], Champs = [864, 1052, 1079], KerchiefGold = [526, 542, 689], OtherGold = [11, 22, 16];""",
"""    static readonly int[] Ember = [57, 62, 67], Champs = [864, 1052, 1079], KerchiefGold = [375, 351, 365], OtherGold = [15, 12, 16];"""),
("""        const int days = 10;
        // What an arena's champions pay, from a real arena's rules (combat's line, 7f04b40).
        double champion = ArenaTests.Make(ArenaTests.Spec("kerchiefs")).B.Rules.ChampionGold;
        Assert.InRange(champion, 0.05, 0.15);
        var day = Enumerable.Range(0, 8).Select(s => Play(days, KerchiefGold, (uint)(101 + s * 7), s % 2 == 0)).ToList();
        var cut = Enumerable.Range(0, 8).Select(s => Play(days, KerchiefGold, (uint)(101 + s * 7), s % 2 == 0)).ToList();
        foreach (int kg in new[] { 350, 400, 450, 500, 550, 600 })
            Report($"kerchief night {kg}", Enumerable.Range(0, 8).Select(s => Play(days, [kg, kg, kg], (uint)(101 + s * 7), s % 2 == 0)).ToList());""",
"""        const int days = 10;
        // The gold measured above holds only while an arena keeps the rates it was measured at
        // (combat's lines in ArenaRun.Begin): re-run CraftingProbe if they move.
        var rules = ArenaTests.Make(ArenaTests.Spec("kerchiefs")).B.Rules;
        Assert.Equal(0.07, rules.ChampionGold, 6);
        Assert.Equal(0.0015, rules.FodderGold, 6);
        var runs = Enumerable.Range(0, 8).Select(s => Play(days, KerchiefGold, (uint)(101 + s * 7), s % 2 == 0)).ToList();
        // What the old rates paid a Kerchief night (champions in full, fodder at 2%), for comparison.
        var before = Enumerable.Range(0, 8).Select(s => Play(days, [2570, 3320, 2796], (uint)(101 + s * 7), s % 2 == 0)).ToList();"""),
("""        Report("champions at the day's gold (before the cut)", day);
        Report($"champions at {champion:0%} of it (an arena's rule)", cut);
        log.WriteLine(cut[0].Log);

        // The targets (design 13.3), on what an arena pays: its champions drop a tenth of the day's
        // gold (at the day's rate a Kerchief night paid 2.5k-3.3k, which bought the whole forge in a
        // night). The first craft on day 1 or 2; the starting weapon rare""",
"""        Report("before the arena's gold was cut", before);
        Report("an arena's gold today", runs);
        log.WriteLine(runs[0].Log);

        // The targets (design 13.3), on what an arena pays now (a Kerchief night about 350-375 gold;
        // at the old rates it paid 2.5k-3.3k, which bought the whole forge in a night). The first
        // craft on day 1 or 2; the starting weapon rare"""),
])
