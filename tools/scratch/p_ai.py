PAIRS = [
("""        b.TickStatus(e, dt);
        if (!e.Alive || e.State == EnemyState.Dying) return;""",
"""        b.TickStatus(e, dt);
        if (!e.Alive || e.State == EnemyState.Dying) return;
        if (e.HasteT > 0) e.HasteT -= dt;
        if (e.WardT > 0) e.WardT -= dt;"""),
("""        double speed = e.Speed * SlowFactor(e);""",
"""        double speed = e.Speed * SlowFactor(e) * (e.HasteT > 0 ? e.Haste : 1);"""),
("""                // A charge that ends in a tree ends the charger for a while.
                if (b.Collision.Resolve(ref e.X, ref e.Z, e.Radius))
                {
                    if (def.Charge != null)
                    {""",
"""                // A charge that ends in a tree ends the charger for a while.
                if (b.Collision.Resolve(ref e.X, ref e.Z, e.Radius))
                {
                    // (A lit crate run into a tree goes up there.)
                    if (def.RunBursts) { b.KillEnemy(e, false, null); return; }
                    e.ChainLeft = 0;
                    if (def.Charge != null)
                    {"""),
("""                if (e.StateT <= 0) { e.State = EnemyState.Recover; e.StateT = 0.55; }
                return;
            }""",
"""                if (e.StateT <= 0)
                {
                    // Its run done: a lit crate goes up where it stops; a chain turns and runs again.
                    if (def.RunBursts) { b.KillEnemy(e, false, null); return; }
                    if (e.ChainLeft > 0 && dist > 2)
                    {
                        e.ChainLeft--;
                        Run(b, e, lunge, dx / dist, dz / dist, lunge.Windup * 0.55);
                        return;
                    }
                    e.State = EnemyState.Recover; e.StateT = 0.55;
                }
                return;
            }"""),
("""                && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.3) == null && b.Charges.MayStart(b, e))
            {
                e.State = EnemyState.Windup;
                e.StateT = lunge.Windup;
                e.LungeX = dx / dist; e.LungeZ = dz / dist;
                double reachL = lunge.Speed * lunge.Time;
                b.Events.Emit(new Ev.Telegraph
                {
                    Id = e.Id, Shape = TelegraphShape.Line, X = e.X, Z = e.Z, X1 = e.X + e.LungeX * reachL, Z1 = e.Z + e.LungeZ * reachL,
                    Radius = e.Radius, Width = e.Radius * 2.2, Duration = lunge.Windup, Hostile = e.Disposition != Disposition.Ally,
                });
                e.Vx = e.Vz = 0;
                return;
            }""",
"""                && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.3) == null && b.Charges.MayStart(b, e))
            {
                e.ChainLeft = def.Chain;
                Run(b, e, lunge, dx / dist, dz / dist, lunge.Windup);
                return;
            }"""),
("""            if (e.State == EnemyState.Casting)
            {
                e.StateT -= dt;
                e.Anim = EnemyAnim.Cast;
                e.Vx = e.Vz = 0;
                if (e.StateT <= 0)
                {
                    e.State = EnemyState.Active;
                    int n = 0;""",
"""            if (e.State == EnemyState.Casting && e.Cast is CastKind.Raise or CastKind.None)
            {
                e.StateT -= dt;
                e.Anim = EnemyAnim.Cast;
                e.Vx = e.Vz = 0;
                if (e.StateT <= 0)
                {
                    e.State = EnemyState.Active;
                    e.Cast = CastKind.None;
                    int n = 0;"""),
("""                    e.State = EnemyState.Casting;
                    e.StateT = 1.5;
                    b.Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Ring, X = e.X, Z = e.Z, Radius = raise.Range, Duration = 1.5, Hostile = true });""",
"""                    e.State = EnemyState.Casting;
                    e.Cast = CastKind.Raise;
                    e.StateT = 1.5;
                    b.Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Ring, X = e.X, Z = e.Z, Radius = raise.Range, Duration = 1.5, Hostile = true });"""),
("""        // Where it wants to be.
        switch (def.Behavior)""",
"""        // Its own verbs: a rallying pulse, a call for its kind, a blow on the ground.
        if ((def.Aura != null || def.Summon != null || def.Slam != null) && Verbs(b, e, def, tgt, dist, dt)) return;

        // Where it wants to be.
        switch (def.Behavior)"""),
("""            double every = def.AttackEvery ?? 1.0;
            if (e.Disposition == Disposition.Ally) every /= b.Stats.Get(Stat.SummonHaste);""",
"""            double every = (def.AttackEvery ?? 1.0) / (e.HasteT > 0 ? e.Haste : 1);
            if (e.Disposition == Disposition.Ally) every /= b.Stats.Get(Stat.SummonHaste);"""),
("""    /// <summary>A grave within reach. A loop, not a lambda: one capturing the""",
"""    /// <summary>Plant and mark the lane, then run exactly it (a first run, or the next of a chain).</summary>
    static void Run(Battle b, Enemy e, LungeSpec lunge, double dirX, double dirZ, double windup)
    {
        e.State = EnemyState.Windup;
        e.StateT = windup;
        e.LungeX = dirX; e.LungeZ = dirZ;
        double reachL = lunge.Speed * lunge.Time;
        b.Events.Emit(new Ev.Telegraph
        {
            Id = e.Id, Shape = TelegraphShape.Line, X = e.X, Z = e.Z, X1 = e.X + e.LungeX * reachL, Z1 = e.Z + e.LungeZ * reachL,
            Radius = e.Radius, Width = e.Radius * 2.2, Duration = windup, Hostile = e.Disposition != Disposition.Ally,
        });
        e.Vx = e.Vz = 0;
    }

    /* ------------------------------------------------- the encounters' verbs -- */

    /// <summary>A rallying pulse, a call for its kind, a blow on the ground (docs/SKILLS_DESIGN.md,
    /// "Encounters"): each a cast with its mark and its word first, then the thing. True while
    /// it is casting (it does nothing else).</summary>
    static bool Verbs(Battle b, Enemy e, EnemyDef def, in Tgt tgt, double dist, double dt)
    {
        if (e.State == EnemyState.Casting && e.Cast is CastKind.Summon or CastKind.Slam or CastKind.Aura)
        {
            e.StateT -= dt;
            e.Anim = EnemyAnim.Cast;
            e.Vx = e.Vz = 0;
            if (e.StateT > 0) return true;
            var done = e.Cast;
            e.State = EnemyState.Active;
            e.Cast = CastKind.None;
            if (done == CastKind.Summon) Call(b, e, def.Summon!);
            else if (done == CastKind.Aura) Rally(b, e, def.Aura!);
            // (A slam's blow was laid down when it was marked: marked, it lands.)
            return true;
        }
        if (e.Disposition != Disposition.Hostile) return false;
        if (def.Aura is { } aura && (e.AuraT -= dt) <= 0)
        {
            e.AuraT = aura.Every;
            Begin(e, CastKind.Aura, 0.7);
            b.Events.Emit(new Ev.Telegraph
            {
                Id = e.Id, Shape = TelegraphShape.Ring, X = e.X, Z = e.Z, Inner = Math.Max(0, aura.Radius - 0.6), Radius = aura.Radius, Duration = 0.7,
                Hostile = false, Label = aura.Word.Length > 0 ? aura.Word : null, ByX = e.X, ByZ = e.Z,
            });
            return true;
        }
        if (def.Summon is { } su && tgt.Player && dist < 16 && e.Summoned < su.Max && (e.SummonT -= dt) <= 0)
        {
            e.SummonT = su.Every;
            Begin(e, CastKind.Summon, su.Cast);
            e.CastX = su.AtTarget ? tgt.X : e.X; e.CastZ = su.AtTarget ? tgt.Z : e.Z;
            // Where each will come, marked on the ground; the word over the one calling.
            for (int i = 0; i < su.Count; i++)
            {
                var (x, z) = CallPoint(e, su, i);
                b.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.8, Duration = su.Cast, Hostile = true, Kind = TelegraphKind.Ground });
            }
            if (su.Word.Length > 0) b.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = su.Word });
            return true;
        }
        if (def.Slam is { } sl && (e.SlamT -= dt) <= 0)
        {
            if (dist > sl.Range || (!sl.Self && dist < 1.0)) { e.SlamT = 0.3; return false; }
            if (!b.Charges.MayStart(b, e, retry: false)) { e.SlamT = 0.5; return false; }
            e.SlamT = sl.Cooldown;
            double sx = sl.Self ? e.X : tgt.X, sz = sl.Self ? e.Z : tgt.Z;
            Begin(e, CastKind.Slam, sl.Windup);
            e.Facing = Math.Atan2(sz - e.Z, sx - e.X);
            b.Events.Emit(new Ev.Telegraph
            {
                Id = e.Id, Shape = TelegraphShape.Circle, X = sx, Z = sz, Radius = sl.Radius, Duration = sl.Windup, Hostile = true,
                Label = sl.Word.Length > 0 ? sl.Word : null, ByX = e.X, ByZ = e.Z,
            });
            b.EnemyStrike(sx, sz, sl.Radius, e.Damage * sl.DamagePct, sl.School, sl.Windup);
            return true;
        }
        return false;
    }

    static void Begin(Enemy e, CastKind kind, double t)
    {
        e.State = EnemyState.Casting;
        e.Cast = kind;
        e.StateT = t;
        e.Vx = e.Vz = 0;
        e.Anim = EnemyAnim.Cast;
        e.AnimT = 0;
    }

    /// <summary>Where the i-th of a call comes: round the mark, the same at the call's start
    /// and its end (so the marks shown are where they come).</summary>
    static (double X, double Z) CallPoint(Enemy e, SummonSpec su, int i)
    {
        double a = e.Seed * Math.Tau + e.Summoned * 0.7 + i * Math.Tau / su.Count;
        return (e.CastX + Math.Cos(a) * su.Range, e.CastZ + Math.Sin(a) * su.Range);
    }

    static void Call(Battle b, Enemy e, SummonSpec su)
    {
        for (int i = 0; i < su.Count; i++)
        {
            var (x, z) = CallPoint(e, su, i);
            if (b.Collision.Blocked(x, z, 0.5) || b.InBounds?.Invoke(x, z) == false) continue;
            if (b.SpawnEnemy(su.Into, x, z, new Battle.SpawnOpts { Level = e.Level, Style = su.Style, Faction = e.Faction }) is { } c)
                b.Hooks.OnCalled?.Invoke(c, e);
        }
        e.Summoned += su.Count;
    }

    /// <summary>Its kind round it quickened or warded for a while (itself too).</summary>
    static void Rally(Battle b, Enemy e, AuraSpec aura)
    {
        b.Spatial.Query(e.X, e.Z, aura.Radius, b.AiScratch);
        foreach (var id in b.AiScratch)
        {
            var o = b.Enemies.Items[id];
            if (!o.Alive || o.State == EnemyState.Dying || o.Faction != e.Faction || o.Disposition != e.Disposition || o.Boss) continue;
            if (Dist(o.X, o.Z, e.X, e.Z) > aura.Radius) continue;
            if (aura.Haste > 1) { o.HasteT = aura.Duration; o.Haste = aura.Haste; }
            if (aura.Ward > 0) { o.WardT = aura.Duration; o.Ward = aura.Ward; }
        }
    }

    /// <summary>A grave within reach. A loop, not a lambda: one capturing the"""),
]
