W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/MapRun.cs": [
        ("""    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Dusk;""",
         """    /// <summary>By day: the maps are the day's build in the day's world, and a pack must be read
    /// before it is woken (at dusk the way was black past the start's fire).</summary>
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Day;
    /// <summary>A pack and the ground round it in view: higher than the road's, nearer than a night's.</summary>
    public override (double Pitch, double Distance)? Camera => (62, 24);"""),
    ],
    W + "src/Game/Autopilot.cs": [
        ("""        var boss = g.Zone is ArenaRun { BossScript: { } s } && s.E is { Alive: true } be && be.State != EnemyState.Dying ? s : null;""",
         """        var script = g.Zone switch { ArenaRun a => a.BossScript, MapRun m => m.BossScript, _ => null };
        var boss = script is { } s && s.E is { Alive: true } be && be.State != EnemyState.Dying ? s : null;"""),
    ],
}
