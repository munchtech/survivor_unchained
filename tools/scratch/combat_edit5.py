W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Bosses\ArenaBosses.cs', [
('''/// <summary>The Pack-Mother: she herds you; refuse to be herded. Fire breaks her
/// moon-howl.</summary>''',
'''/// <summary>The Pack-Mother: she herds you; refuse to be herded. Fire breaks her
/// moon-howl. The same fight is Greymuzzle's in his own Hollow (the story's): he is
/// wordless, so the Pack's lines are what is heard, never what is said.</summary>'''),
('''    public override string WeaknessText => "Fire breaks her moon-howl";''',
'''    public override string WeaknessText => $"Fire breaks {Her} moon-howl";
    /// <summary>Greymuzzle is a he; the Pack-Mother a she.</summary>
    bool He => A.BossName == "Greymuzzle";
    string Her => He ? "his" : "her";'''),
('''        A.Bark(E.X, E.Z, "A rising howl: the Pack wheels.", "The Pack-Mother");''',
'''        A.Bark(E.X, E.Z, "A rising howl: the Pack wheels.", null);'''),
('''        A.Bark(e.X, e.Z, "She sits back and howls at the moon.", "The Pack-Mother");''',
'''        A.Bark(e.X, e.Z, $"{(He ? "He" : "She")} sits back and howls at the moon.", null);'''),
('''1.8, 1.2, 1.5, "Her dead run", School.Frost);''',
'''1.8, 1.2, 1.5, He ? "His dead run" : "Her dead run", School.Frost);'''),
])

edit(r'logic\Play\Bosses\ArenaBoss.cs', [
('''    Battle B { get; }
    int Tier { get; }''',
'''    Battle B { get; }
    int Tier { get; }
    /// <summary>Who it is here (the Pack's ruler is Greymuzzle in his Hollow, the Pack-Mother at the table).</summary>
    string BossName { get; }'''),
])

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''    int IBossArena.Tier => Spec.Tier;''',
'''    int IBossArena.Tier => Spec.Tier;
    string IBossArena.BossName => BossName;'''),
('''            boss.Boss = true;
            if (Spec.BossName != null) boss.Named = new Named { Title = Spec.BossName };''',
'''            boss.Boss = true;
            // Named, so its body glows as a named thing's does and its blows carry its name.
            boss.Named = new Named { Title = BossName };'''),
])
print("ok")
