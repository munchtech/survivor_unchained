import io
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad059388f00c19f9f\godot\src\Actors\CrowdView.cs"
s = io.open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("        whiteFlashes = 0;\n", "        whiteFlashes = 0;\n        eliteFlashes = 0;\n")
rep("""    int whiteFlashes;
    const int WhiteFlashes = 3;
""", """    int whiteFlashes;
    const int WhiteFlashes = 3;
    /// <summary>Champions flashed white this frame, on top of the three: eight elite risen under one
    /// Iron Palms went white together, the same white-out the cap was made against.</summary>
    int eliteFlashes;
    const int EliteFlashes = 2;
""")
rep("""        // The struck flare's instant of white across the whole body is for a few at once (and any
        // champion or ruler); the rest keep it at the rim. A blast that hits sixty at once turned
        // sixty bodies white in the same frame.
        // The flinch keeps the whole blow; only the light is held back (a crowd's struck all read by
        // their flinch, a few by their flare).
        float flare = f;
        if (f > FlashRimOnly && !e.Elite && !e.Boss && e.Named == null && ++whiteFlashes > WhiteFlashes) flare = FlashRimOnly;
""", """        // The struck flare's instant of white across the whole body is for a few at once, and two
        // champions besides (any ruler always); the rest keep it at the rim. A blast that hits sixty
        // at once turned sixty bodies white in the same frame.
        // The flinch keeps the whole blow; only the light is held back (a crowd's struck all read by
        // their flinch, a few by their flare).
        float flare = f;
        if (f > FlashRimOnly && !e.Boss && e.Named == null
            && (e.Elite ? ++eliteFlashes > EliteFlashes : ++whiteFlashes > WhiteFlashes)) flare = FlashRimOnly;
""")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("ok")
