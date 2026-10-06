W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""        // As the game wires it: what is picked up goes into the pack (charts, gear, materials).
        var zh = zone.Hooks;
        b.Hooks = BattleHooks.Following(zh);
        b.Hooks.OnPickup = pk => (zh.OnPickup == null || zh.OnPickup(pk)) && j.PickedUp(pk);""",
         """        // As the game wires it: what is picked up goes into the pack (charts and materials); gear is
        // counted and stashed, so the pack never fills and leaves a piece lying under the hands.
        var zh = zone.Hooks;
        b.Hooks = BattleHooks.Following(zh);
        int gear = 0;
        b.Hooks.OnPickup = pk =>
        {
            if (zh.OnPickup != null && !zh.OnPickup(pk)) return false;
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Charts.FromRef(pk.Ref) == null) { gear++; return true; }
            j.PickedUp(pk);
            return true;
        };"""),
        ("""        r.Items = j.Ch.Pack.Count(i => i != null && Items.Find(i.Def)?.Base == true);""",
         """        r.Items = gear;"""),
    ],
}
