import os, re
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

# Paths: each union is its path's crowning capstone, and its weapon is the path's own.
p = 'logic/Content/Paths.cs'
s = open(p, encoding='utf-8').read()
unions = {'steel': ['butchers_wheel'], 'hunt': ['hail_of_steel'], 'pyre': ['frostfire_comet'], 'rime': ['frostfire_comet'],
          'storm': ['the_tempest'], 'dawn': ['dawns_judgement'], 'grave': ['soul_lantern'], 'wild': ['rotwood'],
          'host': ['barrow_host'], 'weave': ['starfall']}
for path, us in unions.items():
    m = re.search(r'(new\(\) \{ Id = "%s".*?Weapons = \[)([^\]]*)(\].*?Capstones = \[)([^\]]*)(\])' % path, s, re.S)
    assert m, path
    extra = ', '.join(f'"{u}"' for u in us)
    s = s[:m.start()] + m.group(1) + m.group(2) + ', ' + extra + m.group(3) + m.group(4) + ', ' + extra + m.group(5) + s[m.end():]
s = s.replace(""" * Every combat skill belongs to at least one path, every passive skill and
 * blessing serves at least two builds, and every path has its own capstone
 * evolutions. */""", """ * Every combat skill belongs to at least one path, every passive skill and
 * blessing serves at least two builds, and every path has its own capstone
 * evolutions and a union of its own (Content/Unions.cs) to crown it. */""")
open(p, 'w', encoding='utf-8').write(s)

# The milestones, retimed to the slower ember: between the great blessings, not on them.
edit('logic/Content/Boons.cs', [
("""    /// <summary>The ember levels that bring a blessing: the first a minute or
    /// two in, then further apart (4, 10, 18, 28, 40 ...).</summary>
    public static readonly int[] Milestones = MakeMilestones();

    static int[] MakeMilestones()
    {
        var o = new List<int>();
        for (int l = 4, gap = 6; l < 400; l += gap, gap += 2) o.Add(l);
        return o.ToArray();
    }""", """    /// <summary>The ember levels that bring a blessing: the first a minute in,
    /// then further apart (5, 12, 21, 32, 45, 60 ...): at the ember's pace,
    /// about the first, fifth, tenth, twentieth and twenty-eighth minutes,
    /// between the great blessings rather than on them.</summary>
    public static readonly int[] Milestones = MakeMilestones();

    static int[] MakeMilestones()
    {
        var o = new List<int>();
        for (int l = 5, gap = 7; l < 400; l += gap, gap += 2) o.Add(l);
        return o.ToArray();
    }"""),
])

# Arenas: discoveries are combat skills only; evolutions and unions go in the codex; a tome is a choice.
edit('logic/Arena/Arena.cs', [
("""public sealed record ArenaResult(ArenaSpec Spec, bool Won, double Seconds, int Kills, int EmberLevel, double Xp, double Gold,
    List<string> Discovered, int LevelsGained, bool Longest = false, string? Tome = null, string? Taught = null);""",
"""public sealed record ArenaResult(ArenaSpec Spec, bool Won, double Seconds, int Kills, int EmberLevel, double Xp, double Gold,
    List<string> Discovered, int LevelsGained, bool Longest = false, string? Tome = null, string? Taught = null)
{
    /// <summary>What a tome won here may be inscribed with (the player chooses
    /// one: Arenas.Inscribe); empty if none was won.</summary>
    public List<string> TomeChoices { get; init; } = new();
    /// <summary>Evolutions and unions made here for the first time (now in the codex).</summary>
    public List<string> Recorded { get; init; } = new();
}"""),
("""    /// <summary>The skills a run discovered: every combat skill carried at the
    /// end (and what it evolved from), every passive taken.</summary>
    public static IEnumerable<string> Skills(Battle b) =>
        b.Weapons.Select(w => w.Id).Concat(b.Boons.Keys.Where(k => Content.Boons.All.TryGetValue(k, out var d) && d.Kind == Content.BoonKind.Passive));""",
"""    /// <summary>The skills a run discovered: every combat skill carried at the
    /// end (evolved or not), and the halves of any union made. Only combat
    /// skills can be learned by day, so only they are discovered.</summary>
    public static IEnumerable<string> Skills(Battle b) =>
        b.Weapons.SelectMany(w => Content.Unions.All.FirstOrDefault(u => u.Into == w.Id) is { } un ? new[] { un.A, un.B } : new[] { w.Id })
            .Where(id => Content.Weapons.All.TryGetValue(id, out var d) && d.Findable).Distinct();

    /// <summary>What the fight made that the codex keeps: its evolutions
    /// (evo:id) and unions (union:id), each with its recipe for the book.</summary>
    public static IEnumerable<string> Made(Battle b) =>
        b.Weapons.Select(w => w.Evolution is { } e ? $"evo:{e.Id}" : Content.Unions.All.FirstOrDefault(u => u.Into == w.Id) is { } un ? $"union:{un.Id}" : null)
            .Where(x => x != null).Select(x => x!);

    /// <summary>Write a tome won in an arena with one of its choices: the tome
    /// goes into the pack, ready to be read. False if it was not one of them.</summary>
    public static bool Inscribe(Journey j, ArenaResult r, string id) =>
        r.TomeChoices.Contains(id) && j.GiveItem(SkillBook.Tome(id), 1);"""),
("""        // A story fight won gives a tome of something found in it (a table's, now and then).
        string? tome = null;
        if (won && (spec.Story || b.Rng.Next() < 0.35))
        {
            var learnable = Skills(b).Where(id => SkillBook.CanLearn(ch, id)).ToList();
            if (learnable.Count > 0)
            {
                tome = learnable[(int)(b.Rng.Next() * learnable.Count)];
                j.GiveItem(SkillBook.Tome(tome), 1);
            }
        }""", """        // A story fight won gives a tome (a table's, now and then): blank, to be
        // written with one of what burned here, the survivor's choice of up to three.
        var choices = new List<string>();
        if (won && (spec.Story || b.Rng.Next() < 0.35))
            choices = Skills(b).Where(id => SkillBook.CanLearn(ch, id))
                .OrderByDescending(id => b.Weapons.FirstOrDefault(w => w.Id == id)?.Rank ?? 8).Take(3).ToList();
        // What was made here for the first time goes in the codex, recipe and all.
        var recorded = new List<string>();
        foreach (var m in Made(b))
            if (!j.World.Codex.Contains(m)) { j.World.Codex.Add(m); recorded.Add(m); }
        foreach (var m in Made(b).Where(m => m.StartsWith("evo:")))
            if (!ch.Stats.Evolutions.Contains(m[4..])) ch.Stats.Evolutions.Add(m[4..]);"""),
("""        return new ArenaResult(spec, won, b.Time, b.KillCount, b.EmberLevel, xp, b.GoldTotal, fresh, levels, longest, tome, taught);""",
"""        return new ArenaResult(spec, won, b.Time, b.KillCount, b.EmberLevel, xp, b.GoldTotal, fresh, levels, longest, null, taught)
        {
            TomeChoices = choices, Recorded = recorded,
        };"""),
])
print('ok')
