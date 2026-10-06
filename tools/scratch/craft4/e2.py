from ed import sub

sub("src/Game/Game.cs", [
("""leaveDone;""", """leaveDone, clearDone;"""),
("""        // --leave T: a won arena left by its way out T seconds in (pictures of a night's real tally:
        // --minute 95 --won --leave 4 is an hour and five minutes stayed past the win).
        if (!leaveDone && Args.Has("leave") && zone is ArenaRun lr && Battle != null && Journey.Playtime >= Args.Num("leave", 4))
        {
            leaveDone = true;
            lr.Leave();
        }
""",
"""        // --clear T: on a map, T seconds in, every pack, keeper and its ruler felled by her hand and the
        // gold drawn in (pictures of what a whole map pays; then --leave).
        if (!clearDone && Args.Has("clear") && zone is MapRun cm && Battle != null && Journey.Playtime >= Args.Num("clear", 3))
        {
            clearDone = true;
            cm.ClearNow();
        }
        // --leave T: a won arena or a cleared map left by its way out T seconds in (pictures of the real
        // tally: --minute 95 --won --leave 4 is an hour and five minutes stayed past the win).
        if (!leaveDone && Args.Has("leave") && Battle != null && Journey.Playtime >= Args.Num("leave", 4))
        {
            leaveDone = true;
            if (zone is ArenaRun lr) lr.Leave();
            else if (zone is MapRun lm) lm.Leave();
        }
"""),
])
