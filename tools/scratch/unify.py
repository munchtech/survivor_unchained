import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

A = 'balance/Harness/ArenaSim.cs'
edit(A, [
("""/// <summary>One arena to play: who, how they draft, where, how long.</summary>
public sealed record RunSpec(int Seed, string Calling, string Policy, int Tier = 1, string People = "pack", string[]? Oaths = null,
    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0)
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}";
}""",
"""/// <summary>One arena to play: who, how they draft, where, how long; the
/// survivor's character level (points in the calling's own attribute), and
/// whether the hands are deft (they read lunges, pots and burning ground as a
/// player who knows the fight does: a death is then the game's, not the bot's).</summary>
public sealed record RunSpec(int Seed, string Calling, string Policy, int Tier = 1, string People = "pack", string[]? Oaths = null,
    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0, int Level = 1, bool Deft = false)
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") +
        (Oaths is { Length: > 0 } ? $"/{string.Join("+", Oaths)}" : "");
}"""),
("""    public List<string> Greats = new();

    /// <summary>Won at the half hour and still standing for the boss: the target.</summary>""",
"""    public List<string> Greats = new();
    /// <summary>Every card taken, with the minute it was taken (for comparing runs that took a card early).</summary>
    public List<(string Card, double Minute)> Picks = new();
    /// <summary>What was left of the boss when the survivor fell to it (-1: it was not up).</summary>
    public double BossLeft = -1;
    public int Quaffs;

    /// <summary>Won at the half hour and still standing for the boss: the target.</summary>"""),
("""            if (take.Great) r.Greats.Add(take.Id);""",
"""            if (take.Great) r.Greats.Add(take.Id);
            r.Picks.Add((Card(take), b.Time / 60));"""),
("""        }, (uint)spec.Seed);
        var arena = new ArenaSpec""",
"""        }, (uint)spec.Seed);
        // A survivor further on: the levels, and the points put into the calling's own.
        while (j.Ch.Level < spec.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (spec.Calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        var arena = new ArenaSpec"""),
("""            var (mx, mz) = Pilot.Steer(b);
            Pilot.Act(b, j, mx, mz);""",
"""            var (mx, mz) = Pilot.Steer(b, spec.Deft);
            if (Pilot.Act(b, j, mx, mz)) r.Quaffs++;"""),
("""        r.Died = !p.Alive;
        r.Minutes = t / 60;""",
"""        r.Died = !p.Alive;
        r.Minutes = t / 60;
        if (r.Died && r.WonAt == null && host.Boss is { } bar && t >= arena.Minutes * 60) r.BossLeft = bar.Hp / Math.Max(1, bar.MaxHp);"""),
])

P = 'balance/Harness/Pilot.cs'
s = open(P, encoding='utf-8').read()
s = s.replace("""    public static (double X, double Z) Steer(Battle b)
    {""", """    public static (double X, double Z) Steer(Battle b, bool deft = false)
    {""")
old_tail = """        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) (mx, mz) = (-mz, mx);"""
assert s.count(old_tail) == 1
s = s.replace(old_tail, """        if (deft) Deft(b, press.Count >= 2 || stone != null, ref mx, ref mz);
        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) (mx, mz) = (-mz, mx);""")
old_act = """    public static void Act(Battle b, Journey j, double mx, double mz)
    {"""
assert s.count(old_act) == 1
s = s.replace(old_act, """    /// <returns>Whether a draught was drunk.</returns>
    public static bool Act(Battle b, Journey j, double mx, double mz)
    {""")
old_q = """        if (p.Hp < b.MaxHp * 0.33) j.Quaff(b);
    }"""
assert s.count(old_q) == 1
s = s.replace(old_q, """        if (p.Hp >= b.MaxHp * 0.33) return false;
        double before = p.Hp;
        j.Quaff(b);
        return p.Hp > before;
    }

    /// <summary>What a player who knows the fight does over the plain hands'
    /// choice, the worst danger first (from the balance lab's deft bot, which
    /// the tests' ArenaPlay shares): off the line of a marked lunge, dashing
    /// across it if late; out from under a lobbed pot and off burning ground;
    /// and, with nothing pressing and no ember near, in on the nearest thrower.</summary>
    public static void Deft(Battle b, bool busy, ref double mx, ref double mz)
    {
        var p = b.Player;
        foreach (var e in b.Enemies.Living())
        {
            if (e.State != EnemyState.Windup || e.Disposition != Disposition.Hostile) continue;
            var lunge = e.Def.Charge ?? e.Def.Lunge;
            if (lunge == null) continue;
            double reach = lunge.Speed * lunge.Time + e.Radius + 1;
            double rx = p.X - e.X, rz = p.Z - e.Z;
            double along = rx * e.LungeX + rz * e.LungeZ;
            double across = rx * -e.LungeZ + rz * e.LungeX;
            if (along < -1 || along > reach || Math.Abs(across) > e.Radius * 1.1 + p.Radius + 0.9) continue;
            double side = across >= 0 ? 1 : -1;
            mx = -e.LungeZ * side; mz = e.LungeX * side;
            if (e.StateT < 0.3 && p.DashCharges > 0) b.Dash(mx, mz);
            return;
        }
        foreach (var pr in b.Projectiles.Living())
        {
            if (!pr.Lob || pr.Owner != Side.Enemy) continue;
            double d = Dist(pr.LandX, pr.LandZ, p.X, p.Z);
            if (d < 2.2) { mx = (p.X - pr.LandX) / Math.Max(0.1, d); mz = (p.Z - pr.LandZ) / Math.Max(0.1, d); return; }
        }
        foreach (var z in b.Zones.Living())
        {
            if (z.Owner is not (Side.Enemy or Side.World)) continue;
            double d = Dist(z.X, z.Z, p.X, p.Z);
            if (d < z.Radius + p.Radius) { mx = (p.X - z.X) / Math.Max(0.1, d); mz = (p.Z - z.Z) / Math.Max(0.1, d); return; }
        }
        if (busy) return;
        Enemy? shooter = null;
        double sd = 11;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d < sd) { sd = d; shooter = e; }
        }
        if (shooter != null && sd > 1.8 && b.HostilesInRadius(p.X, p.Z, 4.5).Count < 3) { mx = shooter.X - p.X; mz = shooter.Z - p.Z; }
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));""")
open(P, 'w', encoding='utf-8').write(s)

# The tests' arena bot shares the deft hands rather than keeping its own copy.
T = 'tests/ArenaPlay.cs'
s = open(T, encoding='utf-8').read()
i = s.index('    /// <summary>What a player who knows the fight does over the plain bot\'s')
j = s.index('    static double Dist(double ax, double az, double bx, double bz)')
s = s[:i] + s[j:]
s = s.replace('if (c.Deft) Read(b, press.Count >= 2 || stone != null, ref mx, ref mz);', 'if (c.Deft) SurvivorUnchained.Balance.Pilot.Deft(b, press.Count >= 2 || stone != null, ref mx, ref mz);')
open(T, 'w', encoding='utf-8').write(s)
print('ok')
