W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'src\Game\Autopilot.cs', [
('''using SurvivorUnchained.Sim;
using SurvivorUnchained.World;''',
'''using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;'''),
('''    /// <summary>Out in a fight with no script: circle a patch of ground, keep
    /// the crowd in front and moving, step out of marked ground and lunges,
    /// pick up ember when nothing is close, bash when mobbed, drink when low.</summary>
    void Field(double dt, Battle b)
    {
        var p = b.Player;
        var home = territory ??= (p.X, p.Z, 18);''',
'''    /// <summary>Out in a fight with no script: circle a patch of ground, keep
    /// the crowd in front and moving, step out of marked ground and lunges,
    /// pick up ember when nothing is close, bash when mobbed, drink when low.
    /// An arena's boss up, it circles the boss instead and reads its fight as a
    /// practised player does (BossSense), so pictures show a fight fought.</summary>
    void Field(double dt, Battle b)
    {
        var p = b.Player;
        var boss = g.Zone is ArenaRun { BossScript: { } s } && s.E is { Alive: true } be && be.State != EnemyState.Dying ? s : null;
        var home = boss != null ? (boss.E.X, boss.E.Z, 10.0) : territory ??= (p.X, p.Z, 18);'''),
('''            double w = (e.Elite || e.Boss ? 2.2 : 1) * Math.Max(0, 7 - dd) / 7;''',
'''            double w = (e.Boss ? 0.8 : e.Elite ? 2.2 : 1) * Math.Max(0, 7 - dd) / 7;'''),
('''        if (hd > home.R * 1.5) { mx += (home.X - p.X) / hd * 2; mz += (home.Z - p.Z) / hd * 2; }
        Steer(dt, mx, mz, p, tx, tz);''',
'''        if (hd > home.R * 1.5) { mx += (home.X - p.X) / hd * 2; mz += (home.Z - p.Z) / hd * 2; }
        if (boss != null) BossSense.Steer(b, boss, true, 5, ref mx, ref mz);
        Steer(dt, mx, mz, p, tx, tz);'''),
])
print("ok")
