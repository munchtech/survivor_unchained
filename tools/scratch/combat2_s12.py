W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""        var flow = Flow(map);""", """        var flow = Flow(map, (x, z) => b.Collision.Blocked(x, z, 0.55));"""),
        ("""    static double[] Flow(MapBuild map)
    {
        int res = map.Meta.Res;
        double half = map.Meta.Size / 2;
        var walk = map.Walkable;""", """    static double[] Flow(MapBuild map, Func<double, double, bool> blocked)
    {
        int res = map.Meta.Res;
        double half = map.Meta.Size / 2;
        // The ground's walkable cells, less what stands on them (rocks, stumps, the people's cover).
        var walk = (bool[])map.Walkable.Clone();
        for (int k = 0; k < walk.Length; k++)
            if (walk[k] && blocked(k % res - half, k / res - half)) walk[k] = false;"""),
    ],
}
