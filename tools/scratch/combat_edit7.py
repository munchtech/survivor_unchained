W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'
p = W + r'\balance\Harness\Pilot.cs'
s = open(p, encoding='utf-8').read()
a = s.index('    /// <summary>How long a marked blow is on the ground before the hands answer it:')
b = s.index('    static double Dist(double ax, double az, double bx, double bz)')
s = s[:a] + '''    /// <summary>The boss read as a player who has died to it once (Play/Bosses/BossSense.cs,
    /// shared with the game's autopilot).</summary>
    public static void Boss(Battle b, ArenaBoss? boss, bool deft, ref double mx, ref double mz) =>
        BossSense.Steer(b, boss, deft, Reach(b), ref mx, ref mz);

''' + s[b:]
s = s.replace('using SurvivorUnchained.Content;\n', '', 1) if 'Abilities.' not in s[s.index('public static class Pilot'):] else s
open(p, 'w', encoding='utf-8').write(s)
print("ok")
