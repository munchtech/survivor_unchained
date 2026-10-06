PAIRS = [
('''            case Stage.Boss:
                script?.Step(dt);
                break;''',
'''            case Stage.Boss:
                ShutBehind();
                script?.Step(dt);
                break;'''),
('''    void Open(string gate)
    {''',
'''    bool shutBehind;

    /// <summary>On the boss's ground, the way back shuts behind her (his people close it): the fight is
    /// on its ground, and a fight that drifts back down the way in is a fight that never ends.</summary>
    void ShutBehind()
    {
        if (shutBehind || B == null) return;
        var p = B.Player;
        var ground = Fight.Place.SpaceAt(Fight.Place[Fight.BossStart].X, Fight.Place[Fight.BossStart].Z);
        if (ground == null || !Fight.Place.In(ground, p.X, p.Z, 1.5)) return;
        shutBehind = true;
        foreach (var g in Fight.Place.Gates.Where(g => g.Into == ground)) StoryPlace.Shut(B.Collision, g);
        open.Clear();
        open.Add(ground);
    }

    void Open(string gate)
    {'''),
]
