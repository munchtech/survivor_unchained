import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

P = 'logic/Play/Bosses/ArenaBosses.cs'
edit(P, [
# The crescent: on the far side of the survivor from her, open toward her.
("""        double away = Math.Atan2(p.Z - E.Z, p.X - E.X);
        A.Bark(E.X, E.Z, "A rising howl: the Pack wheels.", "The Pack-Mother");
        int n = 7 + A.Tier;
        for (int k = 0; k < n; k++)
        {
            // The crescent faces her across the survivor, its open side toward her.
            double a = away + Math.PI * (0.25 + 1.5 * k / Math.Max(1, n - 1)) - Math.PI;
            a += Math.PI;
            double x = p.X + Math.Cos(a) * 10, z = p.Z + Math.Sin(a) * 10;
            if (A.CanStand(x, z)) A.Spawn("wolf", x, z);
        }""",
"""        // The crescent on the far side of the survivor from her, its open side toward her.
        double away = Math.Atan2(p.Z - E.Z, p.X - E.X);
        A.Bark(E.X, E.Z, "A rising howl: the Pack wheels.", "The Pack-Mother");
        int n = 7 + A.Tier;
        for (int k = 0; k < n; k++)
        {
            double a = away + (k / (double)Math.Max(1, n - 1) - 0.5) * Math.PI * 1.1;
            double x = p.X + Math.Cos(a) * 10, z = p.Z + Math.Sin(a) * 10;
            if (A.CanStand(x, z)) A.Spawn("wolf", x, z);
        }"""),
# Grimtunnel: half damage while he is under.
("""        if (dazeT > 0) { dazeT -= dt; e.TakenMul = 1.5; e.Vx = e.Vz = 0; e.State = EnemyState.Stunned; e.StateT = Math.Max(e.StateT, dt * 2); return true; }
        e.TakenMul = 1;""",
"""        if (dazeT > 0) { dazeT -= dt; e.TakenMul = 1.5; e.Vx = e.Vz = 0; e.State = EnemyState.Stunned; e.StateT = Math.Max(e.StateT, dt * 2); return true; }
        // Under the ground he is still in reach, at half.
        e.TakenMul = under ? 0.5 : 1;"""),
("""        double tx = p.X, tz = p.Z;
        e.TakenMul = 0.5;
        DashTo(tx, tz, 2.4, () =>
        {
            var b = Circle(E.X, E.Z, 3.5, 1.2, 2.0, "He bursts up", School.Physical);
            double bx = E.X, bz = E.Z;
            Hold(1.2, () =>
            {
                dazeT = frostCaught ? 8 : 4;
                frostCaught = false;
                if (PhaseIx == 1) Pit(bx, bz);
            }, _ => { E.TakenMul = 0.5; return true; });
        });
    }
    bool frostCaught;""",
"""        double tx = p.X, tz = p.Z;
        under = true;
        DashTo(tx, tz, 2.4, () =>
        {
            Circle(E.X, E.Z, 3.5, 1.2, 2.0, "He bursts up", School.Physical);
            double bx = E.X, bz = E.Z;
            Hold(1.2, () =>
            {
                under = false;
                dazeT = frostCaught ? 8 : 4;
                frostCaught = false;
                if (PhaseIx == 1) Pit(bx, bz);
            });
        });
    }
    bool frostCaught, under;"""),
("""        if (school == Weakness && E.TakenMul <= 0.5 && Busy) frostCaught = true;""",
 """        if (school == Weakness && under) frostCaught = true;"""),
# Pits: a collider and a mark that lasts while it does.
("""    readonly System.Collections.Generic.List<(double X, double Z, int Id)> pits = new();""",
 """    readonly System.Collections.Generic.List<(double X, double Z, int Id, int Mark)> pits = new();"""),
("""        if (pits.Count >= cap && !Soft) { var old = pits[0]; pits.RemoveAt(0); B.Collision.Remove(old.Id); }
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, X = x, Z = z, Radius = 2.6, Delay = 1.5, From = E, Label = "The ground goes" });
        var b = B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Ground, X = x, Z = z, Radius = 2.6, Delay = 1.5 + 600, From = E });
        int id = B.Collision.AddCircle(x, z, 2.4, new ColliderOpts(Tag: "pit"));
        pits.Add((x, z, id));""",
 """        if (pits.Count >= cap && !Soft) { var old = pits[0]; pits.RemoveAt(0); B.Collision.Remove(old.Id); B.EndMark(old.Mark); }
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, X = x, Z = z, Radius = 2.6, Delay = 1.5, From = E, Label = "The ground goes" });
        int mark = B.Mark(TelegraphKind.Wall, x, z, 2.5, 900);
        int id = B.Collision.AddCircle(x, z, 2.4, new ColliderOpts(Tag: "pit")).Id;
        pits.Add((x, z, id, mark));"""),
("""        foreach (var (_, _, id) in pits) B.Collision.Remove(id);
        pits.Clear();
        double x = e.X, z = e.Z;""",
 """        ClosePits();
        double x = e.X, z = e.Z;"""),
("""    public override void Fell(Enemy e) { foreach (var (_, _, id) in pits) B.Collision.Remove(id); pits.Clear(); }""",
 """    public override void Fell(Enemy e) => ClosePits();

    /// <summary>The pits fill in behind him (arena changes end with the fight).</summary>
    void ClosePits()
    {
        foreach (var (_, _, id, mark) in pits) { B.Collision.Remove(id); B.EndMark(mark); }
        pits.Clear();
    }"""),
# The Red Hand: posts by id; the thief caught or escaped; storm on the thief.
("""                posts.Add(B.Collision.AddCircle(cx + Math.Cos(a) * 5, cz + Math.Sin(a) * 5, 0.7, new ColliderOpts(Tag: "cage")));""",
 """                posts.Add(B.Collision.AddCircle(cx + Math.Cos(a) * 5, cz + Math.Sin(a) * 5, 0.7, new ColliderOpts(Tag: "cage")).Id);"""),
("""        if (thief != null && (!thief.Alive || thief.State == EnemyState.Dying)) Recover(true);""",
 """        if (thief != null && (!thief.Alive || thief.State == EnemyState.Dying)) Recover(thief.Credit);
        // Storm on the thief: he drops what he took.
        else if (thief != null && thief.LastSchool == Weakness && thief.Hp < thief.MaxHp) { B.Enemies.Release(thief); Recover(true); }"""),
("""    public override void OnHit(Enemy e, School school, double dmg) => base.OnHit(e, school, dmg);

    /// <summary>Storm on the thief: he drops what he took.</summary>
    public void OnThiefHit(School school)
    {
        if (school == Weakness && thief != null) { B.Enemies.Release(thief); Recover(true); }
    }
""", ""),
])

edit('logic/Sim/Battle.cs', [
("""    readonly List<EnemyBlow> blows = new();
    int blowIds = 1;""",
 """    readonly List<EnemyBlow> blows = new();
    int blowIds = 1;

    /// <summary>A mark on the ground that stays (a pit, a cage) until it is ended.</summary>
    public int Mark(TelegraphKind kind, double x, double z, double r, double duration)
    {
        int id = 900000 + blowIds++;
        Events.Emit(new Ev.Telegraph { Id = id, Shape = TelegraphShape.Circle, Kind = kind, X = x, Z = z, Radius = r, Duration = duration, Hostile = true, Boss = true });
        return id;
    }

    public void EndMark(int id) =>
        Events.Emit(new Ev.Telegraph { Id = id, Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, Radius = 0.01, Duration = 0.01, Hostile = true });"""),
])

edit('logic/Sim/Weapons.cs', [
("""    /// <summary>Times it has been honed (finished, in the endless dark).</summary>
    public int Honed;""",
 """    /// <summary>Times it has been honed (finished, in the endless dark).</summary>
    public int Honed;
    /// <summary>Taken from the hand for a while (the Red Hand's toll): it does not fire.</summary>
    public double DisabledT;"""),
("""    public static void Tick(Battle b, WeaponInst w, double dt)
    {
        w.Timer -= dt;""",
 """    public static void Tick(Battle b, WeaponInst w, double dt)
    {
        if (w.DisabledT > 0) { w.DisabledT -= dt; return; }
        w.Timer -= dt;"""),
])

edit('logic/Play/Zone.cs', [
("""public sealed record BossBar(string Name, string Title, double Hp, double MaxHp, double[]? Phases = null,
    (string Label, double Progress)? Channel = null, bool Shielded = false);""",
 """/// IsBoss: a boss's (its music); a herald's is not. Break: the damage past
/// its phase marks; Stagger: its stagger bar (0..1).
public sealed record BossBar(string Name, string Title, double Hp, double MaxHp, double[]? Phases = null,
    (string Label, double Progress)? Channel = null, bool Shielded = false, bool IsBoss = true, double Break = 0, double Stagger = 0);"""),
])
print('ok')
