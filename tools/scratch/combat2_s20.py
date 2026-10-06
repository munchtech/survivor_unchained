W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/MapGenTests.cs": [
        ("""        var sw = Stopwatch.StartNew();
        var m = MapGen.Generate(new MapSpec { Seed = seed, Tier = 1 });
        sw.Stop();
        Assert.True(sw.ElapsedMilliseconds < 4000, $"made in {sw.ElapsedMilliseconds} ms");
        Assert.Equal(16, m.Areas.Count);""",
         """        // (No clock here: a busy machine made a 1 s map take 6. The work is bounded by what is made,
        // below: sixteen clearings, a few thousand colliders, the flora.)
        var m = MapGen.Generate(new MapSpec { Seed = seed, Tier = 1 });
        Assert.Equal(16, m.Areas.Count);"""),
        ("""        var sw = Stopwatch.StartNew();
        var m = MapGen.Generate(new MapSpec { Seed = seed, Arena = true });
        Assert.True(sw.ElapsedMilliseconds < 4000, $"made in {sw.ElapsedMilliseconds} ms");
        Assert.Equal("arena", m.Meta.Id);""",
         """        var m = MapGen.Generate(new MapSpec { Seed = seed, Arena = true });
        Assert.Equal("arena", m.Meta.Id);"""),
    ],
}
