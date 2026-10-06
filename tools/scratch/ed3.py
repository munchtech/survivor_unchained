import sys
root = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot"

def edit(path, pairs):
    p = root + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        if s.count(a) != 1:
            print("NOT UNIQUE/FOUND in", path, ":", a[:80], s.count(a)); sys.exit(1)
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)

edit(r"logic\Play\Zones\ArenaRun.cs", [
("""        b.InBounds = map.CanStand;
        // The first great blessing, before anything moves.""",
"""        b.InBounds = map.CanStand;
        // The horde's charges come in waves with lulls, and now and then a spike on the people's tell.
        b.Charges.Spikes = true;
        (b.Charges.Tell, b.Charges.TellSound) = SpikeTell();
        b.Charges.Cap = ChargeCap();
        // The first great blessing, before anything moves."""),
("""    /// <summary>A kind from the people, weighted: those that joined long ago more often.</summary>""",
"""    /// <summary>The crowd's charges at once in a wave (Sim/Charges.cs): 2 + tier / 2, at most 4,
    /// one more each ten minutes of the long night (to three more); one while a boss is up, so
    /// its own marks are the ones read.</summary>
    int ChargeCap() => bossUp ? 1 : Math.Min(4, 2 + Spec.Tier / 2) + Math.Min(3, (int)(Beyond / 10));

    /// <summary>What a people does before many of them run at once: heard, then said.</summary>
    (string Tell, string Sound) SpikeTell() => people.Id switch
    {
        "pack" => ("The wolves give tongue, and the tuskers lower their heads.", "tell_howl"),
        "dead" => ("A drum, twice. The dead set their feet.", "tell_drum"),
        "lamplings" => ("Fuses spit, all round you.", "tell_fuse"),
        "kerchiefs" => ("A whistle, and a shout: \\"Now!\\"", "tell_whistle"),
        _ => ("Something gathers itself in the dark.", "tell"),
    };

    /// <summary>A kind from the people, weighted: those that joined long ago more often.</summary>"""),
("""        // The horde kept up: groups from out of sight, all round.
        spawnT -= dt;""",
"""        B.Charges.Cap = ChargeCap();
        B.Charges.Spikes = !bossUp;
        // The horde kept up: groups from out of sight, all round.
        spawnT -= dt;"""),
("""        herald.Named = new Named { Title = $"Herald of {people.Name}" };""",
"""        herald.Named = new Named { Title = $"Herald of {people.Name}" };
        // Its arrival is read on its own: the crowd's lanes hold off a moment.
        B!.Charges.Calm(B, 10);"""),
])
print("ok")
