import re, sys
root = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\logic"

def edit(path, pairs):
    p = root + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        if s.count(a) != 1:
            print("NOT UNIQUE/FOUND in", path, ":", a[:80], s.count(a)); sys.exit(1)
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)

edit(r"Sim\Battle.cs", [
("""    public MapRules Rules = new();
    public int EmberLevel = 1;""",
"""    public MapRules Rules = new();
    /// <summary>When the horde's chargers may run, and its other marks' caps (Charges.cs).</summary>
    public readonly ChargeDirector Charges = new();
    public int EmberLevel = 1;"""),
("""        RebuildSpatial();
        UpdatePlayer(dt, moveX, moveZ);""",
"""        RebuildSpatial();
        Charges.Tick(this, wdt);
        UpdatePlayer(dt, moveX, moveZ);"""),
("""            if (Rules.DeathBurst && Rng.Next() < 0.22)""",
"""            if (Rules.DeathBurst && Rng.Next() < 0.22 && Charges.MayFuse(this, 0.7))"""),
("""        if (e.Def.Burst is { } b)
        {""",
"""        if (e.Def.Burst is { } b && Charges.MayFuse(this, b.Fuse))
        {"""),
("""    public GroundZone? SpawnZone(Side owner, double x, double z, double radius, double life, double dps, School school)
    {
        var zn = Zones.Spawn();""",
"""    public GroundZone? SpawnZone(Side owner, double x, double z, double radius, double life, double dps, School school)
    {
        // The horde's burning ground is capped (the oldest goes out first), so it never fills
        // the field nor takes the pool from the survivor's own.
        if (owner == Side.Enemy)
        {
            int n = 0;
            GroundZone? oldest = null;
            foreach (var g in Zones.Items)
            {
                if (!g.Alive || g.Owner != Side.Enemy) continue;
                n++;
                if (oldest == null || g.Age > oldest.Age) oldest = g;
            }
            if (n >= Charges.GroundCap && oldest != null) Zones.Release(oldest);
        }
        var zn = Zones.Spawn();"""),
])

edit(r"Sim\Ai.cs", [
("""            e.RangedT -= dt;
            if (e.RangedT <= 0 && dist < lunge.Range && dist > 2 && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.3) == null)
            {""",
"""            e.RangedT -= dt;
            // The charge director says when (Charges.cs): in a spike, a charger whose own clock is
            // most of the way round goes with the rest; refused, it walks on and asks again.
            if (e.RangedT <= (b.Charges.Eager ? lunge.Cooldown * 0.4 : 0) && dist < lunge.Range && dist > 2
                && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.3) == null && b.Charges.MayStart(b, e))
            {"""),
("""                if (tgt.Player && dist > 6 && e.RangedT <= 0)
                {""",
"""                if (tgt.Player && dist > 6 && e.RangedT <= 0 && b.Charges.MayBurrow(b, e))
                {"""),
])
print("ok")
