W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);""", """        // As the game wires it: what is picked up goes into the pack (charts, gear, materials).
        var zh = zone.Hooks;
        b.Hooks = BattleHooks.Following(zh);
        b.Hooks.OnPickup = pk => (zh.OnPickup == null || zh.OnPickup(pk)) && j.PickedUp(pk);
        host.Battle = b;
        zone.Begin(b);"""),
    ],
}
