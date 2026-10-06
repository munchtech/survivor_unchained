import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Entities.cs', [
("""    /// <summary>When a wraith last drained it.</summary>
    public double DrainedAt = -99;""",
"""    /// <summary>When a wraith last drained it.</summary>
    public double DrainedAt = -99;
    /// <summary>Just thawed: it cannot freeze again until this runs out (3 s, a champion 5 s).</summary>
    public double ThawT;
    /// <summary>Raised from a grave by one of its own: it carries no ember (raising is never a farm).</summary>
    public bool Raised;"""),
])

edit('logic/Sim/Battle.cs', [
# Frost lock: a chill on the frozen does not keep it frozen; the just-thawed cannot freeze again for a while.
("""                if (s[StatusKind.Frozen] is { } frozen) { frozen.T = Math.Max(frozen.T, 0.4); break; }""",
"""                // The frozen stay frozen only as long as the freeze: more cold does not lock them for good.
                if (s.Has(StatusKind.Frozen)) break;"""),
("""                if (cur.Stacks >= 5 && !e.Boss)""",
"""                if (cur.Stacks >= 5 && !e.Boss && e.ThawT <= 0)"""),
("""            if (slot.T <= 0) s.Remove(k);
        }
    }""",
"""            if (slot.T <= 0)
            {
                s.Remove(k);
                if (k == StatusKind.Frozen) e.ThawT = e.Elite ? 5 : 3;
            }
        }
        if (e.ThawT > 0) e.ThawT -= dt;
    }"""),
("""        e.Decoy = e.Prey = false;""",
"""        e.Decoy = e.Prey = false;
        e.ThawT = 0;
        e.Raised = false;"""),
# Champions: a guard holds back at most 60% (a projectile build is not locked out of a champion).
("""            if (fx * ix + fz * iz > Math.Cos(guard.Arc / 2)) { dmg *= 1 - guard.Reduction; blocked = true; }""",
"""            if (fx * ix + fz * iz > Math.Cos(guard.Arc / 2)) { dmg *= 1 - (e.Elite && !e.Def.Elite ? Math.Min(guard.Reduction, 0.6) : guard.Reduction); blocked = true; }"""),
# Raised dead carry no ember.
("""            if (xp > 0 && EmberOn) DropEmber(e.X, e.Z, xp);""",
"""            if (xp > 0 && EmberOn && !e.Raised) DropEmber(e.X, e.Z, xp);"""),
# Poison and burning on the survivor say so: a quiet blow each second, and a death named for them.
("""        if (p.BurnT > 0) { p.BurnT -= dt * cure; HurtPlayerRaw(p.BurnDps * dt, School.Fire, "burning", null, true); }
        if (p.PoisonT > 0) { p.PoisonT -= dt * cure; HurtPlayerRaw(p.PoisonDps * dt, School.Nature, "poison", null, true); }""",
"""        if (p.BurnT > 0) { p.BurnT -= dt * cure; Dot(ref p.BurnSum, p.BurnDps * dt, School.Fire, "burning", dt); }
        if (p.PoisonT > 0) { p.PoisonT -= dt * cure; Dot(ref p.PoisonSum, p.PoisonDps * dt, School.Nature, "poison", dt); }"""),
("""    public double HurtPlayerRaw(double dmg, School school, string source, Enemy? from, bool silent = false)
    {""",
"""    /// <summary>Damage over time on the survivor: taken each tick, said once a second
    /// (a quiet blow with its own source), and a death by it named for it.</summary>
    void Dot(ref double sum, double dmg, School school, string source, double dt)
    {
        var p = Player;
        p.DotT += dt;
        sum += HurtPlayerRaw(dmg, school, source, null, true, dot: true);
        if (p.DotT < 1 || sum <= 0) return;
        p.DotT = 0;
        if (p.Alive) Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = sum, School = school, Source = source, Dot = true });
        sum = 0;
    }

    public double HurtPlayerRaw(double dmg, School school, string source, Enemy? from, bool silent = false, bool dot = false)
    {"""),
("""                Events.Emit(new Ev.PlayerDeath { X = p.X, Z = p.Z, Killer = p.LastKiller?.Def.Name ?? source, KillerId = p.LastKiller?.Id ?? -1 });""",
"""                // Felled by what was in them (poison, burning), it is named so; the creature that put it there keeps the credit.
                p.FellTo = dot ? source : null;
                Events.Emit(new Ev.PlayerDeath { X = p.X, Z = p.Z, Killer = dot ? source : p.LastKiller?.Def.Name ?? source, KillerId = p.LastKiller?.Id ?? -1 });"""),
("""    public double BurnT, BurnDps, PoisonT, PoisonDps;""",
"""    public double BurnT, BurnDps, PoisonT, PoisonDps;
    /// <summary>What the burning and poison have taken since they last said so, and the clock for it.</summary>
    public double BurnSum, PoisonSum, DotT;
    /// <summary>What felled the survivor when it was not a blow (poison, burning).</summary>
    public string? FellTo;"""),
])

edit('logic/Sim/Events.cs', [
("""        public double X, Z, Amount; public School School; public string Source = ""; public bool Dodged, Blocked;""",
"""        public double X, Z, Amount; public School School; public string Source = ""; public bool Dodged, Blocked;
        /// <summary>Damage over time (poison, burning), said once a second: quieter than a blow.</summary>
        public bool Dot;"""),
])

# Champions see through Mirror Step's reflections.
edit('logic/Sim/Ai.cs', [
("""        if (hostileToPlayer && b.Decoys.Count > 0)""",
"""        // Champions and bosses are not fooled by a reflection: Mirror Step saves you from the crowd, not from them.
        if (hostileToPlayer && b.Decoys.Count > 0 && !e.Elite && !e.Boss)"""),
("""                        b.SpawnEnemy(raise.Into, g.X, g.Z, new Battle.SpawnOpts { Level = e.Level, Style = SpawnStyle.Rise, Faction = e.Faction });""",
"""                        if (b.SpawnEnemy(raise.Into, g.X, g.Z, new Battle.SpawnOpts { Level = e.Level, Style = SpawnStyle.Rise, Faction = e.Faction }) is { } risen) risen.Raised = true;"""),
])

# The oaths repriced by how they play (docs/bestiary/RISK_REWARD.md 4); the Lamplings' champion a digger that closes, not a thrower to chase.
edit('logic/Maps/MapOffers.cs', [
("""        new("champions", "Oath of Champions", "Twice the champions", "More gear from them", Elites: 2, Gear: 1.6,""",
 """        new("champions", "Oath of Champions", "Twice the champions", "More gear from them", Elites: 2, Gear: 1.3,"""),
("""        new("blight", "Oath of the Blight", "Their blows poison, and you mend a third less", "Two fifths more ember", Ember: 1.4,""",
 """        new("blight", "Oath of the Blight", "Their blows poison, and you mend a third less", "Two fifths more ember, and finer gear", Ember: 1.4, Gear: 1.6,"""),
("""            [("lampling", 5, 0), ("lampling_sapper", 3.5, 4)], "lampling_sapper"),""",
 """            [("lampling", 5, 0), ("lampling_sapper", 3.5, 4)], "lampling"),"""),
])
print('ok')
