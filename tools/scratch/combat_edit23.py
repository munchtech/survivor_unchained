W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Arena\Arena.cs', [
('''    public string? Boss, BossName, BossTitle;
''',
'''    public string? Boss, BossName, BossTitle;
    /// <summary>The boss is brought down and let go, not killed (Greymuzzle, when the story
    /// allows it: docs/STORY_BIBLE.md, "The nights").</summary>
    public bool Spare;
'''),
])

edit(r'logic\Play\Bosses\ArenaBoss.cs', [
('''    /// <summary>Who it is here (the Pack's ruler is Greymuzzle in his Hollow, the Pack-Mother at the table).</summary>
    string BossName { get; }''',
'''    /// <summary>Who it is here (the Pack's ruler is Greymuzzle in his Hollow, the Pack-Mother at the table).</summary>
    string BossName { get; }
    /// <summary>The story lets it go at the end rather than die.</summary>
    bool Spare { get; }'''),
])

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''    string IBossArena.BossName => BossName;''',
'''    string IBossArena.BossName => BossName;
    bool IBossArena.Spare => Spec.Spare;'''),
])

edit(r'logic\Play\Bosses\ArenaBosses.cs', [
('''    protected override string HardName => "The Long Hunt";
    double driveT = 6, biteT = 3, howlT, shakeT = 2, lungeT = 4;
    double howlHp;
    bool lastPack;''',
'''    protected override string HardName => "The Long Hunt";
    double driveT = 6, biteT = 3, howlT, shakeT = 2, lungeT = 4;
    double howlHp;
    bool lastPack;
    /// <summary>Let go (the story's Greymuzzle, spared): he goes down and does not die.</summary>
    protected override bool DiesAtZero => !A.Spare;
    bool lettingGo;
    double goT;'''),
('''    protected override bool Act(Enemy e, double dt)
    {
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        var p = B.Player;
        // The Pack's turn: each wolf at her side takes some of what comes at her.''',
'''    protected override bool Act(Enemy e, double dt)
    {
        if (lettingGo) return LetGo(e, dt);
        if (A.Spare && e.Hp <= 1.5 && PhaseIx == 2) { StartLetGo(e); return true; }
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        var p = B.Player;
        // The Pack's turn: each wolf at her side takes some of what comes at her.'''),
('''    protected override void OnSoft() { driveT = Math.Min(driveT, 4); }''',
'''    /// <summary>Greymuzzle let go (docs/STORY_BIBLE.md, "The nights": only if she knelt and
    /// promised and the stream already runs clean): he goes down, and does not die; he gets
    /// up, slowly, and goes to the den among his sick, and she lets him. No words: he has none.</summary>
    void StartLetGo(Enemy e)
    {
        lettingGo = true;
        goT = 0;
        Channel = null;
        e.Hp = 1;
        e.TakenMul = 0;
        // Out of the fight: nothing of hers is aimed at him now.
        e.Disposition = Disposition.Neutral;
        e.State = EnemyState.Stunned;
        e.StateT = 2.4;
        e.Vx = e.Vz = 0;
        A.Bark(e.X, e.Z, "He goes down, and does not stay down.", null);
        B.Events.Emit(new Ev.Focus { X = e.X, Z = e.Z, Duration = 2.4 });
    }

    bool LetGo(Enemy e, double dt)
    {
        goT += dt;
        e.TakenMul = 0;
        if (goT < 2.4) { e.Vx = e.Vz = 0; e.State = EnemyState.Stunned; e.StateT = Math.Max(e.StateT, dt * 2); return true; }
        if (goT - dt < 2.4)
        {
            // Up, and away from her, to the edge of the light: slowly, an old wolf's walk.
            var (dx, dz, _) = ToPlayer();
            e.State = EnemyState.Active;
            A.Bark(e.X, e.Z, "He gets up, slowly, and goes to his sick. You let him.", null);
            DashTo(E.X - dx * 12, E.Z - dz * 12, 6);
        }
        if (Running(e, dt) && goT < 8.6) return true;
        double x = e.X, z = e.Z;
        B.Enemies.Release(e);
        A.Won(x, z);
        return true;
    }

    protected override void OnSoft() { driveT = Math.Min(driveT, 4); }'''),
])

edit(r'logic\Play\Zones\Verge.cs', [
('''            () => Story("hollow_by_night", "The Hollow by Night", "pack", 311, "boss_pack", "Greymuzzle", "Who Kept the Cold Off",
                $$"""[{ "set": { "greymuzzle": "dead", "hollow.hostile": true } }, { "add": { "beasts.population": -30 } }, { "quest": { "id": "beasts", "entry": "alpha_dead" } }, { "give": "greymuzzle_fang" }, {{Hist("killed_greymuzzle", "killed Greymuzzle, the old alpha of the Pack, in his own Hollow by night", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -50, "respect": -20 }, "holloway": { "respect": 20 } }""")}}]""",
                """[{ "add": { "beasts.population": 10 } }, { "set": { "hollow.hostile": true } }, { "quest": { "id": "beasts", "entry": "hollow_lost" } }]"""));''',
'''            () =>
            {
                // Greymuzzle let go (docs/STORY_BIBLE.md, "The nights"), narrowly: only if she knelt
                // and promised and the stream already runs clean. He goes down, gets up and goes to
                // his sick; beasts.outcome stands; Maeca hears of it, the one fight that raises her regard.
                bool spare = F("promise.pack").Truthy && !F("promise.broken").Truthy && StreamClean();
                var spec = Story("hollow_by_night", "The Hollow by Night", "pack", 311, "boss_pack", "Greymuzzle", "Who Kept the Cold Off",
                    spare
                        ? $$"""[{ "set": { "greymuzzle": "spared" } }, {{Hist("spared_greymuzzle", "brought Greymuzzle down in his own Hollow by night, and let him get up and go to his sick", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": 15, "respect": 20 } }""")}}]"""
                        : $$"""[{ "set": { "greymuzzle": "dead", "hollow.hostile": true } }, { "add": { "beasts.population": -30 } }, { "quest": { "id": "beasts", "entry": "alpha_dead" } }, { "give": "greymuzzle_fang" }, {{Hist("killed_greymuzzle", "killed Greymuzzle, the old alpha of the Pack, in his own Hollow by night", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -50, "respect": -20 }, "holloway": { "respect": 20 } }""")}}]""",
                    """[{ "add": { "beasts.population": 10 } }, { "set": { "hollow.hostile": true } }, { "quest": { "id": "beasts", "entry": "hollow_lost" } }]""");
                spec.Spare = spare;
                return spec;
            });'''),
])
print("ok")
