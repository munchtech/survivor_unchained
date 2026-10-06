W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/"
FILES = {
    W + "godot/logic/Play/Zones/ArenaRun.cs": [
        ("""        // Compounding from an hour past: three hundredths a minute, so by two hours past
        // nothing stands (measured: docs/team/combat.md).
        double press = m > 60 ? Math.Pow(1.03, m - 60) : 1;
        return ((1 + 0.1 * m + 0.006 * m * m) * press,""",
         """        // Compounding from an hour past: three hundredths a minute, so by two hours past
        // nothing stands (measured: docs/team/combat.md). The square's 0.004 (from 0.006) gives
        // the tail to good builds: the median run past the half hour went 22 -> 26 minutes.
        double press = m > 60 ? Math.Pow(1.03, m - 60) : 1;
        return ((1 + 0.1 * m + 0.004 * m * m) * press,"""),
    ],
    W + "docs/SKILLS_DESIGN.md": [
        ("""  `1 + 0.1m + 0.006m²`, blows `1 + 0.035m`, smoothly for the first hour past""",
         """  `1 + 0.1m + 0.004m²`, blows `1 + 0.035m`, smoothly for the first hour past"""),
        ("""| What ended them | heralds and the Kerchiefs' bruisers first, then lamplings | the horde, spread across the peoples (lamplings first); no return a wall |""",
         """| What ended them | heralds and the Kerchiefs' bruisers first, then lamplings | the horde, spread across the peoples (lamplings first); no return a wall |

Later, with greedy drafts only (8 seeds, 30 won runs): at the square's 0.006
the median was 22 minutes past (15–38), furthest 54; at 0.004, 26 (16–41),
furthest 43, so 0.004 stays. The square is not what ends the long night: the
dark's oaths and the crowd are (lamp-throwers, the blight-sick, shield-men,
crossbows, grave-callers), and only a quarter of runs stand at +30."""),
    ],
}
