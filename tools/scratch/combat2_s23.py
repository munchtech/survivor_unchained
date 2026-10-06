W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/MapRun.cs": [
        ("""        var e = B.SpawnEnemy(people.Boss, bc.X, bc.Z, new Battle.SpawnOpts { Level = Level + 2, Elite = true, Style = SpawnStyle.Walk });""",
         """        var e = B.SpawnEnemy(people.Boss, bc.X, bc.Z, new Battle.SpawnOpts { Level = Level + 1, Elite = true, Style = SpawnStyle.Walk });"""),
        ("""        e.Damage *= script?.DamageMul ?? 1.3;
        if (script != null)
        {
            script.FloorScale = BossFloors;""",
         """        // Its blows as its people's champion's, not the night's ruler's third more: a day build carries
        // none of the ember's mending, and her bites took a level-ten warden from full in eight seconds.
        if (script != null)
        {
            script.FloorScale = BossFloors;"""),
    ],
}
