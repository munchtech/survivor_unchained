import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot\balance')
p = 'Harness/Pilot.cs'
s = open(p, encoding='utf-8').read()
old = """        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
        if (press.Count >= crowded)"""
new = """        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
        // A champion or the boss at arm's length: give ground round it, as anyone does who
        // has been hit by one twice (a ranged build kites it; a blade fights it only with
        // the health to). Without this the bot stood in a boss's combo and fell.
        Enemy? big = null;
        double bigD = close ? 2.2 : 4.5;
        foreach (var e in b.HostilesInRadius(p.X, p.Z, bigD))
            if ((e.Boss || e.Elite) && (!close || p.Hp < b.MaxHp * 0.5)) { big = e; break; }
        if (big != null)
        {
            double cx = big.X - p.X, cz = big.Z - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            mx = -cx / cl * 0.8 - cz / cl * 0.6; mz = -cz / cl * 0.8 + cx / cl * 0.6;
        }
        else if (press.Count >= crowded)"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
