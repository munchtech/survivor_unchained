PAIRS = [
('''        if (beatIx < Fight.Between.Length) G.Say(Fight.Between[beatIx]);''',
'''        if (Fight.BetweenSight(this, beatIx) is { } sight) G.Say(sight);'''),
('''    public Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null)
    {
        var e = Spawn(def, x, z, true, SpawnStyle.Walk);
        if (e == null) return null;
        // A named foe: a miniboss's measure at its own level (between a champion's twice and a herald's
        // five times), times what its stage asks of it. Not more a tier: its level grows it already.
        e.MaxHp = e.Hp = e.MaxHp * 2.2 * hpMul;
        e.Named = new Named { Title = e.Def.Name };
        smallChests.Add(e.Id);
        B!.Charges.Calm(B, 4);
        G.Announce(new Announcement(e.Def.Name, e.Def.Lesson, "danger", 3.2, kicker));
        return e;
    }''',
'''    public Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null, bool quiet = false)
    {
        var e = Spawn(def, x, z, true, SpawnStyle.Walk);
        if (e == null) return null;
        // A named foe: a miniboss's measure at its own level (between a champion's twice and a herald's
        // five times), times what its stage asks of it. Not more a tier: its level grows it already.
        e.MaxHp = e.Hp = e.MaxHp * 2.2 * hpMul;
        e.Named = new Named { Title = e.Def.Name };
        if (quiet) return e;
        smallChests.Add(e.Id);
        B!.Charges.Calm(B, 4);
        G.Announce(new Announcement(e.Def.Name, e.Def.Lesson, "danger", 3.2, kicker ?? (Fight.Kicker != "" ? Fight.Kicker : null)));
        return e;
    }

    readonly HashSet<string> marks = new();
    public void Mark(string key) => marks.Add(key);
    public bool Marked(string key) => marks.Contains(key);
    public bool Test(Cond cond) => Rules.Test(cond, C);
    bool IStoryArena.Knows(string key) => Knows(key);
    public void After(double seconds, Action act) => G.After(seconds, act);'''),
]
