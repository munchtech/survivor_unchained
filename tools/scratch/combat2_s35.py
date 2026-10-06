W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Bosses/ArenaBoss.cs": [
        ("""    public void Begin(Enemy e)
    {
        E = e;
        MaxHp = e.MaxHp;""", """    /* The oaths on the boss (docs/bosses/SURVIVORS_BOSSES.md 0.12; SKILLS_DESIGN 16.8): one visible
     * change each, in the direction it changes the horde, said on its card. The deep dark's levels,
     * the hunt's pace, the swarm's adds and the champions' lieutenant come from the arena; these
     * are the boss's own. */
    bool winter, embers, blight, ruin;
    double blightT;

    /// <summary>What the oaths sworn do to it, for its card ("its heavy blows chill").</summary>
    public string Sworn()
    {
        var o = new List<string>();
        if (A.Sworn("winter")) o.Add("its heavy blows chill");
        if (A.Sworn("embers")) o.Add("its blows leave fire");
        if (A.Sworn("blight")) o.Add("it leaves blight where it walks");
        if (A.Sworn("ruin")) o.Add("it bursts as each phase turns");
        if (A.Sworn("vigil")) o.Add("its phases come quicker");
        if (A.Sworn("iron")) o.Add("it staggers slower");
        return string.Join(", ", o);
    }

    public void Begin(Enemy e)
    {
        E = e;
        MaxHp = e.MaxHp;
        winter = A.Sworn("winter"); embers = A.Sworn("embers"); blight = A.Sworn("blight"); ruin = A.Sworn("ruin");
        // The long vigil: its floors a third shorter and its moves a fifth quicker.
        if (A.Sworn("vigil")) { FloorScale *= 2 / 3.0; cadenceMul = 0.8; }"""),
        ("""    protected double Cadence => Soft ? 0.75 : 1;""", """    double cadenceMul = 1;
    protected double Cadence => (Soft ? 0.75 : 1) * cadenceMul;"""),
        ("""        PhaseT += dt;
        var ph = Current;""", """        PhaseT += dt;
        // The blight: where it walks the ground goes bad for a while behind it.
        if (blight && (blightT -= dt) <= 0 && Math.Abs(e.Vx) + Math.Abs(e.Vz) > 0.5)
        {
            blightT = 0.5;
            var z = B.SpawnZone(Side.Enemy, e.X, e.Z, 1.4, 2, e.Damage * 0.1, School.Nature);
            if (z != null) z.Tags = [Tag.Zone, Tag.Nature];
        }
        var ph = Current;"""),
        ("""        B.Events.Emit(new Ev.Shake { Amount = 0.35 });
        A.Say(Current.Name, over > 0 ? $"Break: {Math.Round(over):N0}" : null, "danger");""",
         """        B.Events.Emit(new Ev.Shake { Amount = 0.35 });
        A.Say(Current.Name, over > 0 ? $"Break: {Math.Round(over):N0}" : null, "danger");
        // Ruin: it bursts as the phase turns (out of it in the turn's moment).
        if (ruin) Circle(e.X, e.Z, 4.5, 1.5, 1.2, "It bursts", School.Fire);"""),
        ("""    protected Battle.EnemyBlow Circle(double x, double z, double r, double delay, double mul, string label = "", School school = School.Physical) =>
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = x, Z = z, Radius = r, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label });

    protected Battle.EnemyBlow Lane(double x0, double z0, double x1, double z1, double width, double delay, double mul, string label = "", School school = School.Physical) =>
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Line, X = x0, Z = z0, X1 = x1, Z1 = z1, Width = width, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label });

    protected Battle.EnemyBlow Cone(double radius, double arcDeg, double delay, double mul, string label = "", School school = School.Physical)
    {
        var (dx, dz, _) = ToPlayer();
        return B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = E.X, Z = E.Z, Radius = radius, Angle = Math.Atan2(dz, dx), Arc = arcDeg * Math.PI / 180, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label });
    }

    protected Battle.EnemyBlow Band(double x, double z, double inner, double outer, double delay, double mul, string label = "", School school = School.Physical, TelegraphKind kind = TelegraphKind.Blow) =>
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Ring, Kind = kind, X = x, Z = z, Inner = inner, Radius = outer, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label });""",
         """    protected Battle.EnemyBlow Circle(double x, double z, double r, double delay, double mul, string label = "", School school = School.Physical) =>
        Oathed(B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = x, Z = z, Radius = r, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label }), mul, x, z, r * 0.6);

    protected Battle.EnemyBlow Lane(double x0, double z0, double x1, double z1, double width, double delay, double mul, string label = "", School school = School.Physical) =>
        Oathed(B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Line, X = x0, Z = z0, X1 = x1, Z1 = z1, Width = width, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label }), mul, x1, z1, width * 0.7);

    protected Battle.EnemyBlow Cone(double radius, double arcDeg, double delay, double mul, string label = "", School school = School.Physical)
    {
        var (dx, dz, _) = ToPlayer();
        return Oathed(B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = E.X, Z = E.Z, Radius = radius, Angle = Math.Atan2(dz, dx), Arc = arcDeg * Math.PI / 180, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label }),
            mul, E.X + dx * radius * 0.6, E.Z + dz * radius * 0.6, radius * 0.35);
    }

    protected Battle.EnemyBlow Band(double x, double z, double inner, double outer, double delay, double mul, string label = "", School school = School.Physical, TelegraphKind kind = TelegraphKind.Blow) =>
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Ring, Kind = kind, X = x, Z = z, Inner = inner, Radius = outer, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label });

    /// <summary>A marked blow under the oaths: the winter's chill on a heavy one, the embers' fire
    /// left where it lands (a little patch, so the clear ground round it stays clear).</summary>
    Battle.EnemyBlow Oathed(Battle.EnemyBlow b, double mul, double x, double z, double r)
    {
        if (winter && mul >= 1.5 && b.Slow == 0) { b.Slow = 0.55; b.SlowFor = 1.5; }
        if (embers && b.Kind == TelegraphKind.Blow && b.After == null)
        {
            double dmg = E.Damage * 0.15;
            b.After = bb => { var zn = bb.SpawnZone(Side.Enemy, x, z, Math.Clamp(r, 1, 2.2), 3, dmg, School.Fire); if (zn != null) zn.Tags = [Tag.Zone, Tag.Fire]; };
        }
        return b;
    }"""),
    ],
    W + "logic/Maps/MapOffers.cs": [
        ("""            Answer: "critical strikes", Lean: ["keen", "cruel"], Rule: r => r.IronSkin = 0.33),""",
         """            Answer: "critical strikes", Lean: ["keen", "cruel"], Rule: r => { r.IronSkin = 0.33; r.StaggerTaken = 2 / 3.0; }),"""),
    ],
    W + "logic/Play/Zones/ArenaRun.cs": [
        ("""        G.Announce(new Announcement(BossName, script != null ? $"{BossTitle} · Weakness: {script.WeaknessText}" : BossTitle, "danger", 3.4,""",
         """        // The champions' oath: a champion of its people stands beside it, signed.
        if (Spec.Oaths.Contains("champions") && Around(signAngle + 0.6, 13) is var (lx, lz) && Spawn(Strongest(), lx, lz, true) is { } lieutenant)
        {
            lieutenant.MaxHp = lieutenant.Hp = lieutenant.MaxHp * 2;
            Sign(lieutenant, SignsFor(false));
            chests.Add(lieutenant.Id);
        }
        string sworn = script?.Sworn() ?? "";
        G.Announce(new Announcement(BossName, (script != null ? $"{BossTitle} · Weakness: {script.WeaknessText}" : BossTitle) + (sworn.Length > 0 ? $" · Sworn: {sworn}" : ""), "danger", 3.4,"""),
        ("""    Enemy? IBossArena.Spawn(string def, double x, double z, bool elite, SpawnStyle? style) => Spawn(def, x, z, elite, style);""",
         """    Enemy? IBossArena.Spawn(string def, double x, double z, bool elite, SpawnStyle? style)
    {
        var e = Spawn(def, x, z, elite, style);
        // The swarm's oath: what the boss calls comes half again as many.
        if (e != null && !elite && Spec.Oaths.Contains("swarm") && R() < 0.5) Spawn(def, x + (R() - 0.5) * 1.6, z + (R() - 0.5) * 1.6, false, style);
        return e;
    }"""),
    ],
}
