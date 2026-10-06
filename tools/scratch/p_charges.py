PAIRS = [
("""            if (e.Boss || e.Disposition == Disposition.Ally || (e.Def.Charge ?? e.Def.Lunge) == null) continue;
            if (e.State is EnemyState.Windup or EnemyState.Lunging)""",
"""            if (e.Boss || e.Disposition == Disposition.Ally || ((e.Def.Charge ?? e.Def.Lunge) == null && e.Def.Slam == null)) continue;
            // (A blow on the ground being marked is a run as the eye reads it.)
            if (e.State is EnemyState.Windup or EnemyState.Lunging || (e.State == EnemyState.Casting && e.Cast == CastKind.Slam))"""),
("""    public bool MayStart(Battle b, Enemy e)
    {
        if (e.Boss || e.Disposition == Disposition.Ally) return true;
        if (!On) { Started++; live++; return true; }
        if (e.Elite)
        {
            if (liveElite >= EliteCap) return Refuse(b, e);""",
"""    /// <param name="retry">Refused, set its run's clock to ask again shortly (a slam keeps its own).</param>
    public bool MayStart(Battle b, Enemy e, bool retry = true)
    {
        if (e.Boss || e.Disposition == Disposition.Ally) return true;
        if (!On) { Started++; live++; return true; }
        if (e.Elite)
        {
            if (liveElite >= EliteCap) return Refuse(e, retry);"""),
("""        if (live >= cap || b.Time - lastStart < gap) return Refuse(b, e);""",
"""        if (live >= cap || b.Time - lastStart < gap) return Refuse(e, retry);"""),
("""    bool Refuse(Battle b, Enemy e)
    {
        e.RangedT = 0.3 + 0.5 * rng.Next();""",
"""    bool Refuse(Enemy e, bool retry)
    {
        if (retry) e.RangedT = 0.3 + 0.5 * rng.Next();"""),
]
