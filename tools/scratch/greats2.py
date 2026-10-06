import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""    public int Revives;
    public Enemy? LastKiller;""",
"""    public int Revives;
    /// <summary>Risings From the Ashes still owed tonight (the ember's own, lost at dawn).</summary>
    public int Ashes;
    public Enemy? LastKiller;"""),
("""        // Half a ghost: blows land at half.
        if (Art.WraithT > 0) dmg *= 0.5;
        return HurtPlayerRaw(dmg, school, source, from);""",
"""        // Half a ghost: blows land at half.
        if (Art.WraithT > 0) dmg *= 0.5;
        // Grounding: part of the blow goes to earth (its lightning is the blessing's Hurt rule).
        if (Boons.TryGetValue("grounding", out int ground)) dmg *= ground >= 2 ? 0.67 : 0.8;
        return HurtPlayerRaw(dmg, school, source, from);"""),
("""            if (p.Revives > 0)
            {
                p.Revives--;
                p.Hp = MaxHp * 0.5;
                p.Iframes = 2;
                Events.Emit(new Ev.Announce { Title = "You rise again", Tone = Tone.Boon });
            }""",
"""            if (p.Revives > 0 || p.Ashes > 0)
            {
                // The ember's rising first: the kit's keeps for a night without it.
                bool ashes = p.Ashes > 0;
                if (ashes) p.Ashes--; else p.Revives--;
                int ar = Boons.GetValueOrDefault("from_the_ashes");
                p.Hp = MaxHp * (ashes && ar >= 2 ? 1 : 0.5);
                p.Iframes = 2;
                if (ashes) RiseBurning(ar);
                Events.Emit(new Ev.Announce { Title = ashes ? "From the ashes" : "You rise again", Tone = Tone.Boon });
            }"""),
("""    /// <summary>Cinderwake: fire where the dash has been.</summary>""",
"""    /// <summary>From the Ashes: the survivor gets up burning, and so does everything near them.</summary>
    void RiseBurning(int rank)
    {
        var p = Player;
        var was = credit;
        credit = "boon:from_the_ashes";
        double r = (rank >= 2 ? 8 : 4) * Math.Sqrt(Stats.Get(Stat.Area)), dmg = 40 * (1 + 0.08 * (EmberLevel - 1));
        Explode(p.X, p.Z, r, dmg, School.Fire, [Tag.Fire, Tag.Area], null);
        var burn = new StatusPayload(StatusKind.Burn, 1, 1, 4);
        ForEachHostileInRadius(p.X, p.Z, r, (e, _) => ApplyStatus(e, burn, dmg));
        credit = was;
    }

    /// <summary>Cinderwake: fire where the dash has been.</summary>"""),
("""        if (id == "spirit_companion") Summon("spirit_wolf", 0, 99);""",
"""        if (id == "spirit_companion") Summon("spirit_wolf", 0, 99);
        if (id == "from_the_ashes" && r != 2) Player.Ashes++;"""),
("""        GreatOwed = 0;
        EmberOn = false;""",
"""        GreatOwed = 0;
        Player.Ashes = 0;
        EmberOn = false;"""),
("""        if (o.Summon) dmg *= st.Get(Stat.SummonDamage) * (e.Boss || e.Elite ? 2.0 : 1);""",
"""        if (o.Summon) dmg *= st.Get(Stat.SummonDamage) * (e.Boss || e.Elite ? (Boons.ContainsKey("go_for_the_throat") ? 2.8 : 2.0) : 1);"""),
])

edit('logic/Sim/Ai.cs', [
("""        if (e.Disposition == Disposition.Ally)
        {
            var t = b.NearestHostile(e.X, e.Z, 11);
            // Do not wander off: only fight what is near the survivor.
            if (t != null && Dist(t.X, t.Z, p.X, p.Z) < 16) return t.Id;
            return -2;
        }""",
"""        if (e.Disposition == Disposition.Ally)
        {
            // Go for the Throat: the toughest thing in reach, not the nearest.
            var t = b.Boons.ContainsKey("go_for_the_throat") ? Toughest(b, e.X, e.Z, 11) : b.NearestHostile(e.X, e.Z, 11);
            // Do not wander off: only fight what is near the survivor.
            if (t != null && Dist(t.X, t.Z, p.X, p.Z) < 16) return t.Id;
            return -2;
        }"""),
("""    static bool ResolveTarget(Battle b, Enemy e, out Tgt tgt)""",
"""    /// <summary>The toughest hostile within r: a boss before a champion before the rest.</summary>
    static Enemy? Toughest(Battle b, double x, double z, double r)
    {
        Enemy? best = null;
        double bv = -1;
        b.Spatial.Query(x, z, r, b.AiScratch);
        foreach (var id in b.AiScratch)
        {
            var o = b.Enemies.Items[id];
            if (!o.Alive || o.State == EnemyState.Dying || o.Disposition != Disposition.Hostile || Dist(o.X, o.Z, x, z) > r) continue;
            double v = (o.Boss ? 2e6 : o.Elite ? 1e6 : 0) + o.MaxHp;
            if (v > bv) { bv = v; best = o; }
        }
        return best;
    }

    static bool ResolveTarget(Battle b, Enemy e, out Tgt tgt)"""),
])
print('ok')
