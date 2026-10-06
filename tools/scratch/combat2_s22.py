W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""                    case Ev.PlayerDeath d: r.KilledBy = d.Killer; break;""",
         """                    case Ev.PlayerDeath d: r.KilledBy = d.Killer; break;
                    // MAP_BLOWS=1: the blows that land in the ruler's fight (why its fight was lost).
                    case Ev.PlayerHit ph when blows && zone.Boss != null:
                        Console.Error.WriteLine($"{t / 60:0.000} {ph.Source,-22} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : "")} hp {p.Hp:0}/{b.MaxHp:0} phase {zone.BossScript?.PhaseIx}");
                        break;"""),
        ("""        bool trace = Environment.GetEnvironmentVariable("MAP_TRACE") == "1";""",
         """        bool trace = Environment.GetEnvironmentVariable("MAP_TRACE") == "1", blows = Environment.GetEnvironmentVariable("MAP_BLOWS") == "1";"""),
    ],
}
