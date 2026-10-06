import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

R = 'balance/Harness/Report.cs'
edit(R, [
("""        Summary(sb, "people", runs.GroupBy(r => r.Spec.People));""",
"""        Summary(sb, "people", runs.GroupBy(r => r.Spec.People));
        if (runs.Select(r => r.Spec.Tier).Distinct().Count() > 1) Summary(sb, "tier", runs.GroupBy(r => $"tier {r.Spec.Tier}"));
        if (runs.Select(r => Oath(r)).Distinct().Count() > 1) Summary(sb, "oath", runs.GroupBy(Oath));
        if (runs.Select(r => r.Spec.Level).Distinct().Count() > 1) Summary(sb, "level", runs.GroupBy(r => $"level {r.Spec.Level}"));

        // How the losses come: before the boss, by five minutes; to the boss, with what was left of it.
        var lost = runs.Where(r => r.Died && !r.Won).ToList();
        if (lost.Count > 0)
        {
            sb.AppendLine("### When the losses come\\n");
            var tiers = runs.Select(r => r.Spec.Tier).Distinct().OrderBy(t => t).ToList();
            Head(sb, ["minutes", .. tiers.Select(t => $"tier {t}")]);
            for (int b5 = 0; b5 < 7; b5++)
                Row(sb, [b5 < 6 ? $"{b5 * 5}-{b5 * 5 + 5}" : "the boss", .. tiers.Select(t => (object)lost.Count(r => r.Spec.Tier == t && (r.BossLeft >= 0 ? 6 : (int)Math.Min(5, r.Minutes / 5)) == b5))]);
            var toBoss = lost.Where(r => r.BossLeft >= 0).ToList();
            if (toBoss.Count > 0) sb.AppendLine($"\\nFell to the boss: {toBoss.Count}, with a median {Pct(Median(toBoss.Select(r => r.BossLeft)))} of it left.");
            sb.AppendLine();
        }"""),
# The cards, compared fairly: runs that took one by the fifteenth minute against runs that had not.
("""        sb.AppendLine("### Cards (offered, taken, and the win rate of the runs that took one)\\n");
        Head(sb, "card", "offered", "taken", "pick", "won taking", "won not", "delta", "lived taking (min)");""",
"""        // Runs that took a card by the fifteenth minute against those that had not (nearly
        // every run lives that long, so long runs, which take more cards, do not flatter it).
        sb.AppendLine("### Cards (offered, taken, and how the runs that took one by minute 15 went)\\n");
        Head(sb, "card", "offered", "taken", "pick", "won, taken by 15", "won, not by 15", "delta", "first taken (min)");"""),
("""            var took = runs.Where(r => r.Taken.ContainsKey(k)).ToList();
            var not = runs.Where(r => !r.Taken.ContainsKey(k)).ToList();
            double wt = Rate(took, r => r.Won), wn = Rate(not, r => r.Won);
            rowsOut.Add((k, wt - wn, [k, offered.ToString(), taken.ToString(), Pct(offered == 0 ? double.NaN : taken / (double)offered), Pct(wt), Pct(wn), F((wt - wn) * 100, "+0;-0;0"), F(Median(took.Select(r => r.Minutes)))]));""",
"""            var took = runs.Where(r => r.Picks.Any(p => p.Card == k && p.Minute < 15)).ToList();
            var not = runs.Where(r => r.Picks.All(p => p.Card != k || p.Minute >= 15)).ToList();
            double wt = Rate(took, r => r.Won), wn = Rate(not, r => r.Won);
            var first = runs.Select(r => r.Picks.FirstOrDefault(p => p.Card == k)).Where(p => p.Card != null).Select(p => p.Minute);
            rowsOut.Add((k, wt - wn, [k, offered.ToString(), taken.ToString(), Pct(offered == 0 ? double.NaN : taken / (double)offered), Pct(wt), Pct(wn), F((wt - wn) * 100, "+0;-0;0"), F(Median(first))]));"""),
("""    public static string Probes(List<ProbeResult> probes)""",
"""    static string Oath(RunResult r) => r.Spec.Oaths is { Length: > 0 } o ? string.Join("+", o) : "none";

    static string Q(string s) => s.Contains(',') || s.Contains('"') ? $"\\"{s.Replace("\\"", "\\"\\"")}\\"" : s;

    /// <summary>The runs as CSV (the balance lab's columns, for a spreadsheet): one row a run,
    /// and one a card taken.</summary>
    public static void Csv(List<RunResult> runs, string dir)
    {
        System.IO.Directory.CreateDirectory(dir);
        var o = new StringBuilder("run,key,policy,bot,seed,calling,weapon,art,tier,people,oath,level,won,win_min,died,minutes,killer,kills,ember,cards,low_hp,boss_ttk,boss_left,quaffs,greats,ember_curve,alive_curve,hp_curve,build\\n");
        var cards = new StringBuilder("run,calling,tier,people,won,minutes,card,minute\\n");
        for (int i = 0; i < runs.Count; i++)
        {
            var r = runs[i];
            var s = r.Spec;
            o.AppendLine(string.Join(",", new[]
            {
                i.ToString(), Q(s.Key), s.Policy, s.Deft ? "deft" : "plain", s.Seed.ToString(), s.Calling, s.Weapon.ToString(), s.Art.ToString(), s.Tier.ToString(), s.People, Oath(r), s.Level.ToString(),
                r.Won ? "1" : "0", r.WonAt is double w ? F(w, "0.00") : "", r.Died ? "1" : "0", F(r.Minutes, "0.00"), r.KilledBy, r.Kills.ToString(), r.Ember.ToString(), r.Cards.ToString(),
                F(r.LowHp, "0.000"), r.BossTtk is double bt ? F(bt, "0.0") : "", r.BossLeft < 0 ? "" : F(r.BossLeft, "0.000"), r.Quaffs.ToString(), Q(string.Join(" ", r.Greats)),
                Q(string.Join(" ", r.ByMinute.Select(m => m.Ember))), Q(string.Join(" ", r.ByMinute.Select(m => m.Alive))), Q(string.Join(" ", r.ByMinute.Select(m => F(m.LowHp, "0.00")))), Q(r.Build),
            }));
            foreach (var p in r.Picks) cards.AppendLine($"{i},{s.Calling},{s.Tier},{s.People},{(r.Won ? 1 : 0)},{F(r.Minutes, "0.00")},{p.Card},{F(p.Minute, "0.00")}");
        }
        System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "arena_runs.csv"), o.ToString());
        System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "arena_cards.csv"), cards.ToString());
    }

    public static string Probes(List<ProbeResult> probes)"""),
])

PR = 'balance/Program.cs'
edit(PR, [
("""    var peoples = opt.List("people", "all") is ["all"] ? MapOffers.Peoples.Select(p => p.Id).ToArray() : opt.List("people", "all");
    int seeds = opt.Int("seeds", 4), seed0 = opt.Int("seed0", 1), tier = opt.Int("tier", 1);
    bool allWeapons = opt.Get("weapons", "") == "all";
    var specs = new List<RunSpec>();
    foreach (var c in Callers())
        foreach (var pol in Policies())
            for (int s = 0; s < seeds; s++)
            {
                int nw = allWeapons ? Callings.Archetype(c).Weapons.Count : 1;
                for (int w = 0; w < nw; w++)
                    specs.Add(new RunSpec(seed0 + s, c, pol, tier, peoples[(s + w) % peoples.Length], null, opt.Double("cap", 40), opt.Double("beyond", 0), allWeapons ? w : s % Callings.Archetype(c).Weapons.Count));
            }""",
"""    var peoples = opt.List("people", "all") is ["all"] ? MapOffers.Peoples.Select(p => p.Id).ToArray() : opt.List("people", "all");
    int seeds = opt.Int("seeds", 4), seed0 = opt.Int("seed0", 1);
    var tiers = opt.Has("tiers") ? opt.List("tiers", "1").Select(int.Parse).ToArray() : [opt.Int("tier", 1)];
    // --oaths none|all|a,b+c: unsworn, each oath alone, or the ones named ('+' swears two at once).
    var oaths = opt.List("oaths", "none") is ["all"] ? new[] { "none" }.Concat(MapOffers.Oaths.Select(o => o.Id)).ToArray() : opt.List("oaths", "none");
    // --level N|tier: the survivor's character level (tier: 1, 4, 7 by tier, as the story's pace has it).
    string level = opt.Get("level", "1");
    bool deft = opt.Get("bot", "plain") == "deft";
    bool allWeapons = opt.Get("weapons", "") == "all";
    var specs = new List<RunSpec>();
    foreach (var c in Callers())
        foreach (var pol in Policies())
            foreach (int tier in tiers)
                foreach (var oath in oaths)
                    for (int s = 0; s < seeds; s++)
                    {
                        int nw = allWeapons ? Callings.Archetype(c).Weapons.Count : 1;
                        for (int w = 0; w < nw; w++)
                            specs.Add(new RunSpec(seed0 + s, c, pol, tier, peoples[(s + w) % peoples.Length], oath == "none" ? null : oath.Split('+'),
                                opt.Double("cap", 40), opt.Double("beyond", 0), allWeapons ? w : s % Callings.Archetype(c).Weapons.Count,
                                Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft));
                    }"""),
("""    var md = Report.Arena(results.ToList());
    File.WriteAllText(Path.ChangeExtension(outPath, ".md"), md);""",
"""    var md = Report.Arena(results.OrderBy(r => r.Spec.Key).ToList());
    File.WriteAllText(Path.ChangeExtension(outPath, ".md"), md);
    if (opt.Has("csv")) Report.Csv(results.OrderBy(r => r.Spec.Key).ToList(), opt.Get("csv", "out/csv"));"""),
(""" * Options: --callings warden,reaver|all  --policies greedy,random,path:steel|paths
 *          --seeds N  --seed0 S  --tier T  --people pack,dead|all  --cap MIN
 *          --beyond MIN  --weapons all  --levels 20,40  --par N  --out PATH */""",
""" * Options: --callings warden,reaver|all  --policies greedy,random,path:steel|paths
 *          --seeds N  --seed0 S  --tier T (or --tiers 1,2,3)  --people pack,dead|all
 *          --oaths none|all|a,b+c  --level N|tier  --bot plain|deft  --cap MIN
 *          --beyond MIN  --weapons all  --levels 20,40  --par N  --out PATH  --csv DIR
 *
 * This is the one balance tool: the balance lab's sweep (godot/tests/BalanceLab.cs,
 * BALANCE_LAB=arena) runs these same arenas through these same hands. */"""),
])
print('ok')
