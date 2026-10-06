W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''            // Come again, it is the first fight's length and a part more each time (its blows
            // harden with the night, as everything does); not the night's hardening on its
            // health too, which would make a quarter hour's return a ten-minute wall.
            if (!again) firstBossHp = boss.MaxHp;
            else boss.MaxHp = boss.Hp = firstBossHp * (1 + ReturnGrowth * returns);
            boss.Damage *= script?.DamageMul ?? 1.3;''',
'''            boss.Damage *= script?.DamageMul ?? 1.3;
            // Come again, it is the first fight and a part more each time, by a rule the player
            // can learn, not the night's hardening and its levels on top of the boss's own (that
            // made the first return a wall: the sweep's runs fell to it more than to anything).
            if (!again) { firstBossHp = boss.MaxHp; firstBossDmg = boss.Damage; }
            else
            {
                boss.MaxHp = boss.Hp = firstBossHp * (1 + ReturnGrowth * returns);
                boss.Damage = firstBossDmg * (1 + ReturnBite * returns);
            }'''),
('''    /// <summary>A returning boss's health over the first's, per return.</summary>
    public const double ReturnGrowth = 0.35;
    double nextDark, nextReturn, firstBossHp;''',
'''    /// <summary>A returning boss's health, and its blows, over the first's, per return.</summary>
    public const double ReturnGrowth = 0.35, ReturnBite = 0.25;
    double nextDark, nextReturn, firstBossHp, firstBossDmg;'''),
])
print("ok")
