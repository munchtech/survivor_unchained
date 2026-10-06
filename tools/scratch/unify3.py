import os, re
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')
p = 'tests/BalanceLab.cs'
s = open(p, encoding='utf-8').read()

# Header comment: one tool.
old = """///   LAB_BOT       'plain' (default: the arena bot as it was) or 'deft' (it also dodges
///                 lunges and pots and closes on the throwers: nearer a player who knows the game)"""
new = """///   LAB_BOT       'plain' (default) or 'deft' (it also dodges lunges and pots and closes
///                 on the throwers: nearer a player who knows the game)
///   LAB_POLICY    how cards are chosen (default 'first'; or greedy, random, path:ID, paths)
///
/// The arena half is the balance harness (godot/balance: the same arenas, hands,
/// drafting policies and report as `Balance.dll arena`), so there is one tool; the
/// day-story half walks the Verge with StoryPlay."""
assert s.count(old) == 1
s = s.replace(old, new)

# The arena: the harness's runs and report in place of the lab's own.
i = s.index('    sealed record Row(ArenaPlay.Case Case, ArenaPlay.Result R)')
j = s.index('    static List<T> RunAll<T, TCase>(')
s = s[:i] + s[j:]
i = s.index('    void Arena(string dir, StringBuilder sum)')
j = s.index('    /* ------------------------------------------------------- the day story -- */')
arena = '''    void Arena(string dir, StringBuilder sum)
    {
        var callings = List("LAB_CALLINGS", "warden,reaver,arcanist,stalker");
        var tiers = List("LAB_TIERS", "1,2,3").Select(int.Parse).ToArray();
        var peoples = List("LAB_PEOPLES", "pack,dead,lamplings,kerchiefs");
        var oathList = List("LAB_OATHS", "none");
        if (oathList is ["all"]) oathList = new[] { "none" }.Concat(MapOffers.Oaths.Select(o => o.Id)).ToArray();
        var policies = List("LAB_POLICY", "first").SelectMany(x => x == "paths" ? Content.Paths.All.Select(q => $"path:{q.Id}") : [x]).ToArray();
        int seeds = int.Parse(Env("LAB_SEEDS", "4")), seed0 = int.Parse(Env("LAB_SEED0", "1000"));
        string level = Env("LAB_LEVEL", "tier");
        double minutes = double.Parse(Env("LAB_MINUTES", "45"), Inv);
        bool deft = Env("LAB_BOT", "plain") == "deft";
        var specs = new List<RunSpec>();
        foreach (var c in callings)
        {
            int weapons = Rpg.Callings.Archetype(c).Weapons.Count;
            foreach (var policy in policies)
                foreach (int tier in tiers)
                    foreach (var people in peoples)
                        foreach (var oath in oathList)
                            for (int s = 0; s < seeds; s++)
                                specs.Add(new RunSpec(seed0 + s * 7919 + tier * 31 + Array.FindIndex(MapOffers.Peoples, d => d.Id == people) * 3, c, policy, tier, people,
                                    oath == "none" ? null : oath.Split('+'), Cap: minutes, Beyond: Math.Max(0, minutes - 30), Weapon: s % weapons, Art: s / weapons % 2,
                                    Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft));
        }
        // Everything the runs touch read in once, before the threads share it.
        ArenaSim.Play(specs[0] with { Cap = 0.05 });
        var runs = RunAll(specs, ArenaSim.Play, dir, "arena", log);
        Report.Csv(runs, dir);
        sum.AppendLine(Report.Arena(runs));
    }

    static string Q(string s) => s.Contains(',') || s.Contains('"') ? $"\\"{s.Replace("\\"", "\\"\\"")}\\"" : s;

    static double Median(IEnumerable<double> xs)
    {
        var a = xs.OrderBy(x => x).ToArray();
        return a.Length == 0 ? double.NaN : a.Length % 2 == 1 ? a[a.Length / 2] : (a[a.Length / 2 - 1] + a[a.Length / 2]) / 2;
    }

    static string Pct(int k, int n) => n == 0 ? "-" : $"{100.0 * k / n:0}%";
    static string M(double v, string f = "0.0") => double.IsNaN(v) ? "-" : F(v, f);

'''
s = s[:i] + arena + s[j:]
s = s.replace('using SurvivorUnchained.Maps;', 'using SurvivorUnchained.Balance;\nusing SurvivorUnchained.Maps;')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
