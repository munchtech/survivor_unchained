PAIRS = [
('''                    if (beatIx + 1 < Fight.Beats.Length) StartBeat(beatIx + 1);
                    else BossOpen();
                }''',
'''                    if (beatIx + 1 < Fight.Beats.Length) StartBeat(beatIx + 1);
                    // The boss comes when she steps onto his ground (or, if she does not come, the ember
                    // takes her there after a while: a night is not lost standing at a gate).
                    else if (OnBossGround() || betweenT < -20)
                    {
                        if (!OnBossGround()) { var (gx, gz) = Fight.Place[Fight.BossStart]; B.Player.X = gx; B.Player.Z = gz; }
                        BossOpen();
                    }
                }'''),
('''    bool shutBehind;''', '''    bool shutBehind;

    /// <summary>The boss's own ground: the space its start stands in.</summary>
    string? BossGround => Fight.Place.SpaceAt(Fight.Place[Fight.BossStart].X, Fight.Place[Fight.BossStart].Z);
    bool OnBossGround() => BossGround is { } g && B != null && Fight.Place.In(g, B.Player.X, B.Player.Z, 1.5);'''),
('''        var ground = Fight.Place.SpaceAt(Fight.Place[Fight.BossStart].X, Fight.Place[Fight.BossStart].Z);
        if (ground == null || !Fight.Place.In(ground, p.X, p.Z, 1.5)) return;''',
'''        var ground = BossGround;
        if (ground == null || !OnBossGround()) return;'''),
]
