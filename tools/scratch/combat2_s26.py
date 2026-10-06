W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/MapTests.cs": [
        ("""        var charts = r.B.Pickups.Living().Where(p => p.Ref != null && Charts.FromRef(p.Ref) != null).Select(p => Charts.FromRef(p.Ref!)!).ToList();""",
         """        // (On the ground, or already in the pack if they fell within her reach.)
        var charts = r.B.Pickups.Living().Where(p => p.Ref != null && Charts.FromRef(p.Ref) != null).Select(p => Charts.FromRef(p.Ref!)!)
            .Concat(r.J.Ch.Pack.Where(i => i?.Chart != null).Select(i => i!.Chart!)).ToList();"""),
    ],
}
