from ed import edit
edit(r"logic\Sim\Entities.cs", [
    ("""    public bool LastCrit;
    public double LastDx, LastDz;
""", """    public bool LastCrit;
    /// <summary>The last blow was a tick of something in it (a burn, a poison): drawn as no blow.</summary>
    public bool LastDot;
    public double LastDx, LastDz;
"""),
])
edit(r"logic\Sim\Battle.cs", [
    ("""        e.LastCrit = crit;
        e.LastDx = dx / dl; e.LastDz = dz / dl;
""", """        e.LastCrit = crit;
        e.LastDot = o.Dot;
        e.LastDx = dx / dl; e.LastDz = dz / dl;
"""),
    ("e.Burst = false; e.LastBlow = 0; e.LastCrit = false;", "e.Burst = false; e.LastBlow = 0; e.LastCrit = false; e.LastDot = false;"),
])
edit(r"src\Actors\CrowdView.cs", [
    ("""        float flare = f;
        if (f > FlashRimOnly && !e.Boss && e.Named == null
            && (e.Elite ? ++eliteFlashes > EliteFlashes : ++whiteFlashes > WhiteFlashes)) flare = FlashRimOnly;
        // The flinch along the blow: big enough to read from thirty metres up, twice on a critical (S-17).
        float push = e.LastCrit ? 0.45f : 0.25f;
""", """        float flare = f;
        // A tick of a burn or a poison is no blow: a breath at the rim, no white and no flinch. (Burning
        // ground's ticks turned three bodies a frame into white cut-outs, over and over.)
        if (e.LastDot && !e.Boss) { flare = Math.Min(f, FlashRimOnly); f *= 0.2f; }
        else if (f > FlashRimOnly && !e.Boss && e.Named == null
            && (e.Elite ? ++eliteFlashes > EliteFlashes : ++whiteFlashes > WhiteFlashes)) flare = FlashRimOnly;
        // The flinch along the blow: big enough to read from thirty metres up, twice on a critical (S-17).
        float push = e.LastCrit ? 0.45f : 0.25f;
"""),
])
