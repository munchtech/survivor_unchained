W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Sim/Charges.cs": [
        ("""    public (double Min, double Max) SpikeEvery = (40, 55);""",
         """    public (double Min, double Max) SpikeEvery = (40, 55);
    /// <summary>A spike's runs come in pairs from two sides (a pincer): while the night builds into
    /// a landmark, so the run-ups ask where to stand as well as how many.</summary>
    public bool Pincer;
    double pincerAngle = double.NaN, pincerT;"""),
        ("""        int cap = b.Time < calmUntil ? 0 : Now switch { Beat.Wave => Cap, Beat.Spike => SpikeCap, _ => 0 };
        // One after another in a wave, so each lane is read before the next; a ripple in a spike.
        double gap = Now == Beat.Spike ? 0.12 : 0.7;
        if (live >= cap || b.Time - lastStart < gap) return Refuse(e, retry);
        live++; Started++;
        lastStart = b.Time;
        return true;""",
         """        int cap = b.Time < calmUntil ? 0 : Now switch { Beat.Wave => Cap, Beat.Spike => SpikeCap, _ => 0 };
        // One after another in a wave, so each lane is read before the next; a ripple in a spike.
        double gap = Now == Beat.Spike ? 0.12 : 0.7;
        if (live >= cap || b.Time - lastStart < gap) return Refuse(e, retry);
        // A pincer: each run in a spike from the side the last was not (for a moment; then whoever is ready).
        double a = Math.Atan2(e.Z - b.Player.Z, e.X - b.Player.X);
        if (Pincer && Now == Beat.Spike && !double.IsNaN(pincerAngle) && b.Time < pincerT)
        {
            double d = Math.Abs(Math.Atan2(Math.Sin(a - pincerAngle), Math.Cos(a - pincerAngle)));
            if (d < Math.PI * 0.6) return Refuse(e, retry);
        }
        pincerAngle = a;
        pincerT = b.Time + 0.8;
        live++; Started++;
        lastStart = b.Time;
        return true;"""),
    ],
    W + "logic/Play/Zones/ArenaRun.cs": [
        ("""            B.Charges.SpikeEvery = pacing.Building(Seconds) ? (18, 26) : (40, 55);
        }
        else B.Charges.SpikeEvery = (40, 55);""",
         """            B.Charges.SpikeEvery = pacing.Building(Seconds) ? (18, 26) : (40, 55);
            B.Charges.Pincer = pacing.Building(Seconds);
        }
        else { B.Charges.SpikeEvery = (40, 55); B.Charges.Pincer = false; }"""),
        ("""    /// <summary>A kind from the people, weighted: those that joined long ago more often.</summary>
    string Pick()
    {
        var open = escalation.Kinds(Minute).ToList();
        double W((string Def, double Weight, double From) h) => h.Weight * (1 + (Minute - h.From) / 8);""",
         """    /// <summary>The night builds into a landmark (the experience lead's run-ups: into each herald, and
    /// the long push): there the crowd brings its throwers and rallying voices forward, and its
    /// champions twice as often, signed, so the danger rises with the numbers.</summary>
    bool Building => !won && !bossUp && pacing.Building(Seconds);

    /// <summary>A kind from the people, weighted: those that joined long ago more often.</summary>
    string Pick()
    {
        var open = escalation.Kinds(Minute).ToList();
        bool building = Building;
        double W((string Def, double Weight, double From) h) => h.Weight * (1 + (Minute - h.From) / 8)
            * (building && (Enemies.Get(h.Def).Ranged != null || Enemies.Get(h.Def).Aura != null) ? 2 : 1);"""),
        ("""            // Now and then one of them a champion (more under the oath of champions, and as the minutes go).
            if (Spawn(def, sx, sz, R() < 0.012 * elites * (1 + Minute / 12)) is { } e)
            {
                // A champion in the crowd wears a Sign from the tenth minute above the first tier.
                if (e.Elite && Spec.Tier >= 2 && Minute >= 10) Sign(e, 1);""",
         """            // Now and then one of them a champion (more under the oath of champions, and as the minutes
            // go; twice as often as the night builds into a landmark).
            if (Spawn(def, sx, sz, R() < 0.012 * elites * (1 + Minute / 12) * (Building ? 2 : 1)) is { } e)
            {
                // A champion in the crowd wears a Sign from the tenth minute above the first tier, and
                // in any run-up.
                if (e.Elite && (Spec.Tier >= 2 && Minute >= 10 || Building)) Sign(e, 1);"""),
    ],
}
