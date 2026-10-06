W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/MapRun.cs": [
        ("""using SurvivorUnchained.Sim;

namespace""", """using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace"""),
        ("""    static bool Near(Player p, double x""", """    static bool Near(PlayerState p, double x"""),
        ("""    int IBossArena.Tier => BossTier;""", """    Battle IBossArena.B => B!;
    int IBossArena.Tier => BossTier;"""),
    ],
}
