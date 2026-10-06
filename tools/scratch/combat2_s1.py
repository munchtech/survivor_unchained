W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/ArenaTests.cs": [
        ("""        // 380 footpads at the day's rate would drop about 250 purses; 20 champions keep theirs.
        Assert.InRange(gold, 1, 40);""",
         """        // 380 footpads and 20 champions at the day's rate would drop about 220 purses: now a
        // three-hundredth of the crowd's and a tenth of the champions', one or two.
        Assert.InRange(gold, 0, 8);"""),
        ("""    /// the crowd's champions hundreds of pieces of gear. Now the rank and file drop a fiftieth of
    /// their gold, and gear comes only from what carries a chest.</summary>""",
         """    /// the crowd's champions hundreds of pieces of gear. Now the rank and file drop a three-hundredth
    /// of their gold and champions a tenth, and gear comes only from what carries a chest.</summary>"""),
    ],
}
