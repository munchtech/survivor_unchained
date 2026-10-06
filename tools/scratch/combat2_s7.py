W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
S = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/"
PAIRS = [
    ("""        // A fiftieth still paid a Kerchief night 1.6k-2.1k gold from its forty thousand dead (crafting's
        // measure): a three-hundredth keeps it the gold night at about 400.
        b.Rules.FodderGold = 0.003;
        b.Rules.ChampionGold = 0.1;""",
     """        // A fiftieth still paid a Kerchief night 1.6k-2.1k gold from its forty thousand dead, and a
        // three-hundredth 530-690 (crafting's probes, against an economy that holds at 350-450).
        b.Rules.FodderGold = 0.0015;
        b.Rules.ChampionGold = 0.07;"""),
]
FILES = {W + "logic/Play/Zones/ArenaRun.cs": PAIRS, S + "combat2_ar_head.cs": PAIRS}
