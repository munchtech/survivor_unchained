import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\logic\Sim"
FILES = {
os.path.join(ROOT, "Battle.cs"): [
("""            if (Dist(p.X, p.Z, z.X, z.Z) < z.Radius + p.Radius * 0.5)
            {
                HurtPlayer(z.Dps * z.Tick, z.School, "burning ground", null);
                if (z.School == School.Fire) { p.BurnT = 1.5; p.BurnDps = z.Dps * 0.25; }
            }""",
"""            if (Dist(p.X, p.Z, z.X, z.Z) < z.Radius + p.Radius * 0.5)
            {
                HurtByGround(z.Dps * z.Tick, z.School, z.Tick);
                if (z.School == School.Fire) { p.BurnT = 1.5; p.BurnDps = z.Dps * 0.25; }
                // The drowned's wet ground is cold underfoot.
                if (z.School == School.Frost) SlowPlayer(0.75, 0.6);
            }"""),
("""    double thornsAt = -9;
    static readonly Tag[] ThornTags = [Tag.Aura, Tag.Area, Tag.Nature];""",
"""    double thornsAt = -9;
    static readonly Tag[] ThornTags = [Tag.Aura, Tag.Area, Tag.Nature];
    double groundSum;

    /// <summary>Bad ground under the survivor: armour and resistance answer it, as they answer a
    /// blow; but it is not a blow. It is never dodged or blocked, sets off no thorns, and buys
    /// none of the moment of grace a blow buys (it did: standing in fire made the survivor
    /// untouchable by the crowd's teeth, half a second in every half second). Said once a second.</summary>
    void HurtByGround(double amount, School school, double dt)
    {
        var p = Player;
        if (!p.Alive || p.Iframes > 0 || p.Leap != null) return;
        var st = Stats;
        double dmg = amount * (1 - StatBlock.ArmorReduction(st.Get(Stat.Armor))) * (1 - Clamp(st.GetRaw(Stat.ResistOf(school)), -1, 0.8));
        if (p.BulwarkT > 0) dmg *= Has("unmoving") ? 0.2 : 0.35;
        if (Art.WraithT > 0) dmg *= 0.5;
        string source = school switch { School.Fire => "burning ground", School.Frost => "frozen ground", School.Nature => "foul ground", _ => "bad ground" };
        Dot(ref groundSum, dmg, school, source, dt);
    }"""),
],
}
